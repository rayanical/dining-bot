from typing import Dict, List, Optional
from sqlalchemy import and_, or_, func, String
from sqlalchemy.orm import Session
from app.models import DiningHallMenu
from app.core.query_parser import parse_user_query

def build_sql_filters(filters: Dict, db: Session) -> List:
    """Build SQLAlchemy filter conditions from parsed query filters.

    This function constructs a list of SQLAlchemy expressions based on structured
    filters and the current database engine, handling both PostgreSQL and SQLite
    differences for array-like fields.

    Args:
        filters (Dict): Parsed filters (e.g., dining_hall, meal, diets, allergies,
            min_calories, max_calories).
        db (Session): SQLAlchemy database session.

    Returns:
        List: A list of SQLAlchemy boolean expressions to pass to Query.filter().
    """
    conditions = []
    
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
                # This avoids the ARRAY.contains() issue
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
    
    # Note: The schema doesn't have protein_g, so we can't filter by protein
    # We'll order by calories or just return items sorted by name
    
    
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
    order_by: str = "calories"
) -> List[DiningHallMenu]:
    """Retrieve relevant menu items based on a natural language query.

    Args:
        query (str): User's natural language question.
        db (Session): SQLAlchemy database session.
        user_profile (Optional[Dict]): Optional user profile influencing filters
            (e.g., diets, allergies, goals).
        limit (int): Maximum number of rows to return. Defaults to 10.
        order_by (str): Field to order by. Currently informational; the function
            chooses ordering based on query semantics.

    Returns:
        List[DiningHallMenu]: The list of matching menu rows.
    """
    filters = parse_user_query(query, user_profile)
    conditions = build_sql_filters(filters, db)
    q = db.query(DiningHallMenu)
    if conditions:
        q = q.filter(and_(*conditions))
    
    # Order by (note: schema doesn't have protein_g, so we order by calories or item name)
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
        q = q.order_by(DiningHallMenu.item.asc())
    
    items = q.limit(limit).all()
    
    return items

