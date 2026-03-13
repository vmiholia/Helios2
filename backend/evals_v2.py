"""
Helios2 Evals - Pipeline Logging with Per-Nutrient Surity
Store: Text Input → Decomposition → Nutrients with surity
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict, field
import httpx


# Complete nutrient categories
NUTRIENT_CATEGORIES = {
    "macros": ["calories", "protein", "carbohydrates", "fats", "fiber", "water", "sugar"],
    "vitamins": ["vitamin_a_mcg", "vitamin_d_mcg", "vitamin_e_mg", "vitamin_k_mcg",
                 "vitamin_b1_mg", "vitamin_b2_mg", "vitamin_b3_mg", "vitamin_b5_mg",
                 "vitamin_b6_mg", "vitamin_b7_mcg", "vitamin_b9_mcg", "vitamin_b12_mcg",
                 "vitamin_c_mg"],
    "minerals": ["calcium_mg", "iron_mg", "magnesium_mg", "phosphorus_mg", "potassium_mg",
                 "sodium_mg", "zinc_mg", "selenium_mcg", "copper_mg", "manganese_mg",
                 "iodine_mcg", "chromium_mcg", "fluoride_mg", "molybdenum_mcg"]
}


@dataclass
class NutrientValue:
    """Single nutrient with value and surity"""
    value: float = 0.0
    surity: float = 0.0  # 0-100%


@dataclass
class EvalRecord:
    """Single pipeline record with per-nutrient surity"""
    timestamp: str = ""
    input_text: str = ""
    
    # Decomposition
    items_detected: List[str] = field(default_factory=list)
    quantities: List[Any] = field(default_factory=list)
    
    # Nutrients stored as {name: {value: x, surity: y}}
    nutrients: List[Dict] = field(default_factory=list)
    
    # Totals (calculated from nutrients)
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fats: float = 0.0
    
    # Metadata
    source: str = "ai_parsed"  # ai_parsed, fallback, manual
    notes: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class EvalLogger:
    """Simple logger for pipeline review"""
    
    def __init__(self, storage_file: str = "eval_logs.jsonl"):
        self.storage_file = storage_file
    
    def log(self, record: EvalRecord):
        """Append record to file"""
        with open(self.storage_file, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")
    
    def load(self) -> List[EvalRecord]:
        """Load all records"""
        records = []
        if not os.path.exists(self.storage_file):
            return records
        
        with open(self.storage_file, "r") as f:
            for line in f:
                if line.strip():
                    records.append(EvalRecord(**json.loads(line)))
        return records
    
    def print_all(self):
        """Print all records for review"""
        records = self.load()
        
        print("\n" + "="*80)
        print(f"HELIOS2 PIPELINE LOG - {len(records)} records")
        print("="*80)
        
        for i, r in enumerate(records, 1):
            print(f"\n--- Record {i} ---")
            print(f"Time: {r.timestamp}")
            print(f"Input: {r.input_text}")
            print(f"Items: {r.items_detected}")
            print(f"Quantities: {r.quantities}")
            print(f"Total: {r.total_calories:.0f}cal | P:{r.total_protein:.1f}g | C:{r.total_carbs:.1f}g | F:{r.total_fats:.1f}g")
            print(f"Source: {r.source}")
            
            # Print per-item nutrients with surity
            for j, n in enumerate(r.nutrients):
                print(f"\n  [{j+1}] {n.get('name', '?')}")
                if "nutrients" in n:
                    for nut_name, nut_data in n["nutrients"].items():
                        val = nut_data.get("value", 0)
                        sur = nut_data.get("surity", 0)
                        print(f"      {nut_name}: {val} (surity: {sur}%)")
            
            if r.notes:
                print(f"Notes: {r.notes}")
        
        print("\n" + "="*80)
        
        return records
    
    def get_high_surity_nutrients(self, min_surity: float = 70) -> Dict:
        """Get nutrients filtered by surity"""
        records = self.load()
        
        high_surity = {}
        for r in records:
            for n in r.nutrients:
                food_name = n.get("name", "?")
                if "nutrients" in n:
                    for nut_name, nut_data in n["nutrients"].items():
                        if nut_data.get("surity", 0) >= min_surity:
                            if food_name not in high_surity:
                                high_surity[food_name] = {}
                            high_surity[food_name][nut_name] = nut_data
        
        return high_surity


# Singleton
logger = EvalLogger()


async def log_pipeline_run(text: str, items: List[Dict], source: str = "ai_parsed"):
    """Log a single pipeline run with full nutrient surity"""
    
    # Extract items
    item_names = [item.get("name", "?") for item in items]
    quantities = [item.get("quantity", 1) for item in items]
    
    # Build nutrients with surity
    nutrients_list = []
    total_cal = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0
    
    for item in items:
        item_nutrients = {}
        
        # Macros
        for nut in ["calories", "protein", "carbohydrates", "fats", "fiber", "water", "sugar"]:
            val = item.get(nut, 0)
            sur = item.get(f"{nut}_surity", item.get("surity_percentage", 50))
            item_nutrients[nut] = {"value": val, "surity": sur}
            
            # Update totals
            if nut == "calories": total_cal += val
            elif nut == "protein": total_protein += val
            elif nut == "carbohydrates": total_carbs += val
            elif nut == "fats": total_fats += val
        
        # Vitamins (if provided)
        if "vitamins" in item:
            for vit, val in item["vitamins"].items():
                sur = item.get(f"vitamins_surity", {}).get(vit, 30)
                item_nutrients[vit] = {"value": val, "surity": sur}
        
        # Minerals (if provided)
        if "minerals" in item:
            for min, val in item["minerals"].items():
                sur = item.get(f"minerals_surity", {}).get(min, 30)
                item_nutrients[min] = {"value": val, "surity": sur}
        
        nutrients_list.append({
            "name": item.get("name", "?"),
            "grams": item.get("estimated_grams", 0),
            "quantity": item.get("quantity", 1),
            "nutrients": item_nutrients
        })
    
    # Create record
    record = EvalRecord(
        input_text=text,
        items_detected=item_names,
        quantities=quantities,
        nutrients=nutrients_list,
        total_calories=total_cal,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fats=total_fats,
        source=source
    )
    
    # Save
    logger.log(record)
    
    return record


def show_logs():
    """Show all logged records"""
    return logger.print_all()


def get_high_surity(min_surity: float = 70):
    """Show high surity nutrients"""
    return logger.get_high_surity_nutrients(min_surity)


if __name__ == "__main__":
    print("Current Pipeline Logs:")
    show_logs()
