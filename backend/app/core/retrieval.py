from typing import Dict, List, Optional
from datetime import date
from sqlalchemy import and_, or_, func, String
from sqlalchemy.orm import Session
from app.models import DiningHallMenu, PGVECTOR_AVAILABLE
from app.core.query_parser import parse_user_query

def build_sql_filters(filters: Dict, db: Session, current_date: Optional[date] = None) -> List:
    """Build SQLAlchemy filter conditions from parsed query filters.

    Args:
        filters (Dict): Parsed filters (e.g., dining_hall, meal, diets, allergies,
            min_calories, max_calories, item_name).
        db (Session): SQLAlchemy database session.
        current_date (Optional[date]): The current date to filter by. If None, uses today's date.

    Returns:
        List: A list of SQLAlchemy boolean expressions to pass to Query.filter().
    """
    conditions = []
    
    # CRITICAL: Always filter by today's date to avoid stale "ghost" menu items
    filter_date = current_date or date.today()
    conditions.append(DiningHallMenu.last_updated == filter_date)
    
    # --- NEW: Handle Text Search ("item_name") ---
    if filters.get("item_name"):
        search_term = filters["item_name"]
        # Use ilike for case-insensitive matching
        conditions.append(DiningHallMenu.item.ilike(f"%{search_term}%"))
    # ---------------------------------------------

    if filters.get("dining_hall"):
        conditions.append(DiningHallMenu.dining_hall == filters["dining_hall"])
    
    if filters.get("meal"):
        # Meal is already lowercase from query parser to match database format
        meal_filter = filters["meal"].lower()  # Ensure lowercase for safety
        if "postgres" in str(db.bind.url).lower():
            # PostgreSQL: use array_to_string to search in array
            conditions.append(func.array_to_string(DiningHallMenu.availability_today, ',').ilike(f'%{meal_filter}%'))
        else:
            # SQLite fallback
            conditions.append(func.cast(DiningHallMenu.availability_today, String).like(f'%"{meal_filter}"%'))
    
    if filters.get("diets"):
        diet_conditions = []
        db_url = str(db.bind.url).lower()
        
        # Check if we're using PostgreSQL
        is_postgres = "postgres" in db_url
        
        for diet in filters["diets"]:
            if is_postgres:
                # PostgreSQL: Use array_to_string to convert array to string, then search
                diet_conditions.append(func.array_to_string(DiningHallMenu.diet_types, ',').ilike(f'%{diet}%'))
            else:
                # SQLite: ARRAY type doesn't work, so we check using string operations
                diet_conditions.append(
                    func.cast(DiningHallMenu.diet_types, String).like(f'%"{diet}"%')
                    if hasattr(func, 'cast')
                    else func.array_to_string(DiningHallMenu.diet_types, ',').ilike(f'%{diet}%')
                )
        
        if diet_conditions:
            try:
                conditions.append(or_(*diet_conditions))
            except Exception:
                for condition in diet_conditions:
                    conditions.append(condition)
    
    if filters.get("allergies"):
        for allergen in filters["allergies"]:
            if "postgres" in str(db.bind.url).lower():
                # PostgreSQL: Use array_to_string to search, then negate
                conditions.append(~func.array_to_string(DiningHallMenu.allergens, ',').ilike(f'%{allergen}%'))
            else:
                conditions.append(~func.cast(DiningHallMenu.allergens, String).like(f'%"{allergen}"%'))
    
    if filters.get("min_calories") is not None:
        conditions.append(DiningHallMenu.calories >= filters["min_calories"])
    if filters.get("max_calories") is not None:
        conditions.append(DiningHallMenu.calories <= filters["max_calories"])
    
    return conditions


def retrieve_food_items(
    query: str,
    db: Session,
    user_profile: Optional[Dict] = None,
    limit: int = 10,
    order_by: str = "calories",
    use_hybrid: bool = True,
    structured_filters: Optional[Dict] = None,
    current_date: Optional[date] = None,
) -> List[DiningHallMenu]:
    """Retrieve relevant menu items based on a natural language query.

    Args:
        query (str): User's natural language question.
        db (Session): SQLAlchemy database session.
        user_profile (Optional[Dict]): Optional user profile influencing filters.
        limit (int): Maximum number of rows to return.
        order_by (str): Field to order by.
        use_hybrid (bool): Whether to use the hybrid retrieval approach.
        structured_filters (Optional[Dict]): Manual UI-selected filters (dining_hall, meal, item_name)
            that override or augment the parsed query.
        current_date (Optional[date]): Date to filter by.

    Returns:
        List[DiningHallMenu]: The list of matching menu rows.
    """
    
    # Bypass Hybrid logic if specific structured filters are present (like search term or hall)
    # This prevents the LLM/Vector search from overthinking a simple database lookup
    if structured_filters and (structured_filters.get("item_name") or structured_filters.get("dining_hall")):
        return _legacy_retrieve(query, db, user_profile, limit, order_by, structured_filters, current_date)

    # Try hybrid retrieval first (GPT SQL + semantic search)
    if use_hybrid:
        try:
            from app.core.semantic_retrieval import hybrid_retrieve
            
            results = hybrid_retrieve(
                query=query,
                db=db,
                user_profile=user_profile,
                limit=limit,
                use_semantic=PGVECTOR_AVAILABLE,
                use_text_to_sql=True,
                manual_filters=structured_filters,
                current_date=current_date,
            )
            
            if results:
                return results
        except Exception as e:
            # Log but don't fail - fall back to legacy approach
            print(f"[Retrieval] Hybrid retrieval failed, falling back: {e}")

    # Fallback: Legacy keyword-based retrieval
    return _legacy_retrieve(query, db, user_profile, limit, order_by, structured_filters, current_date)


def _legacy_retrieve(
    query: str,
    db: Session,
    user_profile: Optional[Dict] = None,
    limit: int = 10,
    order_by: str = "calories",
    structured_filters: Optional[Dict] = None,
    current_date: Optional[date] = None,
) -> List[DiningHallMenu]:
    """Legacy retrieval using regex-parsed filters and SQLAlchemy queries.
    
    Kept as fallback when hybrid retrieval fails or is disabled.
    """
    filters = parse_user_query(query, user_profile)

    # Merge structured filters into parsed filters
    if structured_filters:
        for k, v in structured_filters.items():
            if v is not None:
                filters[k] = v

    conditions = build_sql_filters(filters, db, current_date)
    q = db.query(DiningHallMenu)
    if conditions:
        q = q.filter(and_(*conditions))
    
    # Order by logic
    query_lower = query.lower()
    if "best" in query_lower or "top" in query_lower or "highest" in query_lower:
        if "calorie" in query_lower and "low" in query_lower:
            q = q.order_by(DiningHallMenu.calories.asc())
        elif "calorie" in query_lower:
            q = q.order_by(DiningHallMenu.calories.desc())
        else:
            # Default: order by item name
            q = q.order_by(DiningHallMenu.item.asc())
    else:
        # Default sort for lists
        q = q.order_by(DiningHallMenu.dining_hall.asc(), DiningHallMenu.item.asc())
    
    items = q.limit(limit).all()
    
    return items