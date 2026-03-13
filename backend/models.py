"""
Helios2 Database Models
Detailed nutrient tracking with surity percentage
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class FoodItem(Base):
    """Master food database with detailed nutrients"""
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Surity percentage (0-100) - how confident we are in the nutrient data
    surity_percentage = Column(Float, default=0.0)
    
    # Standard serving info
    default_serving_grams = Column(Float, default=100.0)
    serving_unit = Column(String, default="g")
    
    # Macronutrients (per 100g)
    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbohydrates = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    fiber = Column(Float, default=0.0)
    water = Column(Float, default=0.0)
    sugar = Column(Float, default=0.0)
    
    # Detailed Carbohydrates (stored as JSON)
    carbohydrates_detail = Column(JSON, default=dict)
    
    # Detailed Proteins (stored as JSON)  
    protein_detail = Column(JSON, default=dict)
    
    # Detailed Fats (stored as JSON)
    fats_detail = Column(JSON, default=dict)
    
    # Micronutrients - Vitamins (per 100g)
    vitamins = Column(JSON, default=dict)
    
    # Micronutrients - Minerals (per 100g)
    minerals = Column(JSON, default=dict)
    
    # Micronutrients - Phytonutrients (per 100g)
    phytonutrients = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entries = relationship("FoodEntry", back_populates="food_item")


class FoodEntry(Base):
    """User's food log entry"""
    __tablename__ = "food_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # Telegram user ID
    
    # Food reference
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    food_item = relationship("FoodItem", back_populates="entries")
    
    # Consumption details
    quantity = Column(Float, default=1.0)
    serving_grams = Column(Float)
    
    # Time
    logged_at = Column(DateTime, default=datetime.utcnow)
    ingested_at = Column(DateTime)  # When food was consumed
    
    # Raw input text
    raw_text = Column(String)
    
    # Calculated nutrients (snapshot at time of logging)
    # Surity percentage - how confident we are in these values
    surity_percentage = Column(Float, default=0.0)
    
    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbohydrates = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    fiber = Column(Float, default=0.0)
    water = Column(Float, default=0.0)
    sugar = Column(Float, default=0.0)
    
    # Detailed nutrients (JSON)
    carbohydrates_detail = Column(JSON, default=dict)
    protein_detail = Column(JSON, default=dict)
    fats_detail = Column(JSON, default=dict)
    vitamins = Column(JSON, default=dict)
    minerals = Column(JSON, default=dict)
    phytonutrients = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyLog(Base):
    """Daily summary for a user"""
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD
    
    # Daily totals
    total_calories = Column(Float, default=0.0)
    total_protein = Column(Float, default=0.0)
    total_carbohydrates = Column(Float, default=0.0)
    total_fats = Column(Float, default=0.0)
    total_fiber = Column(Float, default=0.0)
    total_water = Column(Float, default=0.0)
    total_sugar = Column(Float, default=0.0)
    
    # Detailed daily totals (JSON)
    vitamins = Column(JSON, default=dict)
    minerals = Column(JSON, default=dict)
    
    # Average surity for the day
    average_surity = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
