from sqlalchemy import Column, Integer, String, Float, ARRAY, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    # CHANGE: Integer -> String for Supabase UUID
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # REMOVED: password (handled by Supabase Auth)
    # OPTIONAL: You can keep username if you want a custom display name
    
    goals = relationship("Goal", back_populates="user")
    dietary_constraints = relationship("DietaryConstraint", back_populates="user")
    diet_history = relationship("DietHistory", back_populates="user")
    personal_menus = relationship("PersonalMenu", back_populates="user")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    # CHANGE: Integer -> String
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    goal = Column(String, nullable=False)
    success_metric = Column(String, nullable=True)
    progress = Column(String, nullable=True)
    user = relationship("User", back_populates="goals")

class DietaryConstraint(Base):
    __tablename__ = "dietary_constraints"
    id = Column(Integer, primary_key=True, index=True)
    # CHANGE: Integer -> String
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    constraint = Column(String, nullable=False)
    constraint_type = Column(String, nullable=False)
    user = relationship("User", back_populates="dietary_constraints")

class DietHistory(Base):
    __tablename__ = "diet_history"
    id = Column(Integer, primary_key=True, index=True)
    # CHANGE: Integer -> String
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    item = Column(String, nullable=False)
    mealtime = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    allergens = Column(ARRAY(String), nullable=False)
    diet_types = Column(ARRAY(String), nullable=False)
    user = relationship("User", back_populates="diet_history")

class PersonalMenu(Base):
    __tablename__ = "personal_menu"
    id = Column(Integer, primary_key=True, index=True)
    # CHANGE: Integer -> String
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    item = Column(String, nullable=False)
    calories = Column(Float, nullable=True)
    allergens = Column(ARRAY(String), nullable=True)
    diet_types = Column(ARRAY(String), nullable=True)
    user = relationship("User", back_populates="personal_menus")

# DiningHallMenu remains unchanged
class DiningHallMenu(Base):
    __tablename__ = "dining_hall_menu"
    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False, index=True)
    dining_hall = Column(String, nullable=False, index=True)
    calories = Column(Float, nullable=True)
    allergens = Column(ARRAY(String), nullable=True)
    diet_types = Column(ARRAY(String), nullable=True)
    availability_today = Column(ARRAY(String), nullable=True)