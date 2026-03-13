"""
Helios2 Backend API - With LLM Integration
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

from . import models, schemas, database
from .services import llm_parser

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
        
        # Update average surity
        total_entries = db.query(models.FoodEntry).filter(
            models.FoodEntry.user_id == user_id,
            models.DailyLog.date == date_str
        ).count()
        
        if total_entries > 0:
            avg_surity = sum([e.surity_percentage for e in db.query(models.FoodEntry).filter(
                models.FoodEntry.user_id == user_id
            ).all()]) / total_entries
            daily_log.average_surity = avg_surity
    
    db.commit()
    
    return {
        "status": "success",
        "items_logged": len(logged_entries),
        "total_calories": sum(e.calories for e in logged_entries),
        "average_surity": sum(e.surity_percentage for e in logged_entries) / len(logged_entries) if logged_entries else 0
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
        # Return empty summary
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
            "vitamins": {},
            "minerals": {},
            "average_surity": 0
        }
    
    return log


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
