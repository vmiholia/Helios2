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
    vitamins: Dict
    minerals: Dict
    average_surity: float

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
