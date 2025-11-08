from pydantic import BaseModel
from typing import List, Optional

class UserProfileCreate(BaseModel):
    user_id: str
    email: str
    diets: List[str]
    allergies: List[str]
    goal: str
    dislikes: Optional[str] = None