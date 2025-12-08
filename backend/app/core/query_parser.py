import re
from typing import Dict, Optional

def parse_user_query(query: str, user_profile: Optional[Dict] = None) -> Dict:
    """Parse a natural language query into structured SQL filters.

    Args:
        query (str): The user's question to interpret.
        user_profile (Optional[Dict]): Optional dict with keys like "diets",
            "allergies", and "goal" to bias defaults.

    Returns:
        Dict: A dictionary of filters with keys such as "dining_hall",
        "meal", "diets", "allergies", "min_protein", "max_calories",
        and "keywords".
    """
    query_lower = query.lower()
    filters = {
        "dining_hall": None,
        "meal": None,
        "diets": [],
        "allergies": [],
        "min_protein": None,
        "max_protein": None,
        "min_calories": None,
        "max_calories": None,
        "keywords": [],
    }
    
    dining_halls = ["berkshire", "worcester", "franklin", "hampshire"]
    for hall in dining_halls:
        if hall in query_lower:
            filters["dining_hall"] = hall.capitalize()
            break
    
    # Keep meal lowercase to match database format (availability_today)
    meals = ["breakfast", "lunch", "dinner", "late night", "brunch", "grab' n go"]
    for meal in meals:
        if meal in query_lower:
            filters["meal"] = meal.lower()
            break
    
    diet_keywords = {
        "vegan": "Plant Based",
        "plant based": "Plant Based",
        "plant-based": "Plant Based",
        "vegetarian": "Vegetarian",
        "halal": "Halal",
        "kosher": "Kosher",
        "gluten-free": "Gluten-Free",
        "gluten free": "Gluten-Free",
    }
    for keyword, diet in diet_keywords.items():
        if keyword in query_lower:
            filters["diets"].append(diet)
    
    protein_patterns = [
        (r"high\s+protein", ("min_protein", 20)),
        (r"protein\s+rich", ("min_protein", 20)),
        (r"best\s+protein", ("min_protein", 15)),
        (r"(\d+)\s*g\s*protein", ("min_protein", None)),  # e.g., "20g protein"
    ]
    for pattern, (key, default) in protein_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if default is None and match.groups():
                filters[key] = float(match.group(1))
            elif default is not None:
                filters[key] = default
            break
    
    calorie_patterns = [
        (r"low\s+calorie", ("max_calories", 400)),
        (r"(\d+)\s+calories?", ("max_calories", None)),
    ]
    for pattern, (key, default) in calorie_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if default is None and match.groups():
                filters[key] = float(match.group(1))
            elif default is not None:
                filters[key] = default
            break
    
    important_words = ["best", "top", "recommend", "find", "where", "what"]
    for word in important_words:
        if word in query_lower:
            filters["keywords"].append(word)
    
    if user_profile:
        if user_profile.get("diets"):
            filters["diets"].extend(user_profile["diets"])
            filters["diets"] = list(set(filters["diets"]))
        
        if user_profile.get("allergies"):
            filters["allergies"] = user_profile["allergies"]
        
        if user_profile.get("goal") == "Gain Muscle / Weight":
            if filters["min_protein"] is None:
                filters["min_protein"] = 20
        elif user_profile.get("goal") == "Lose Weight":
            if filters["max_calories"] is None:
                filters["max_calories"] = 500
    
    return filters

