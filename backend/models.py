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


# ============================================================
# WHOOP Integration Models
# ============================================================

class WhoopUser(Base):
    """WHOOP user OAuth tokens and profile"""
    __tablename__ = "whoop_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # Helios2 user (Telegram ID)
    
    # WHOOP OAuth tokens
    whoop_user_id = Column(String, unique=True, index=True)  # WHOOP's user ID
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    
    # Profile info
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    
    # Body measurements
    height_meter = Column(Float)
    weight_kilogram = Column(Float)
    max_heart_rate = Column(Integer)
    
    # Status
    is_active = Column(Integer, default=1)
    last_sync_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WhoopRecovery(Base):
    """WHOOP Recovery scores"""
    __tablename__ = "whoop_recovery"

    id = Column(Integer, primary_key=True, index=True)
    whoop_user_id = Column(String, index=True)
    
    # IDs
    cycle_id = Column(Integer, index=True)
    sleep_id = Column(String)
    
    # Timing
    date = Column(String, index=True)  # YYYY-MM-DD
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Score state
    score_state = Column(String)  # "SCORED", "PENDING", etc.
    
    # Recovery metrics
    recovery_score = Column(Integer)  # 0-100
    resting_heart_rate = Column(Float)  # bpm
    hrv_rmssd_milli = Column(Float)  # ms - heart rate variability
    spo2_percentage = Column(Float)  # blood oxygen
    skin_temp_celsius = Column(Float)
    
    created_at_record = Column(DateTime, default=datetime.utcnow)


class WhoopCycle(Base):
    """WHOOP Daily Cycle (Strain)"""
    __tablename__ = "whoop_cycles"

    id = Column(Integer, primary_key=True, index=True)
    whoop_user_id = Column(String, index=True)
    
    # IDs
    cycle_id = Column(Integer, unique=True, index=True)
    
    # Timing
    date = Column(String, index=True)  # YYYY-MM-DD
    start = Column(DateTime)
    end = Column(DateTime)
    timezone_offset = Column(String)
    
    # Score state
    score_state = Column(String)
    
    # Daily strain metrics
    strain_score = Column(Float)  # 0-21
    kilojoule = Column(Float)
    average_heart_rate = Column(Float)
    max_heart_rate = Column(Float)
    
    created_at_record = Column(DateTime, default=datetime.utcnow)


class WhoopSleep(Base):
    """WHOOP Sleep data"""
    __tablename__ = "whoop_sleep"

    id = Column(Integer, primary_key=True, index=True)
    whoop_user_id = Column(String, index=True)
    
    # IDs
    sleep_id = Column(String, unique=True, index=True)
    cycle_id = Column(Integer)
    
    # Timing
    date = Column(String, index=True)  # YYYY-MM-DD
    start = Column(DateTime)
    end = Column(DateTime)
    timezone_offset = Column(String)
    nap = Column(Integer)  # 0 or 1
    
    # Score state
    score_state = Column(String)
    
    # Sleep stages (in milliseconds)
    total_in_bed_time_milli = Column(Integer)
    total_awake_time_milli = Column(Integer)
    total_no_data_time_milli = Column(Integer)
    total_light_sleep_time_milli = Column(Integer)
    total_slow_wave_sleep_time_milli = Column(Integer)  # Deep sleep
    total_rem_sleep_time_milli = Column(Integer)
    sleep_cycle_count = Column(Integer)
    disturbance_count = Column(Integer)
    
    # Sleep need
    baseline_milli = Column(Integer)
    need_from_sleep_debt_milli = Column(Integer)
    need_from_recent_strain_milli = Column(Integer)
    need_from_recent_nap_milli = Column(Integer)
    
    # Other metrics
    respiratory_rate = Column(Float)
    sleep_performance_percentage = Column(Float)
    sleep_consistency_percentage = Column(Float)
    sleep_efficiency_percentage = Column(Float)
    
    created_at_record = Column(DateTime, default=datetime.utcnow)


class WhoopWorkout(Base):
    """WHOOP Workout data"""
    __tablename__ = "whoop_workouts"

    id = Column(Integer, primary_key=True, index=True)
    whoop_user_id = Column(String, index=True)
    
    # IDs
    workout_id = Column(String, unique=True, index=True)
    v1_id = Column(Integer)
    sport_id = Column(Integer)
    
    # Timing
    date = Column(String, index=True)  # YYYY-MM-DD
    start = Column(DateTime)
    end = Column(DateTime)
    timezone_offset = Column(String)
    
    # Sport
    sport_name = Column(String)
    
    # Score state
    score_state = Column(String)
    
    # Workout metrics
    strain_score = Column(Float)
    average_heart_rate = Column(Float)
    max_heart_rate = Column(Float)
    kilojoule = Column(Float)
    percent_recorded = Column(Float)
    distance_meter = Column(Float)
    altitude_gain_meter = Column(Float)
    altitude_change_meter = Column(Float)
    
    # Heart rate zones (milliseconds in each zone)
    zone_zero_milli = Column(Integer)
    zone_one_milli = Column(Integer)
    zone_two_milli = Column(Integer)
    zone_three_milli = Column(Integer)
    zone_four_milli = Column(Integer)
    zone_five_milli = Column(Integer)
    
    created_at_record = Column(DateTime, default=datetime.utcnow)
