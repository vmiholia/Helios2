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
    
    # Macros (8)
    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbohydrates = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    fiber = Column(Float, default=0.0)
    water = Column(Float, default=0.0)
    sugar = Column(Float, default=0.0)
    
    # Vitamins (13)
    vitamin_a_mcg = Column(Float, default=0.0)
    vitamin_d_mcg = Column(Float, default=0.0)
    vitamin_e_mg = Column(Float, default=0.0)
    vitamin_k_mcg = Column(Float, default=0.0)
    vitamin_b1_mg = Column(Float, default=0.0)
    vitamin_b2_mg = Column(Float, default=0.0)
    vitamin_b3_mg = Column(Float, default=0.0)
    vitamin_b5_mg = Column(Float, default=0.0)
    vitamin_b6_mg = Column(Float, default=0.0)
    vitamin_b7_mcg = Column(Float, default=0.0)
    vitamin_b9_mcg = Column(Float, default=0.0)
    vitamin_b12_mcg = Column(Float, default=0.0)
    vitamin_c_mg = Column(Float, default=0.0)
    
    # Minerals (13)
    calcium_mg = Column(Float, default=0.0)
    iron_mg = Column(Float, default=0.0)
    magnesium_mg = Column(Float, default=0.0)
    phosphorus_mg = Column(Float, default=0.0)
    potassium_mg = Column(Float, default=0.0)
    sodium_mg = Column(Float, default=0.0)
    zinc_mg = Column(Float, default=0.0)
    selenium_mcg = Column(Float, default=0.0)
    copper_mg = Column(Float, default=0.0)
    manganese_mg = Column(Float, default=0.0)
    
    # Detailed nutrients (JSON) - for future expansion
    carbohydrates_detail = Column(JSON, default=dict)
    protein_detail = Column(JSON, default=dict)
    fats_detail = Column(JSON, default=dict)
    vitamins_json = Column(JSON, default=dict)
    minerals_json = Column(JSON, default=dict)
    phytonutrients = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyLog(Base):
    """Daily summary for a user"""
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD
    
    # Daily totals - Macros (8)
    total_calories = Column(Float, default=0.0)
    total_protein = Column(Float, default=0.0)
    total_carbohydrates = Column(Float, default=0.0)
    total_fats = Column(Float, default=0.0)
    total_fiber = Column(Float, default=0.0)
    total_water = Column(Float, default=0.0)
    total_sugar = Column(Float, default=0.0)
    
    # Daily totals - Vitamins (13)
    total_vitamin_a_mcg = Column(Float, default=0.0)
    total_vitamin_d_mcg = Column(Float, default=0.0)
    total_vitamin_e_mg = Column(Float, default=0.0)
    total_vitamin_k_mcg = Column(Float, default=0.0)
    total_vitamin_b1_mg = Column(Float, default=0.0)
    total_vitamin_b2_mg = Column(Float, default=0.0)
    total_vitamin_b3_mg = Column(Float, default=0.0)
    total_vitamin_b5_mg = Column(Float, default=0.0)
    total_vitamin_b6_mg = Column(Float, default=0.0)
    total_vitamin_b7_mcg = Column(Float, default=0.0)
    total_vitamin_b9_mcg = Column(Float, default=0.0)
    total_vitamin_b12_mcg = Column(Float, default=0.0)
    total_vitamin_c_mg = Column(Float, default=0.0)
    
    # Daily totals - Minerals (13)
    total_calcium_mg = Column(Float, default=0.0)
    total_iron_mg = Column(Float, default=0.0)
    total_magnesium_mg = Column(Float, default=0.0)
    total_phosphorus_mg = Column(Float, default=0.0)
    total_potassium_mg = Column(Float, default=0.0)
    total_sodium_mg = Column(Float, default=0.0)
    total_zinc_mg = Column(Float, default=0.0)
    total_selenium_mcg = Column(Float, default=0.0)
    total_copper_mg = Column(Float, default=0.0)
    total_manganese_mg = Column(Float, default=0.0)
    
    # Average surity for the day
    average_surity = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
