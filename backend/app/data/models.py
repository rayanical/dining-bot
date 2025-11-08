import datetime
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    dining_hall = Column(String, index=True)
    meal = Column(String, index=True)
    station = Column(String)
    
    # Nutritional Info
    serving_size = Column(String)
    calories = Column(Float)
    fat_g = Column(Float)
    sat_fat_g = Column(Float)
    trans_fat_g = Column(Float)
    cholesterol_mg = Column(Float)
    sodium_mg = Column(Float)
    carbs_g = Column(Float)
    fiber_g = Column(Float)
    sugars_g = Column(Float)
    protein_g = Column(Float)
    
    # Ingredients and Diets
    allergens = Column(Text)
    ingredients = Column(Text)
    diets = Column(JSON)  # Stores the list of diet tags (e.g., ["Vegan", "Halal"])

    # Relationships
    logs = relationship("UserMealLog", back_populates="food_item")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    meal_logs = relationship("UserMealLog", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Onboarding data
    diets = Column(JSON)         # Stores list: ['Vegan', 'Vegetarian']
    allergies = Column(Text)     # Stores string: "Peanuts, Dairy, Gluten"
    goal = Column(String)        # Stores string: 'Lose Weight', 'Gain Muscle'
    cuisines = Column(JSON)      # Stores list: ['Mediterranean', 'East Asian']
    dislikes = Column(Text)      # Stores string: "Olives, Tofu"

    # Relationships
    user = relationship("User", back_populates="profile")

class UserMealLog(Base):
    __tablename__ = "user_meal_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meal_logs")
    food_item = relationship("FoodItem", back_populates="logs")