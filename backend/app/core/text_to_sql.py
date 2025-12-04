"""
Text-to-SQL generation for natural language queries over the dining hall menu.

Uses GPT to translate user questions into safe PostgreSQL queries,
with sanitization to prevent SQL injection and dangerous operations.
"""

import re
from typing import Optional, List, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import OPENAI_API_KEY
from app.models import DiningHallMenu

_client = OpenAI(api_key=OPENAI_API_KEY)

# Schema description for GPT to understand the database structure
SCHEMA_PROMPT = """You are a SQL query generator for a university dining hall menu database.

TABLE: dining_hall_menu
COLUMNS:
- id: integer (primary key)
- item: text (food name, e.g., "Grilled Chicken Breast", "Caesar Salad")
- dining_hall: text (one of: "Berkshire", "Worcester", "Franklin", "Hampshire")
- last_updated: date
- calories: float (can be NULL)
- serving_size: text
- fat_g: float
- sat_fat_g: float
- trans_fat_g: float
- cholesterol_mg: float
- sodium_mg: float
- carbs_g: float
- fiber_g: float
- sugars_g: float
- protein_g: float
- allergens: text[] (array, e.g., ARRAY['Milk', 'Eggs', 'Wheat'])
- diet_types: text[] (array, e.g., ARRAY['Vegan', 'Vegetarian', 'Halal', 'Kosher'])
- availability_today: text[] (array, e.g., ARRAY['breakfast', 'lunch', 'dinner'])
- ingredients: text[] (array of ingredient names, e.g., ARRAY['chicken', 'olive oil', 'garlic'])

POSTGRESQL ARRAY SYNTAX:
- Check if array contains value: 'value' = ANY(column_name)
- Check if arrays overlap: column_name && ARRAY['val1', 'val2']
- Check if array contains all values: column_name @> ARRAY['val1', 'val2']

RULES:
1. Return ONLY a valid PostgreSQL SELECT query - no explanations
2. Use single quotes for strings
3. Use ILIKE for case-insensitive text matching
4. Use = ANY(column) for checking if a value is in an array
5. ALWAYS add LIMIT 25 at the end
6. NEVER use DELETE, UPDATE, DROP, INSERT, TRUNCATE, ALTER, CREATE, or GRANT
7. Only SELECT from dining_hall_menu table
8. For "best" or "highest" queries, use ORDER BY with DESC
9. For "lowest" or "least" queries, use ORDER BY with ASC
10. Handle NULL values with COALESCE when ordering by nullable columns

EXAMPLES:
User: "vegan lunch options"
SQL: SELECT * FROM dining_hall_menu WHERE 'Vegan' = ANY(diet_types) AND 'lunch' = ANY(availability_today) LIMIT 25

User: "high protein foods at Worcester"
SQL: SELECT * FROM dining_hall_menu WHERE dining_hall = 'Worcester' AND protein_g IS NOT NULL ORDER BY protein_g DESC LIMIT 25

User: "something with chicken"
SQL: SELECT * FROM dining_hall_menu WHERE 'chicken' = ANY(ingredients) OR item ILIKE '%chicken%' LIMIT 25

User: "low calorie breakfast options"
SQL: SELECT * FROM dining_hall_menu WHERE 'breakfast' = ANY(availability_today) AND calories IS NOT NULL ORDER BY calories ASC LIMIT 25

User: "gluten free options without nuts"
SQL: SELECT * FROM dining_hall_menu WHERE 'Gluten-Free' = ANY(diet_types) AND NOT ('Tree Nuts' = ANY(allergens) OR 'Peanuts' = ANY(allergens)) LIMIT 25

User: "what's for dinner at Franklin"
SQL: SELECT * FROM dining_hall_menu WHERE dining_hall = 'Franklin' AND 'dinner' = ANY(availability_today) LIMIT 25
"""

# Forbidden SQL keywords that should never appear in generated queries
FORBIDDEN_KEYWORDS = [
    "DELETE", "UPDATE", "DROP", "INSERT", "TRUNCATE", "ALTER", "CREATE",
    "GRANT", "REVOKE", "EXECUTE", "CALL", "COPY", "VACUUM", "ANALYZE",
    "CLUSTER", "COMMENT", "LOCK", "NOTIFY", "LISTEN", "UNLISTEN",
    "PREPARE", "DEALLOCATE", "SET ", "RESET", "SHOW", "BEGIN", "COMMIT",
    "ROLLBACK", "SAVEPOINT", "RELEASE", "DO ", "DECLARE"
]


def generate_sql(user_query: str) -> str:
    """Generate a SQL query from a natural language question.

    Args:
        user_query: The user's natural language question about the menu.

    Returns:
        A sanitized PostgreSQL SELECT query string.

    Raises:
        ValueError: If the generated SQL is invalid or unsafe.
    """
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SCHEMA_PROMPT},
            {"role": "user", "content": f"Generate SQL for: {user_query}"},
        ],
        temperature=0,
        max_tokens=400,
    )

    sql = response.choices[0].message.content or ""
    # debugging for ai sql generation
    print(f"\n🔍 [Text-to-SQL] Generated:\n{sql}\n")

    return sanitize_sql(sql)


def sanitize_sql(sql: str) -> str:
    """Sanitize and validate a SQL query for safety.

    Args:
        sql: The raw SQL string from GPT.

    Returns:
        A cleaned and validated SQL query.

    Raises:
        ValueError: If the SQL contains forbidden keywords or is malformed.
    """
    # Clean up markdown code blocks and whitespace
    sql = sql.strip()
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip().rstrip(";").strip()

    if not sql:
        raise ValueError("Empty SQL query generated")

    # Check for forbidden keywords
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundary check to avoid false positives
        pattern = r"\b" + re.escape(keyword.strip()) + r"\b"
        if re.search(pattern, sql_upper):
            raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

    # Must start with SELECT
    if not sql_upper.lstrip().startswith("SELECT"):
        raise ValueError("Query must be a SELECT statement")

    # Check for multiple statements (semicolon in middle)
    if ";" in sql:
        raise ValueError("Multiple SQL statements not allowed")

    # Ensure it only queries the allowed table
    if "dining_hall_menu" not in sql.lower():
        raise ValueError("Query must reference dining_hall_menu table")

    # Add LIMIT if not present
    if "LIMIT" not in sql_upper:
        sql = sql + " LIMIT 25"

    return sql


def execute_generated_sql(
    sql: str, db: Session
) -> Tuple[List[DiningHallMenu], Optional[str]]:
    """Execute a generated SQL query and return matching menu items.

    Args:
        sql: A sanitized SQL query string.
        db: SQLAlchemy database session.

    Returns:
        A tuple of (list of DiningHallMenu items, optional error message).
    """
    try:
        # Execute the raw SQL to get IDs
        result = db.execute(text(sql))
        rows = result.fetchall()

        if not rows:
            return [], None

        # Extract IDs from results (assumes first column or id column)
        ids = []
        for row in rows:
            # Try to get id from named column or first column
            if hasattr(row, "id"):
                ids.append(row.id)
            elif hasattr(row, "_mapping") and "id" in row._mapping:
                ids.append(row._mapping["id"])
            elif len(row) > 0:
                ids.append(row[0])

        if not ids:
            return [], None

        # Fetch full ORM objects
        items = db.query(DiningHallMenu).filter(DiningHallMenu.id.in_(ids)).all()
        return items, None

    except Exception as e:
        db.rollback()  # Reset transaction state to prevent cascade failures
        return [], f"SQL execution error: {str(e)}"


def text_to_sql_retrieve(
    query: str, db: Session, limit: int = 10
) -> Tuple[List[DiningHallMenu], Optional[str]]:
    """Full pipeline: generate SQL from text and execute it.

    Args:
        query: Natural language query from user.
        db: SQLAlchemy database session.
        limit: Maximum number of results to return.

    Returns:
        A tuple of (list of menu items, optional error message).
    """
    try:
        sql = generate_sql(query)
        items, error = execute_generated_sql(sql, db)
        if error:
            return [], error
        return items[:limit], None
    except ValueError as e:
        return [], f"SQL generation error: {str(e)}"
    except Exception as e:
        return [], f"Unexpected error: {str(e)}"
