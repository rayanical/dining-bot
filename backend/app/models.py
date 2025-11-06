from sqlalchemy import Column, Integer, String, Float, ARRAY, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Note: schema shows 'password' not 'password_hash'
    
    # Relationships
    goals = relationship("Goal", back_populates="user")
    dietary_constraints = relationship("DietaryConstraint", back_populates="user")
    diet_history = relationship("DietHistory", back_populates="user")
    personal_menus = relationship("PersonalMenu", back_populates="user")

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal = Column(String, nullable=False)  # e.g., "weight loss", "muscle gain"
    success_metric = Column(String, nullable=False)
    progress = Column(String, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="goals")

class DietaryConstraint(Base):
    __tablename__ = "dietary_constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    constraint = Column(String, nullable=False)  # e.g., "peanut allergy"
    constraint_type = Column(String, nullable=False)  # e.g., "allergy", "preference"
    
    # Relationships
    user = relationship("User", back_populates="dietary_constraints")

class DietHistory(Base):
    __tablename__ = "diet_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    item = Column(String, nullable=False)
    mealtime = Column(String, nullable=False)  # e.g., "breakfast", "lunch"
    calories = Column(Float, nullable=False)
    allergens = Column(ARRAY(String), nullable=False)  # PostgreSQL array
    diet_types = Column(ARRAY(String), nullable=False)  # PostgreSQL array
    
    # Relationships
    user = relationship("User", back_populates="diet_history")

class PersonalMenu(Base):
    __tablename__ = "personal_menu"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item = Column(String, nullable=False)
    calories = Column(Float, nullable=True)
    allergens = Column(ARRAY(String), nullable=True)  # PostgreSQL array
    diet_types = Column(ARRAY(String), nullable=True)  # PostgreSQL array
    
    # Relationships
    user = relationship("User", back_populates="personal_menus")

class DiningHallMenu(Base):
    """
    Main menu table - stores all food items available in dining halls.
    This matches the 'dining_hall_menu' table in Supabase.
    """
    __tablename__ = "dining_hall_menu"
    
    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False, index=True)  # Name of the food item
    dining_hall = Column(String, nullable=False, index=True)  # 'Berkshire', 'Worcester', etc.
    calories = Column(Float, nullable=True)
    allergens = Column(ARRAY(String), nullable=True)  # PostgreSQL array of allergens
    diet_types = Column(ARRAY(String), nullable=True)  # PostgreSQL array: ['Vegan', 'Vegetarian', etc.]
    availability_today = Column(ARRAY(String), nullable=True)  # PostgreSQL array: ['breakfast', 'lunch', 'dinner']
    
    # Note: The scraper provides more detailed data (protein, carbs, etc.)
    # but the schema only stores: item, dining_hall, calories, allergens, diet_types, availability_today
    # We'll map the scraper data to match this schema
