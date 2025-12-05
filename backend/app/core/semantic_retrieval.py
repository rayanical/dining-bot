"""
Semantic retrieval using pgvector for similarity search over menu item embeddings.

Provides vector-based search that can find semantically similar items
even when exact keywords don't match.

Key feature: Pre-filtering (metadata filtering) applies hard constraints
(diet types, allergies, dining hall, meal) BEFORE vector similarity search
to ensure compliance with dietary restrictions.
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
    # Pre-filter parameters (hard constraints applied BEFORE vector search)
    required_diets: Optional[List[str]] = None,
    excluded_allergens: Optional[List[str]] = None,
    dining_hall: Optional[str] = None,
    meal: Optional[str] = None,
) -> List[DiningHallMenu]:
    """Perform semantic similarity search using pgvector with pre-filtering.

    Pre-filtering Strategy:
    Instead of "search then sort", we use "filter then search":
    1. Apply hard constraints (diets, allergens, hall, meal) as SQL WHERE clauses
    2. THEN perform vector similarity search on the filtered subset
    This guarantees compliance with dietary restrictions.
    
    Note: Nutritional goals (protein, calories) are NOT pre-filtered here.
    They are applied as soft score boosts in hybrid_retrieve to influence
    ranking without excluding items.

    Args:
        query: Natural language query to search for.
        db: SQLAlchemy database session.
        limit: Maximum number of results to return.
        similarity_threshold: Minimum cosine similarity (0-1) to include results.
        required_diets: List of diet types that items MUST have (e.g., ["Vegan"]).
        excluded_allergens: List of allergens that items must NOT have.
        dining_hall: If provided, only search items from this dining hall.
        meal: If provided, only search items available for this meal.

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

    # Build dynamic WHERE clause for pre-filtering
    # CRITICAL: Always filter by today's date to avoid stale "ghost" menu items
    where_conditions = ["embedding IS NOT NULL", "last_updated = CURRENT_DATE"]
    params = {
        "query_embedding": embedding_literal,
        "threshold": similarity_threshold,
        "limit": limit,
    }
    
    # Pre-filter: Required diet types (hard constraint)
    # Items MUST have ALL specified diet types
    if required_diets:
        for i, diet in enumerate(required_diets):
            param_name = f"diet_{i}"
            # Use array_to_string for case-insensitive matching
            where_conditions.append(
                f"LOWER(array_to_string(diet_types, ',')) LIKE LOWER(:{param_name})"
            )
            params[param_name] = f"%{diet}%"
    
    # Pre-filter: Excluded allergens (hard constraint)
    # Items must NOT contain ANY of the specified allergens
    if excluded_allergens:
        for i, allergen in enumerate(excluded_allergens):
            param_name = f"allergen_{i}"
            # Exclude items that contain this allergen
            where_conditions.append(
                f"(allergens IS NULL OR NOT LOWER(array_to_string(allergens, ',')) LIKE LOWER(:{param_name}))"
            )
            params[param_name] = f"%{allergen}%"
    
    # Pre-filter: Dining hall (hard constraint)
    if dining_hall:
        where_conditions.append("LOWER(dining_hall) = LOWER(:dining_hall)")
        params["dining_hall"] = dining_hall
    
    # Pre-filter: Meal availability (hard constraint)
    if meal:
        where_conditions.append(
            "LOWER(array_to_string(availability_today, ',')) LIKE LOWER(:meal)"
        )
        params["meal"] = f"%{meal}%"
    
    # Combine all WHERE conditions
    where_clause = " AND ".join(where_conditions)

    # Use raw SQL for pgvector cosine distance search with pre-filtering
    sql = text(f"""
        SELECT id, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
        FROM dining_hall_menu
        WHERE {where_clause}
          AND 1 - (embedding <=> CAST(:query_embedding AS vector)) >= :threshold
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """)

    try:
        result = db.execute(sql, params)
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

    Strategy (Filter-Then-Search):
    1. Parse query to extract hard constraints (diets, allergies from query text)
    2. Apply hard constraints as pre-filters to semantic search
    3. Try text-to-SQL for structured queries (explicit filters like hall, meal)
    4. Apply user profile constraints (allergies only as hard exclusions)
    5. Combine and deduplicate results

    Key distinction:
    - Query-extracted diets/allergies = HARD constraints (pre-filter)
    - User profile diets = SOFT preferences (score boost, not exclusion)
    - User profile allergies = HARD exclusions (safety)

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

    # 1. Parse query to extract hard constraints FIRST
    # Now we also pass user_profile to include their saved preferences
    parsed_filters = parse_user_query(query, user_profile=user_profile)
    
    # Extract hard constraints from the query AND user profile
    query_diets = parsed_filters.get("diets") or []  # e.g., ["Plant Based"] from "vegan comfort food" + user profile
    query_allergies = parsed_filters.get("allergies") or []  # From query + user profile
    query_hall = parsed_filters.get("dining_hall")
    query_meal = parsed_filters.get("meal")
    
    # Goal-based nutritional preferences (soft influence, NOT hard filters)
    # These will be used to boost scores, not exclude items
    goal_min_protein = parsed_filters.get("min_protein")  # Set by "Gain Muscle" goal
    goal_max_calories = parsed_filters.get("max_calories")  # Set by "Lose Weight" goal
    
    # All allergens are hard exclusions (safety)
    all_excluded_allergens = list(set(query_allergies))

    # 2. Try text-to-SQL for structured queries
    # Pass user_profile so GPT can generate SQL with dietary constraints
    if use_text_to_sql:
        sql_items, error = text_to_sql_retrieve(query, db, limit=limit * 2, user_profile=user_profile)
        if not error and sql_items:
            for i, item in enumerate(sql_items):
                # Apply hard constraints (diets, allergies) - goals are soft
                if not _passes_hard_constraints(item, query_diets, all_excluded_allergens):
                    continue
                results_map[item.id] = item
                # Higher score for earlier results
                scores[item.id] = 1.0 - (i * 0.02)

    # 3. Semantic search WITH pre-filtering (the key fix)
    # Only diets, allergies, hall, meal are hard filters - NOT nutritional goals
    if use_semantic and PGVECTOR_AVAILABLE:
        semantic_items = semantic_search(
            query=query,
            db=db,
            limit=limit * 2,
            # Pass hard constraints for pre-filtering (diets & allergies only)
            required_diets=query_diets if query_diets else None,
            excluded_allergens=all_excluded_allergens if all_excluded_allergens else None,
            dining_hall=query_hall,
            meal=query_meal,
            # Don't pass min_protein/max_calories - goals are soft preferences
        )
        for i, item in enumerate(semantic_items):
            if item.id not in results_map:
                results_map[item.id] = item
                scores[item.id] = 0.8 - (i * 0.02)
            else:
                # Boost items that appear in both
                scores[item.id] += 0.3

    # 4. Apply goal-based preferences as SOFT score boosts (not exclusions)
    if results_map:
        for item_id, item in results_map.items():
            # Boost high-protein items for "Gain Muscle" goal
            if goal_min_protein is not None and item.protein_g is not None:
                if item.protein_g >= goal_min_protein:
                    scores[item_id] += 0.25  # Significant boost for meeting protein goal
                elif item.protein_g >= goal_min_protein * 0.75:
                    scores[item_id] += 0.1   # Smaller boost for close to goal
            
            # Boost low-calorie items for "Lose Weight" goal
            if goal_max_calories is not None and item.calories is not None:
                if item.calories <= goal_max_calories:
                    scores[item_id] += 0.25  # Significant boost for meeting calorie goal
                elif item.calories <= goal_max_calories * 1.25:
                    scores[item_id] += 0.1   # Smaller boost for close to goal

    # 5. Sort by score and return top results
    sorted_ids = sorted(results_map.keys(), key=lambda x: scores.get(x, 0), reverse=True)
    return [results_map[id_] for id_ in sorted_ids[:limit]]


def _passes_hard_constraints(
    item: DiningHallMenu,
    required_diets: List[str],
    excluded_allergens: List[str],
) -> bool:
    """Check if an item passes all hard constraints (diets and allergies only).
    
    Note: Nutritional goals (protein, calories) are NOT hard constraints.
    They are applied as soft score boosts to influence ranking without excluding items.
    
    Args:
        item: Menu item to check.
        required_diets: Diet types the item MUST have (strict).
        excluded_allergens: Allergens the item must NOT have (strict, for safety).
    
    Returns:
        True if item passes all constraints, False otherwise.
    """
    # Check required diets (HARD constraint)
    if required_diets:
        if not item.diet_types:
            return False
        item_diets = set(d.lower() for d in item.diet_types)
        for required in required_diets:
            if required.lower() not in item_diets:
                return False
    
    # Check excluded allergens (HARD constraint - safety)
    if excluded_allergens and item.allergens:
        item_allergens = set(a.lower() for a in item.allergens)
        excluded_set = set(a.lower() for a in excluded_allergens)
        if item_allergens & excluded_set:
            return False
    
    return True
