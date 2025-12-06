from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class UserProfileCreate(BaseModel):
    user_id: str
    email: str
    diets: List[str]
    allergies: List[str]
    goal: str
    dislikes: Optional[str] = None


class FoodLogCreate(BaseModel):
    """Payload for logging a food entry to a user's diet history."""

    item_name: str
    calories: float
    protein: Optional[float] = None
    meal_type: str  # expected: breakfast | lunch | dinner | grab' n go | late night
    date: date