"""
Helios2 Evals - Simple Pipeline Logging
Store: Text Input → Decomposition → Nutrients
For later review and improvement
"""
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict, field
import httpx


@dataclass
class EvalRecord:
    """Single pipeline record"""
    timestamp: str = ""
    input_text: str = ""
    
    # Decomposition
    items_detected: List[str] = field(default_factory=list)
    quantities: List[Any] = field(default_factory=list)
    
    # Stored nutrients (per item)
    nutrients: List[Dict] = field(default_factory=list)
    
    # Total for the input
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fats: float = 0.0
    
    # Metadata
    source: str = "fallback"  # fallback, llm, manual
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
        
        print("\n" + "="*70)
        print(f"HELIOS2 PIPELINE LOG - {len(records)} records")
        print("="*70)
        
        for i, r in enumerate(records, 1):
            print(f"\n--- Record {i} ---")
            print(f"Time: {r.timestamp}")
            print(f"Input: {r.input_text}")
            print(f"Items: {r.items_detected}")
            print(f"Quantities: {r.quantities}")
            print(f"Total: {r.total_calories:.0f}cal | P:{r.total_protein:.1f}g | C:{r.total_carbs:.1f}g | F:{r.total_fats:.1f}g")
            print(f"Source: {r.source}")
            if r.notes:
                print(f"Notes: {r.notes}")
            
            # Print per-item nutrients
            for j, n in enumerate(r.nutrients):
                print(f"  [{j+1}] {n.get('name', '?')}: {n.get('calories', 0)}cal")
        
        print("\n" + "="*70)
        
        return records


# Singleton
logger = EvalLogger()


async def log_pipeline_run(text: str, items: List[Dict], source: str = "fallback"):
    """Log a single pipeline run"""
    
    # Extract items
    item_names = [item.get("name", "?") for item in items]
    quantities = [item.get("quantity", 1) for item in items]
    
    # Extract nutrients
    nutrients = []
    total_cal = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0
    
    for item in items:
        cal = item.get("calories", 0)
        prot = item.get("protein", 0)
        carb = item.get("carbohydrates", 0)
        fat = item.get("fats", 0)
        
        nutrients.append({
            "name": item.get("name", "?"),
            "grams": item.get("estimated_grams", 0),
            "calories": cal,
            "protein": prot,
            "carbs": carb,
            "fats": fat,
            "surity": item.get("surity_percentage", 0)
        })
        
        total_cal += cal
        total_protein += prot
        total_carbs += carb
        total_fats += fat
    
    # Create record
    record = EvalRecord(
        input_text=text,
        items_detected=item_names,
        quantities=quantities,
        nutrients=nutrients,
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


if __name__ == "__main__":
    # Test
    print("Current Pipeline Logs:")
    show_logs()
