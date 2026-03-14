"""
Helios2 Backend API - With LLM Integration
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime
import sys
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models
import schemas
import database
from services import llm_parser
from evals_simple import log_pipeline_run

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


# --- Parse & Log (The Magic) ---
@app.post("/parse_and_log/")
async def parse_and_log(request: schemas.ParseRequest, db: Session = Depends(get_db)):
    """
    Parse natural language and log food using LLM
    """
    user_id = request.user_id
    text = request.text
    
    # Use LLM to parse
    parsed_data = await llm_parser.parse_food_text(text, user_id)
    
    if "error" in parsed_data:
        return {"status": "error", "message": parsed_data["error"]}
    
    # Handle both single item and array
    items = parsed_data if isinstance(parsed_data, list) else [parsed_data]
    
    logged_entries = []
    
    for item in items:
        surity = item.get("surity_percentage", 50)
        
        # Calculate actual nutrients based on quantity
        multiplier = item.get("estimated_grams", 100) / 100.0
        
        # Create or find food item
        food_name = item.get("name", "Unknown")
        
        # Check if food exists
        food = db.query(models.FoodItem).filter(
            models.FoodItem.name.ilike(f"%{food_name}%")
        ).first()
        
        if not food:
            # Create new food item
            food = models.FoodItem(
                name=food_name,
                surity_percentage=surity,
                default_serving_grams=item.get("estimated_grams", 100),
                calories=item.get("calories", 0),
                protein=item.get("protein", 0),
                carbohydrates=item.get("carbohydrates", 0),
                fats=item.get("fats", 0),
                fiber=item.get("fiber", 0),
                sugar=item.get("sugar", 0),
                water=item.get("water", 0),
            )
            db.add(food)
            db.commit()
            db.refresh(food)
        
        # Create log entry
        entry = models.FoodEntry(
            user_id=user_id,
            food_item_id=food.id,
            quantity=item.get("quantity", 1),
            serving_grams=item.get("estimated_grams", 100),
            raw_text=text,
            surity_percentage=surity,
            ingested_at=datetime.now(),
            calories=item.get("calories", 0) * multiplier,
            protein=item.get("protein", 0) * multiplier,
            carbohydrates=item.get("carbohydrates", 0) * multiplier,
            fats=item.get("fats", 0) * multiplier,
            fiber=item.get("fiber", 0) * multiplier,
            sugar=item.get("sugar", 0) * multiplier,
            water=item.get("water", 0) * multiplier,
        )
        
        db.add(entry)
        logged_entries.append(entry)
        
        # Update daily log
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_log = db.query(models.DailyLog).filter(
            models.DailyLog.user_id == user_id,
            models.DailyLog.date == date_str
        ).first()
        
        if not daily_log:
            daily_log = models.DailyLog(
                user_id=user_id,
                date=date_str,
                total_calories=0,
                total_protein=0,
                total_carbohydrates=0,
                total_fats=0,
                total_fiber=0,
                total_water=0,
                total_sugar=0,
                average_surity=0
            )
            db.add(daily_log)
        
        # Update daily totals
        daily_log.total_calories += entry.calories
        daily_log.total_protein += entry.protein
        daily_log.total_carbohydrates += entry.carbohydrates
        daily_log.total_fats += entry.fats
        daily_log.total_fiber += entry.fiber
        daily_log.total_water += entry.water
        daily_log.total_sugar += entry.sugar
    
    db.commit()
    
    # Calculate average surity
    avg_surity = sum(e.surity_percentage for e in logged_entries) / len(logged_entries) if logged_entries else 0
    
    # Log to evals for review
    await log_pipeline_run(text, items, source="fallback")
    
    return {
        "status": "success",
        "items_logged": len(logged_entries),
        "total_calories": sum(e.calories for e in logged_entries),
        "average_surity": avg_surity
    }


# --- Log Pre-parsed Food (from AI conversation) ---
@app.post("/log_parsed/")
async def log_parsed_food(request: schemas.LogParsedRequest, db: Session = Depends(get_db)):
    """
    Log food items that were already parsed by AI in conversation.
    No parsing needed - just log directly.
    Tracks all 34 nutrients (8 macros + 13 vitamins + 13 minerals)
    """
    user_id = request.user_id
    items = request.items
    raw_text = request.raw_text
    
    logged_entries = []
    
    for item in items:
        # Create or find food item
        food_name = item.name
        
        # Check if food exists
        food = db.query(models.FoodItem).filter(
            models.FoodItem.name.ilike(f"%{food_name}%")
        ).first()
        
        if not food:
            # Create new food item
            food = models.FoodItem(
                name=food_name,
                surity_percentage=item.surity_percentage,
                default_serving_grams=item.estimated_grams,
                calories=item.calories,
                protein=item.protein,
                carbohydrates=item.carbohydrates,
                fats=item.fats,
                fiber=item.fiber,
                sugar=item.sugar,
                water=item.water,
            )
            db.add(food)
            db.commit()
            db.refresh(food)
        
        # Create log entry with all 34 nutrients
        entry = models.FoodEntry(
            user_id=user_id,
            food_item_id=food.id,
            quantity=item.quantity,
            serving_grams=item.estimated_grams,
            raw_text=raw_text,
            surity_percentage=item.surity_percentage,
            ingested_at=datetime.now(),
            # Macros (8)
            calories=item.calories,
            protein=item.protein,
            carbohydrates=item.carbohydrates,
            fats=item.fats,
            fiber=item.fiber,
            water=item.water,
            sugar=item.sugar,
            # Vitamins (13)
            vitamin_a_mcg=item.vitamin_a_mcg,
            vitamin_d_mcg=item.vitamin_d_mcg,
            vitamin_e_mg=item.vitamin_e_mg,
            vitamin_k_mcg=item.vitamin_k_mcg,
            vitamin_b1_mg=item.vitamin_b1_mg,
            vitamin_b2_mg=item.vitamin_b2_mg,
            vitamin_b3_mg=item.vitamin_b3_mg,
            vitamin_b5_mg=item.vitamin_b5_mg,
            vitamin_b6_mg=item.vitamin_b6_mg,
            vitamin_b7_mcg=item.vitamin_b7_mcg,
            vitamin_b9_mcg=item.vitamin_b9_mcg,
            vitamin_b12_mcg=item.vitamin_b12_mcg,
            vitamin_c_mg=item.vitamin_c_mg,
            # Minerals (13)
            calcium_mg=item.calcium_mg,
            iron_mg=item.iron_mg,
            magnesium_mg=item.magnesium_mg,
            phosphorus_mg=item.phosphorus_mg,
            potassium_mg=item.potassium_mg,
            sodium_mg=item.sodium_mg,
            zinc_mg=item.zinc_mg,
            selenium_mcg=item.selenium_mcg,
            copper_mg=item.copper_mg,
            manganese_mg=item.manganese_mg,
        )
        
        db.add(entry)
        logged_entries.append(entry)
    
    # Update daily log ONCE after all entries are created
    date_str = datetime.now().strftime("%Y-%m-%d")
    daily_log = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user_id,
        models.DailyLog.date == date_str
    ).first()
    
    if not daily_log:
        # Initialize all 34 nutrients to 0
        daily_log = models.DailyLog(
            user_id=user_id,
            date=date_str,
            total_calories=0, total_protein=0, total_carbohydrates=0, total_fats=0,
            total_fiber=0, total_water=0, total_sugar=0,
            total_vitamin_a_mcg=0, total_vitamin_d_mcg=0, total_vitamin_e_mg=0,
            total_vitamin_k_mcg=0, total_vitamin_b1_mg=0, total_vitamin_b2_mg=0,
            total_vitamin_b3_mg=0, total_vitamin_b5_mg=0, total_vitamin_b6_mg=0,
            total_vitamin_b7_mcg=0, total_vitamin_b9_mcg=0, total_vitamin_b12_mcg=0,
            total_vitamin_c_mg=0, total_calcium_mg=0, total_iron_mg=0,
            total_magnesium_mg=0, total_phosphorus_mg=0, total_potassium_mg=0,
            total_sodium_mg=0, total_zinc_mg=0, total_selenium_mcg=0,
            total_copper_mg=0, total_manganese_mg=0
        )
        db.add(daily_log)
    
    # Add up all 34 nutrients
    for entry in logged_entries:
        # Macros (8)
        daily_log.total_calories += entry.calories
        daily_log.total_protein += entry.protein
        daily_log.total_carbohydrates += entry.carbohydrates
        daily_log.total_fats += entry.fats
        daily_log.total_fiber += entry.fiber
        daily_log.total_water += entry.water
        daily_log.total_sugar += entry.sugar
        
        # Vitamins (13)
        daily_log.total_vitamin_a_mcg += entry.vitamin_a_mcg
        daily_log.total_vitamin_d_mcg += entry.vitamin_d_mcg
        daily_log.total_vitamin_e_mg += entry.vitamin_e_mg
        daily_log.total_vitamin_k_mcg += entry.vitamin_k_mcg
        daily_log.total_vitamin_b1_mg += entry.vitamin_b1_mg
        daily_log.total_vitamin_b2_mg += entry.vitamin_b2_mg
        daily_log.total_vitamin_b3_mg += entry.vitamin_b3_mg
        daily_log.total_vitamin_b5_mg += entry.vitamin_b5_mg
        daily_log.total_vitamin_b6_mg += entry.vitamin_b6_mg
        daily_log.total_vitamin_b7_mcg += entry.vitamin_b7_mcg
        daily_log.total_vitamin_b9_mcg += entry.vitamin_b9_mcg
        daily_log.total_vitamin_b12_mcg += entry.vitamin_b12_mcg
        daily_log.total_vitamin_c_mg += entry.vitamin_c_mg
        
        # Minerals (13)
        daily_log.total_calcium_mg += entry.calcium_mg
        daily_log.total_iron_mg += entry.iron_mg
        daily_log.total_magnesium_mg += entry.magnesium_mg
        daily_log.total_phosphorus_mg += entry.phosphorus_mg
        daily_log.total_potassium_mg += entry.potassium_mg
        daily_log.total_sodium_mg += entry.sodium_mg
        daily_log.total_zinc_mg += entry.zinc_mg
        daily_log.total_selenium_mcg += entry.selenium_mcg
        daily_log.total_copper_mg += entry.copper_mg
        daily_log.total_manganese_mg += entry.manganese_mg
    
    db.commit()
    
    avg_surity = sum(e.surity_percentage for e in logged_entries) / len(logged_entries) if logged_entries else 0
    
    return {
        "status": "success",
        "items_logged": len(logged_entries),
        "total_calories": sum(e.calories for e in logged_entries),
        "average_surity": avg_surity,
        "foods": [{"name": i.name, "calories": i.calories} for i in items]
    }


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
    """Search for food items"""
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
