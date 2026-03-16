"""
Helios2 Backend API - Clean Architecture
Routes use services layer for business logic
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

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
    result = services.log_food_items(db, request.user_id, request.items, request.raw_text, request.date)
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


# ============================================================
# WHOOP Integration Routes
# ============================================================

import whoop_service
from pydantic import BaseModel


class WhoopAuthCallback(BaseModel):
    """OAuth callback query params"""
    code: str
    state: Optional[str] = None


@app.get("/auth/whoop/authorize")
def whoop_authorize():
    """
    Step 1: Redirect user to WHOOP OAuth authorization page
    """
    auth_url = whoop_service.whoop_service.get_authorization_url()
    return {"authorization_url": auth_url}


@app.get("/auth/whoop/callback")
async def whoop_callback(code: str, state: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Step 2: Handle OAuth callback, exchange code for token
    """
    try:
        # Exchange code for token
        token_data = await whoop_service.whoop_service.exchange_code_for_token(code)
        
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data.get("expires_in", 3600)
        
        # Get user profile
        profile = await whoop_service.whoop_service.get_user_profile(access_token)
        
        # Get body measurements
        measurements = await whoop_service.whoop_service.get_body_measurements(access_token)
        
        # Calculate token expiry
        token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Save to database (using a default user_id for now - can be tied to Telegram later)
        whoop_user = models.WhoopUser(
            user_id="vaibhav",  # TODO: Link to actual Telegram user
            whoop_user_id=str(profile["user_id"]),
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            email=profile.get("email", ""),
            first_name=profile.get("first_name", ""),
            last_name=profile.get("last_name", ""),
            height_meter=measurements.get("height_meter"),
            weight_kilogram=measurements.get("weight_kilogram"),
            max_heart_rate=measurements.get("max_heart_rate"),
            is_active=1
        )
        
        db.add(whoop_user)
        db.commit()
        
        return {
            "status": "success",
            "message": "WHOOP account connected successfully",
            "user": {
                "name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}",
                "email": profile.get("email", "")
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/whoop/status")
def whoop_status(user_id: str = "vaibhav", db: Session = Depends(get_db)):
    """Check WHOOP connection status"""
    whoop_user = db.query(models.WhoopUser).filter(
        models.WhoopUser.user_id == user_id,
        models.WhoopUser.is_active == 1
    ).first()
    
    if not whoop_user:
        return {
            "connected": False,
            "message": "No WHOOP account connected"
        }
    
    return {
        "connected": True,
        "name": f"{whoop_user.first_name} {whoop_user.last_name}",
        "email": whoop_user.email,
        "last_sync": whoop_user.last_sync_at
    }


@app.post("/whoop/sync")
async def whoop_sync(user_id: str = "vaibhav", db: Session = Depends(get_db)):
    """Sync WHOOP data for user"""
    whoop_user = db.query(models.WhoopUser).filter(
        models.WhoopUser.user_id == user_id,
        models.WhoopUser.is_active == 1
    ).first()
    
    if not whoop_user:
        return {"status": "error", "message": "No WHOOP account connected"}
    
    # Check if token needs refresh
    if whoop_user.token_expires_at and whoop_user.token_expires_at < datetime.now():
        try:
            token_data = await whoop_service.whoop_service.refresh_access_token(whoop_user.refresh_token)
            whoop_user.access_token = token_data["access_token"]
            whoop_user.refresh_token = token_data.get("refresh_token", whoop_user.refresh_token)
            whoop_user.token_expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
            db.commit()
        except Exception as e:
            return {"status": "error", "message": f"Token refresh failed: {str(e)}"}
    
    access_token = whoop_user.access_token
    
    # Sync recovery data (last 7 days)
    end_date = datetime.now().isoformat()
    start_date = (datetime.now() - timedelta(days=7)).isoformat()
    
    recovery_data = await whoop_service.whoop_service.get_recovery_collection(
        access_token, limit=10, start=start_date, end=end_date
    )
    
    cycles_data = await whoop_service.whoop_service.get_cycle_collection(
        access_token, limit=10, start=start_date, end=end_date
    )
    
    sleep_data = await whoop_service.whoop_service.get_sleep_collection(
        access_token, limit=10, start=start_date, end=end_date
    )
    
    workouts_data = await whoop_service.whoop_service.get_workout_collection(
        access_token, limit=10, start=start_date, end=end_date
    )
    
    # Save recovery records
    recovery_count = 0
    for rec in recovery_data.get("records", []):
        score = rec.get("score", {})
        cycle_id = rec.get("cycle_id")
        
        # Extract date from created_at
        created_at = rec.get("created_at")
        date_str = created_at[:10] if created_at else None
        
        # Check if already exists
        existing = db.query(models.WhoopRecovery).filter(
            models.WhoopRecovery.cycle_id == cycle_id,
            models.WhoopRecovery.whoop_user_id == str(whoop_user.whoop_user_id)
        ).first()
        
        if not existing and date_str:
            recovery = models.WhoopRecovery(
                whoop_user_id=str(whoop_user.whoop_user_id),
                cycle_id=cycle_id,
                sleep_id=rec.get("sleep_id"),
                date=date_str,
                created_at=rec.get("created_at"),
                updated_at=rec.get("updated_at"),
                score_state=rec.get("score_state"),
                recovery_score=score.get("recovery_score"),
                resting_heart_rate=score.get("resting_heart_rate"),
                hrv_rmssd_milli=score.get("hrv_rmssd_milli"),
                spo2_percentage=score.get("spo2_percentage"),
                skin_temp_celsius=score.get("skin_temp_celsius")
            )
            db.add(recovery)
            recovery_count += 1
    
    # Save cycle records
    cycle_count = 0
    for rec in cycles_data.get("records", []):
        score = rec.get("score", {})
        cycle_id = rec.get("id")
        
        start_time = rec.get("start")
        date_str = start_time[:10] if start_time else None
        
        existing = db.query(models.WhoopCycle).filter(
            models.WhoopCycle.cycle_id == cycle_id,
            models.WhoopCycle.whoop_user_id == str(whoop_user.whoop_user_id)
        ).first()
        
        if not existing and date_str:
            cycle = models.WhoopCycle(
                whoop_user_id=str(whoop_user.whoop_user_id),
                cycle_id=cycle_id,
                date=date_str,
                start=rec.get("start"),
                end=rec.get("end"),
                timezone_offset=rec.get("timezone_offset"),
                score_state=rec.get("score_state"),
                strain_score=score.get("strain"),
                kilojoule=score.get("kilojoule"),
                average_heart_rate=score.get("average_heart_rate"),
                max_heart_rate=score.get("max_heart_rate")
            )
            db.add(cycle)
            cycle_count += 1
    
    # Save sleep records
    sleep_count = 0
    for rec in sleep_data.get("records", []):
        score = rec.get("score", {})
        sleep_id = rec.get("id")
        
        start_time = rec.get("start")
        date_str = start_time[:10] if start_time else None
        
        existing = db.query(models.WhoopSleep).filter(
            models.WhoopSleep.sleep_id == sleep_id,
            models.WhoopSleep.whoop_user_id == str(whoop_user.whoop_user_id)
        ).first()
        
        if not existing and date_str:
            stage_summary = score.get("stage_summary", {})
            sleep_needed = score.get("sleep_needed", {})
            
            sleep = models.WhoopSleep(
                whoop_user_id=str(whoop_user.whoop_user_id),
                sleep_id=sleep_id,
                cycle_id=rec.get("cycle_id"),
                date=date_str,
                start=rec.get("start"),
                end=rec.get("end"),
                timezone_offset=rec.get("timezone_offset"),
                nap=1 if rec.get("nap") else 0,
                score_state=rec.get("score_state"),
                total_in_bed_time_milli=stage_summary.get("total_in_bed_time_milli"),
                total_awake_time_milli=stage_summary.get("total_awake_time_milli"),
                total_no_data_time_milli=stage_summary.get("total_no_data_time_milli"),
                total_light_sleep_time_milli=stage_summary.get("total_light_sleep_time_milli"),
                total_slow_wave_sleep_time_milli=stage_summary.get("total_slow_wave_sleep_time_milli"),
                total_rem_sleep_time_milli=stage_summary.get("total_rem_sleep_time_milli"),
                sleep_cycle_count=stage_summary.get("sleep_cycle_count"),
                disturbance_count=stage_summary.get("disturbance_count"),
                baseline_milli=sleep_needed.get("baseline_milli"),
                need_from_sleep_debt_milli=sleep_needed.get("need_from_sleep_debt_milli"),
                need_from_recent_strain_milli=sleep_needed.get("need_from_recent_strain_milli"),
                need_from_recent_nap_milli=sleep_needed.get("need_from_recent_nap_milli"),
                respiratory_rate=score.get("respiratory_rate"),
                sleep_performance_percentage=score.get("sleep_performance_percentage"),
                sleep_consistency_percentage=score.get("sleep_consistency_percentage"),
                sleep_efficiency_percentage=score.get("sleep_efficiency_percentage")
            )
            db.add(sleep)
            sleep_count += 1
    
    # Save workout records
    workout_count = 0
    for rec in workouts_data.get("records", []):
        score = rec.get("score", {})
        workout_id = rec.get("id")
        
        start_time = rec.get("start")
        date_str = start_time[:10] if start_time else None
        
        existing = db.query(models.WhoopWorkout).filter(
            models.WhoopWorkout.workout_id == workout_id,
            models.WhoopWorkout.whoop_user_id == str(whoop_user.whoop_user_id)
        ).first()
        
        if not existing and date_str:
            zone_durations = score.get("zone_durations", {})
            
            workout = models.WhoopWorkout(
                whoop_user_id=str(whoop_user.whoop_user_id),
                workout_id=workout_id,
                v1_id=rec.get("v1_id"),
                sport_id=rec.get("sport_id"),
                date=date_str,
                start=rec.get("start"),
                end=rec.get("end"),
                timezone_offset=rec.get("timezone_offset"),
                sport_name=rec.get("sport_name"),
                score_state=rec.get("score_state"),
                strain_score=score.get("strain"),
                average_heart_rate=score.get("average_heart_rate"),
                max_heart_rate=score.get("max_heart_rate"),
                kilojoule=score.get("kilojoule"),
                percent_recorded=score.get("percent_recorded"),
                distance_meter=score.get("distance_meter"),
                altitude_gain_meter=score.get("altitude_gain_meter"),
                altitude_change_meter=score.get("altitude_change_meter"),
                zone_zero_milli=zone_durations.get("zone_zero_milli"),
                zone_one_milli=zone_durations.get("zone_one_milli"),
                zone_two_milli=zone_durations.get("zone_two_milli"),
                zone_three_milli=zone_durations.get("zone_three_milli"),
                zone_four_milli=zone_durations.get("zone_four_milli"),
                zone_five_milli=zone_durations.get("zone_five_milli")
            )
            db.add(workout)
            workout_count += 1
    
    # Update last sync time
    whoop_user.last_sync_at = datetime.now()
    db.commit()
    
    return {
        "status": "success",
        "synced": {
            "recovery": recovery_count,
            "cycles": cycle_count,
            "sleep": sleep_count,
            "workouts": workout_count
        }
    }


@app.get("/whoop/daily/{date}")
def whoop_daily(date: str, user_id: str = "vaibhav", db: Session = Depends(get_db)):
    """Get WHOOP data for a specific date"""
    whoop_user = db.query(models.WhoopUser).filter(
        models.WhoopUser.user_id == user_id,
        models.WhoopUser.is_active == 1
    ).first()
    
    if not whoop_user:
        return {"status": "error", "message": "No WHOOP account connected"}
    
    # Get recovery
    recovery = db.query(models.WhoopRecovery).filter(
        models.WhoopRecovery.whoop_user_id == str(whoop_user.whoop_user_id),
        models.WhoopRecovery.date == date
    ).first()
    
    # Get cycle (strain)
    cycle = db.query(models.WhoopCycle).filter(
        models.WhoopCycle.whoop_user_id == str(whoop_user.whoop_user_id),
        models.WhoopCycle.date == date
    ).first()
    
    # Get sleep
    sleep = db.query(models.WhoopSleep).filter(
        models.WhoopSleep.whoop_user_id == str(whoop_user.whoop_user_id),
        models.WhoopSleep.date == date
    ).first()
    
    # Get workouts
    workouts = db.query(models.WhoopWorkout).filter(
        models.WhoopWorkout.whoop_user_id == str(whoop_user.whoop_user_id),
        models.WhoopWorkout.date == date
    ).all()
    
    return {
        "date": date,
        "recovery": {
            "score": recovery.recovery_score if recovery else None,
            "resting_hr": recovery.resting_heart_rate if recovery else None,
            "hrv": recovery.hrv_rmssd_milli if recovery else None,
            "spo2": recovery.spo2_percentage if recovery else None
        } if recovery else None,
        "strain": {
            "score": cycle.strain_score if cycle else None,
            "avg_hr": cycle.average_heart_rate if cycle else None,
            "max_hr": cycle.max_heart_rate if cycle else None
        } if cycle else None,
        "sleep": {
            "performance_pct": sleep.sleep_performance_percentage if sleep else None,
            "efficiency_pct": sleep.sleep_efficiency_percentage if sleep else None,
            "total_hours": (sleep.total_in_bed_time_milli / 3600000) if sleep and sleep.total_in_bed_time_milli else 0,
            "deep_hours": (sleep.total_slow_wave_sleep_time_milli / 3600000) if sleep and sleep.total_slow_wave_sleep_time_milli else 0,
            "rem_hours": (sleep.total_rem_sleep_time_milli / 3600000) if sleep and sleep.total_rem_sleep_time_milli else 0
        } if sleep else None,
        "workouts": [
            {
                "sport": w.sport_name,
                "strain": w.strain_score,
                "duration_minutes": ((w.zone_zero_milli or 0) + (w.zone_one_milli or 0) + (w.zone_two_milli or 0) + (w.zone_three_milli or 0) + (w.zone_four_milli or 0) + (w.zone_five_milli or 0)) / 60000
            } for w in workouts
        ]
    }
