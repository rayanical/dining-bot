"""
Semantic retrieval using pgvector for similarity search over menu item embeddings.

Provides vector-based search that can find semantically similar items
even when exact keywords don't match.
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import DiningHallMenu, PGVECTOR_AVAILABLE
from app.core.embeddings import get_embedding


def semantic_search(
    query: str,
    db: Session,
    limit: int = 20,
    similarity_threshold: float = 0.3,
) -> List[DiningHallMenu]:
    """Perform semantic similarity search using pgvector.

    Args:
        query: Natural language query to search for.
        db: SQLAlchemy database session.
        limit: Maximum number of results to return.
        similarity_threshold: Minimum cosine similarity (0-1) to include results.

    Returns:
        List of DiningHallMenu items ordered by semantic similarity.
    """
    if not PGVECTOR_AVAILABLE:
        # Fallback: return empty if pgvector not available
        return []

    # Generate embedding for the query
    query_embedding = get_embedding(query)
    
    # Format embedding as PostgreSQL array literal
    embedding_literal = "[" + ",".join(map(str, query_embedding)) + "]"

    # Use raw SQL for pgvector cosine distance search
    # Note: We use $1 style or literal substitution to avoid ::vector cast issues
    # The CAST syntax works better with SQLAlchemy parameter binding
    sql = text("""
        SELECT id, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
        FROM dining_hall_menu
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> CAST(:query_embedding AS vector)) >= :threshold
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """)

    try:
        result = db.execute(
            sql,
            {
                "query_embedding": embedding_literal,
                "threshold": similarity_threshold,
                "limit": limit,
            },
        )
        rows = result.fetchall()

        if not rows:
            return []

        # Fetch full ORM objects maintaining order
        ids = [row.id for row in rows]
        items_dict = {
            item.id: item
            for item in db.query(DiningHallMenu).filter(DiningHallMenu.id.in_(ids)).all()
        }
        # Preserve similarity ordering
        return [items_dict[id_] for id_ in ids if id_ in items_dict]

    except Exception as e:
        print(f"[SemanticSearch] Error: {e}")
        db.rollback()  # Reset transaction state to prevent cascade failures
        return []


def hybrid_retrieve(
    query: str,
    db: Session,
    user_profile: Optional[Dict] = None,
    limit: int = 10,
    use_semantic: bool = True,
    use_text_to_sql: bool = True,
) -> List[DiningHallMenu]:
    """Hybrid retrieval combining semantic search, text-to-SQL, and structured filters.

    Strategy:
    1. Try text-to-SQL for structured queries (explicit filters like hall, meal, diet)
    2. Use semantic search for broader, ingredient-based, or vague queries
    3. Apply user profile constraints (allergies, diets) as post-filters
    4. Combine and deduplicate results

    Args:
        query: Natural language query from user.
        db: SQLAlchemy database session.
        user_profile: Optional dict with user's dietary preferences.
        limit: Maximum number of results to return.
        use_semantic: Whether to use semantic search.
        use_text_to_sql: Whether to use GPT-generated SQL.

    Returns:
        List of DiningHallMenu items best matching the query.
    """
    from app.core.text_to_sql import text_to_sql_retrieve
    from app.core.retrieval import build_sql_filters, parse_user_query

    results_map: Dict[int, DiningHallMenu] = {}
    scores: Dict[int, float] = {}

    # 1. Try text-to-SQL for structured queries
    if use_text_to_sql:
        sql_items, error = text_to_sql_retrieve(query, db, limit=limit * 2)
        if not error and sql_items:
            for i, item in enumerate(sql_items):
                results_map[item.id] = item
                # Higher score for earlier results
                scores[item.id] = 1.0 - (i * 0.02)

    # 2. Semantic search for broader matching
    if use_semantic and PGVECTOR_AVAILABLE:
        semantic_items = semantic_search(query, db, limit=limit * 2)
        for i, item in enumerate(semantic_items):
            if item.id not in results_map:
                results_map[item.id] = item
                scores[item.id] = 0.8 - (i * 0.02)
            else:
                # Boost items that appear in both
                scores[item.id] += 0.3

    # 3. Apply user profile filters (allergies, diets)
    if user_profile and results_map:
        filtered_ids = set()
        user_allergies = set(a.lower() for a in (user_profile.get("allergies") or []))
        user_diets = set(d.lower() for d in (user_profile.get("diets") or []))

        for item_id, item in results_map.items():
            # Exclude items with user's allergens
            if user_allergies and item.allergens:
                item_allergens = set(a.lower() for a in item.allergens)
                if item_allergens & user_allergies:
                    continue

            # Prefer items matching user's diet types (but don't exclude others)
            if user_diets and item.diet_types:
                item_diets = set(d.lower() for d in item.diet_types)
                if item_diets & user_diets:
                    scores[item_id] += 0.2

            filtered_ids.add(item_id)

        results_map = {k: v for k, v in results_map.items() if k in filtered_ids}

    # 4. Sort by score and return top results
    sorted_ids = sorted(results_map.keys(), key=lambda x: scores.get(x, 0), reverse=True)
    return [results_map[id_] for id_ in sorted_ids[:limit]]
