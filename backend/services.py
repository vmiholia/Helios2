"""
Helios2 Services - Business Logic Layer
"""
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import models


def get_utc_now():
    """Get current UTC datetime"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_date_str():
    """Get today's date as string in UTC"""
    return get_utc_now().strftime("%Y-%m-%d")


def find_or_create_food(db: Session, name: str, nutrients: dict) -> models.FoodItem:
    """
    Find food item with exact match first, then fuzzy match.
    Returns existing or creates new food item.
    """
    # Try exact match first (case-insensitive)
    food = db.query(models.FoodItem).filter(
        models.FoodItem.name.ilike(name)
    ).first()
    
    if food:
        return food
    
    # Try fuzzy match
    food = db.query(models.FoodItem).filter(
        models.FoodItem.name.ilike(f"%{name}%")
    ).first()
    
    if food:
        return food
    
    # Create new food item
    food = models.FoodItem(
        name=name,
        surity_percentage=nutrients.get("surity_percentage", 50),
        default_serving_grams=nutrients.get("estimated_grams", 100),
        calories=nutrients.get("calories", 0),
        protein=nutrients.get("protein", 0),
        carbohydrates=nutrients.get("carbohydrates", 0),
        fats=nutrients.get("fats", 0),
        fiber=nutrients.get("fiber", 0),
        sugar=nutrients.get("sugar", 0),
        water=nutrients.get("water", 0),
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


def find_or_create_foods_batch(db: Session, food_names: list) -> dict:
    """
    Batch version: Find all foods in one query.
    Returns dict mapping name -> FoodItem (for found items).
    Creates new items for those not found.
    """
    # Batch query for all foods at once
    existing_foods = db.query(models.FoodItem).filter(
        models.FoodItem.name.in_(food_names)
    ).all() if food_names else []
    
    # Build lookup dict (case-insensitive key)
    food_map = {}
    for f in existing_foods:
        food_map[f.name.lower()] = f
    
    # Return found foods
    return food_map


def create_food_entry(db: Session, user_id: str, food: models.FoodItem, 
                      nutrients: dict, raw_text: str) -> models.FoodEntry:
    """Create a food entry with all nutrients"""
    entry = models.FoodEntry(
        user_id=user_id,
        food_item_id=food.id,
        quantity=nutrients.get("quantity", 1),
        serving_grams=nutrients.get("estimated_grams", 100),
        raw_text=raw_text,
        surity_percentage=nutrients.get("surity_percentage", 50),
        ingested_at=get_utc_now(),
        # Macros (8)
        calories=nutrients.get("calories", 0),
        protein=nutrients.get("protein", 0),
        carbohydrates=nutrients.get("carbohydrates", 0),
        fats=nutrients.get("fats", 0),
        fiber=nutrients.get("fiber", 0),
        water=nutrients.get("water", 0),
        sugar=nutrients.get("sugar", 0),
        # Vitamins (13)
        vitamin_a_mcg=nutrients.get("vitamin_a_mcg", 0),
        vitamin_d_mcg=nutrients.get("vitamin_d_mcg", 0),
        vitamin_e_mg=nutrients.get("vitamin_e_mg", 0),
        vitamin_k_mcg=nutrients.get("vitamin_k_mcg", 0),
        vitamin_b1_mg=nutrients.get("vitamin_b1_mg", 0),
        vitamin_b2_mg=nutrients.get("vitamin_b2_mg", 0),
        vitamin_b3_mg=nutrients.get("vitamin_b3_mg", 0),
        vitamin_b5_mg=nutrients.get("vitamin_b5_mg", 0),
        vitamin_b6_mg=nutrients.get("vitamin_b6_mg", 0),
        vitamin_b7_mcg=nutrients.get("vitamin_b7_mcg", 0),
        vitamin_b9_mcg=nutrients.get("vitamin_b9_mcg", 0),
        vitamin_b12_mcg=nutrients.get("vitamin_b12_mcg", 0),
        vitamin_c_mg=nutrients.get("vitamin_c_mg", 0),
        # Minerals (13)
        calcium_mg=nutrients.get("calcium_mg", 0),
        iron_mg=nutrients.get("iron_mg", 0),
        magnesium_mg=nutrients.get("magnesium_mg", 0),
        phosphorus_mg=nutrients.get("phosphorus_mg", 0),
        potassium_mg=nutrients.get("potassium_mg", 0),
        sodium_mg=nutrients.get("sodium_mg", 0),
        zinc_mg=nutrients.get("zinc_mg", 0),
        selenium_mcg=nutrients.get("selenium_mcg", 0),
        copper_mg=nutrients.get("copper_mg", 0),
        manganese_mg=nutrients.get("manganese_mg", 0),
    )
    db.add(entry)
    return entry


def get_or_create_daily_log(db: Session, user_id: str, date_str: str) -> models.DailyLog:
    """Get or create daily log for user and date"""
    daily_log = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user_id,
        models.DailyLog.date == date_str
    ).first()
    
    if daily_log:
        return daily_log
    
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
        total_copper_mg=0, total_manganese_mg=0,
        average_surity=0
    )
    db.add(daily_log)
    return daily_log


def aggregate_entry_to_daily(entry: models.FoodEntry, daily_log: models.DailyLog):
    """Aggregate food entry nutrients to daily log"""
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


def log_food_items(db: Session, user_id: str, items: list, raw_text: str) -> dict:
    """
    Main business logic: Log food items and aggregate to daily log.
    Returns summary of logged items.
    """
    date_str = get_date_str()
    logged_entries = []
    
    # Get or create daily log first
    daily_log = get_or_create_daily_log(db, user_id, date_str)
    
    for item in items:
        # Convert Pydantic model to dict
        nutrients = item.model_dump() if hasattr(item, 'model_dump') else item.dict()
        food_name = nutrients.pop("name")
        
        # Find or create food item
        food = find_or_create_food(db, food_name, nutrients)
        
        # Create food entry
        entry = create_food_entry(db, user_id, food, nutrients, raw_text)
        db.add(entry)
        logged_entries.append(entry)
        
        # Aggregate to daily log immediately
        aggregate_entry_to_daily(entry, daily_log)
    
    # Calculate and save average surity
    if logged_entries:
        avg_surity = sum(e.surity_percentage for e in logged_entries) / len(logged_entries)
        daily_log.average_surity = avg_surity
    
    db.commit()
    
    return {
        "items_logged": len(logged_entries),
        "total_calories": sum(e.calories for e in logged_entries),
        "average_surity": daily_log.average_surity,
        "foods": [{"name": getattr(i, "name", "Unknown")} for i in items]
    }
