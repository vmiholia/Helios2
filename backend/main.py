"""
Helios2 Backend API - Clean Architecture
Routes use services layer for business logic
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
import database
import services

app = FastAPI(title="Helios2 API", description="Telegram-based health tracker with vClaw")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
database.init_db()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Health Check ---
@app.get("/")
def root():
    return {"status": "Helios2 is running!"}


# --- Log Pre-parsed Food (from AI conversation) ---
@app.post("/log_parsed/")
async def log_parsed_food(request: schemas.LogParsedRequest, db: Session = Depends(get_db)):
    """
    Log food items that were already parsed by AI in conversation.
    Tracks all 34 nutrients (8 macros + 13 vitamins + 13 minerals)
    """
    result = services.log_food_items(db, request.user_id, request.items, request.raw_text)
    return {"status": "success", **result}


# --- Food Items API ---
@app.post("/food/", response_model=schemas.FoodItemResponse)
def create_food_item(food: schemas.FoodItemCreate, db: Session = Depends(get_db)):
    """Create a new food item"""
    db_food = models.FoodItem(**food.dict())
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food


@app.get("/food/", response_model=List[schemas.FoodItemResponse])
def get_food_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all food items"""
    return db.query(models.FoodItem).offset(skip).limit(limit).all()


@app.get("/food/search/{query}")
def search_food(query: str, db: Session = Depends(get_db)):
    """Search for food items - exact match first, then fuzzy"""
    # Try exact match first
    foods = db.query(models.FoodItem).filter(
        models.FoodItem.name.ilike(query)
    ).all()
    
    if foods:
        return foods
    
    # Fall back to fuzzy match
    foods = db.query(models.FoodItem).filter(
        models.FoodItem.name.ilike(f"%{query}%")
    ).all()
    return foods


# --- Daily Log API ---
@app.get("/daily/{user_id}", response_model=schemas.DailyLogResponse)
def get_daily_log(user_id: str, date: str, db: Session = Depends(get_db)):
    """Get daily nutrient summary"""
    log = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user_id,
        models.DailyLog.date == date
    ).first()
    
    if not log:
        # Return empty summary with all 34 nutrients
        return {
            "id": 0,
            "user_id": user_id,
            "date": date,
            "total_calories": 0,
            "total_protein": 0,
            "total_carbohydrates": 0,
            "total_fats": 0,
            "total_fiber": 0,
            "total_water": 0,
            "total_sugar": 0,
            "total_vitamin_a_mcg": 0, "total_vitamin_d_mcg": 0, "total_vitamin_e_mg": 0,
            "total_vitamin_k_mcg": 0, "total_vitamin_b1_mg": 0, "total_vitamin_b2_mg": 0,
            "total_vitamin_b3_mg": 0, "total_vitamin_b5_mg": 0, "total_vitamin_b6_mg": 0,
            "total_vitamin_b7_mcg": 0, "total_vitamin_b9_mcg": 0, "total_vitamin_b12_mcg": 0,
            "total_vitamin_c_mg": 0, "total_calcium_mg": 0, "total_iron_mg": 0,
            "total_magnesium_mg": 0, "total_phosphorus_mg": 0, "total_potassium_mg": 0,
            "total_sodium_mg": 0, "total_zinc_mg": 0, "total_selenium_mcg": 0,
            "total_copper_mg": 0, "total_manganese_mg": 0,
            "average_surity": 0
        }
    
    return log


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
