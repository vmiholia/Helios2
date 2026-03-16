"""
Helios2 API Schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


# --- Base Schemas ---
class NutrientBase(BaseModel):
    """Base nutrients"""
    calories: float = 0.0
    protein: float = 0.0
    carbohydrates: float = 0.0
    fats: float = 0.0
    fiber: float = 0.0
    water: float = 0.0
    sugar: float = 0.0


# --- Food Item Schemas ---
class FoodItemCreate(NutrientBase):
    name: str
    surity_percentage: float = 0.0
    default_serving_grams: float = 100.0
    serving_unit: str = "g"
    
    # Detailed nutrients
    carbohydrates_detail: Optional[Dict] = {}
    protein_detail: Optional[Dict] = {}
    fats_detail: Optional[Dict] = {}
    vitamins: Optional[Dict] = {}
    minerals: Optional[Dict] = {}
    phytonutrients: Optional[Dict] = {}


class FoodItemResponse(FoodItemCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Food Entry Schemas ---
class FoodEntryCreate(BaseModel):
    user_id: str
    food_item_id: int
    quantity: float = 1.0
    serving_grams: Optional[float] = None
    raw_text: Optional[str] = None
    ingested_at: Optional[datetime] = None
    surity_percentage: float = 0.0
    
    # All nutrients as per food item
    calories: float = 0.0
    protein: float = 0.0
    carbohydrates: float = 0.0
    fats: float = 0.0
    fiber: float = 0.0
    water: float = 0.0
    sugar: float = 0.0
    
    carbohydrates_detail: Optional[Dict] = {}
    protein_detail: Optional[Dict] = {}
    fats_detail: Optional[Dict] = {}
    vitamins: Optional[Dict] = {}
    minerals: Optional[Dict] = {}
    phytonutrients: Optional[Dict] = {}


class FoodEntryResponse(FoodEntryCreate):
    id: int
    logged_at: datetime

    class Config:
        from_attributes = True


# --- Daily Log Schemas ---
class DailyLogResponse(BaseModel):
    id: int
    user_id: str
    date: str
    total_calories: float
    total_protein: float
    total_carbohydrates: float
    total_fats: float
    total_fiber: float
    total_water: float
    total_sugar: float
    
    # Vitamins (13)
    total_vitamin_a_mcg: float = 0.0
    total_vitamin_d_mcg: float = 0.0
    total_vitamin_e_mg: float = 0.0
    total_vitamin_k_mcg: float = 0.0
    total_vitamin_b1_mg: float = 0.0
    total_vitamin_b2_mg: float = 0.0
    total_vitamin_b3_mg: float = 0.0
    total_vitamin_b5_mg: float = 0.0
    total_vitamin_b6_mg: float = 0.0
    total_vitamin_b7_mcg: float = 0.0
    total_vitamin_b9_mcg: float = 0.0
    total_vitamin_b12_mcg: float = 0.0
    total_vitamin_c_mg: float = 0.0
    
    # Minerals (13)
    total_calcium_mg: float = 0.0
    total_iron_mg: float = 0.0
    total_magnesium_mg: float = 0.0
    total_phosphorus_mg: float = 0.0
    total_potassium_mg: float = 0.0
    total_sodium_mg: float = 0.0
    total_zinc_mg: float = 0.0
    total_selenium_mcg: float = 0.0
    total_copper_mg: float = 0.0
    total_manganese_mg: float = 0.0
    
    average_surity: float = 0.0

    class Config:
        from_attributes = True


# --- Parsing Schemas ---
class ParseRequest(BaseModel):
    """Request to parse natural language food input"""
    text: str
    user_id: str


class ParseResponse(BaseModel):
    """Response with parsed food items"""
    items: List[Dict[str, Any]]
    raw_text: str


# --- Pre-parsed Food Entry ---
class ParsedFoodItem(BaseModel):
    """Single pre-parsed food item with all 34 nutrients"""
    # Basic info
    name: str
    quantity: float = 1.0
    unit: str = "serving"
    estimated_grams: float = 100.0
    surity_percentage: float = 50.0
    
    # Macros (8)
    calories: float = 0.0
    protein: float = 0.0
    carbohydrates: float = 0.0
    fats: float = 0.0
    fiber: float = 0.0
    water: float = 0.0
    sugar: float = 0.0
    
    # Vitamins (13)
    vitamin_a_mcg: float = 0.0
    vitamin_d_mcg: float = 0.0
    vitamin_e_mg: float = 0.0
    vitamin_k_mcg: float = 0.0
    vitamin_b1_mg: float = 0.0
    vitamin_b2_mg: float = 0.0
    vitamin_b3_mg: float = 0.0
    vitamin_b5_mg: float = 0.0
    vitamin_b6_mg: float = 0.0
    vitamin_b7_mcg: float = 0.0
    vitamin_b9_mcg: float = 0.0
    vitamin_b12_mcg: float = 0.0
    vitamin_c_mg: float = 0.0
    
    # Minerals (13)
    calcium_mg: float = 0.0
    iron_mg: float = 0.0
    magnesium_mg: float = 0.0
    phosphorus_mg: float = 0.0
    potassium_mg: float = 0.0
    sodium_mg: float = 0.0
    zinc_mg: float = 0.0
    selenium_mcg: float = 0.0
    copper_mg: float = 0.0
    manganese_mg: float = 0.0


class LogParsedRequest(BaseModel):
    """Request with pre-parsed food items (from AI conversation)"""
    user_id: str
    items: List[ParsedFoodItem]
    raw_text: str = ""
    date: str = None  # Optional: YYYY-MM-DD format, defaults to today IST
