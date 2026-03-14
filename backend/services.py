"""
Helios2 LLM Service
Uses MiniMax for natural language parsing - with SQLite database caching
"""
import os
import json
import httpx
import sqlite3
from datetime import datetime
from pathlib import Path


class LLMParser:
    """Parse food input using MiniMax LLM with database caching"""
    
    def __init__(self):
        # MiniMax configuration
        self.api_key = os.getenv("MINIMAX_API_KEY", "your_minimax_key_here")
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "MiniMax-M2.5"
        
        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), "helios2.db")
        
        # Ensure database exists
        self._ensure_database()
        
        print(f"📦 Food cache initialized from: {self.db_path}")
    
    def _ensure_database(self):
        """Ensure the database has the food_items table"""
        if not os.path.exists(self.db_path):
            print("⚠️ Database not found!")
            return
        
        # Check if food_items table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='food_items'
        """)
        
        if not cursor.fetchone():
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS food_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    surity_percentage REAL DEFAULT 0,
                    default_serving_grams REAL DEFAULT 100,
                    serving_unit TEXT DEFAULT 'g',
                    calories REAL DEFAULT 0,
                    protein REAL DEFAULT 0,
                    carbohydrates REAL DEFAULT 0,
                    fats REAL DEFAULT 0,
                    fiber REAL DEFAULT 0,
                    water REAL DEFAULT 0,
                    sugar REAL DEFAULT 0,
                    nutrients_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        
        conn.close()
    
    def _get_food_from_db(self, food_name: str) -> dict:
        """Get food item from SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search by name (partial match)
        cursor.execute("""
            SELECT * FROM food_items 
            WHERE LOWER(name) LIKE LOWER(?)
        """, (f"%{food_name}%",))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def _get_all_foods_from_db(self) -> dict:
        """Get all foods from database for matching"""
        foods = {}
        
        if not os.path.exists(self.db_path):
            return foods
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM food_items")
            rows = cursor.fetchall()
            
            for row in rows:
                food = dict(row)
                name = food.get("name", "").lower()
                foods[name] = food
        except:
            pass
        
        conn.close()
        return foods
    
    def _save_food_to_db(self, food_data: dict):
        """Save new food to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("SELECT id FROM food_items WHERE LOWER(name) = LOWER(?)", 
                         (food_data.get("name", ""),))
            
            if not cursor.fetchone():
                # Insert new food
                nutrients_json = json.dumps(food_data.get("nutrients", {}))
                
                cursor.execute("""
                    INSERT INTO food_items (
                        name, surity_percentage, default_serving_grams, serving_unit,
                        calories, protein, carbohydrates, fats, fiber, water, sugar,
                        nutrients_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    food_data.get("name", ""),
                    food_data.get("surity_percentage", 50),
                    food_data.get("estimated_grams", 100),
                    food_data.get("unit", "g"),
                    food_data.get("calories", 0),
                    food_data.get("protein", 0),
                    food_data.get("carbohydrates", 0),
                    food_data.get("fats", 0),
                    food_data.get("fiber", 0),
                    food_data.get("water", 0),
                    food_data.get("sugar", 0),
                    nutrients_json
                ))
                
                conn.commit()
                print(f"✅ Saved to DB: {food_data.get('name')}")
        
        except Exception as e:
            print(f"❌ Error saving to DB: {e}")
        
        conn.close()
    
    async def parse_food_text(self, text: str, user_id: str) -> list:
        """
        Parse natural language food input using AI
        Always uses AI to parse the input
        """
        
        print(f"🤖 Calling AI to parse: {text}")
        
        # Call AI to parse
        ai_items = await self._call_ai_brain(text, user_id)
        
        # Save new foods to database for future use
        for item in ai_items:
            self._save_food_to_db(item)
        
        return ai_items
    
    def _extract_food_names(self, text: str) -> list:
        """Extract food names from input text"""
        text_lower = text.lower()
        
        # Common patterns
        patterns = {
            "omelette": "omelette",
            "eggs": "omelette",
            "egg": "omelette",
            "bread": "sourdough bread",
            "toast": "sourdough bread",
            "rice": "jasmine rice",
            "jasmine rice": "jasmine rice",
            "green curry": "thai green curry",
            "curry": "thai green curry",
            "chicken": "chicken",
            "apple": "apple",
            "dal": "dal",
            "roti": "roti",
        }
        
        found = []
        for pattern, food_name in patterns.items():
            if pattern in text_lower and food_name not in found:
                found.append(food_name)
        
        return found if found else ["unknown food"]
    
    async def _call_ai_brain(self, text: str, user_id: str) -> list:
        """Call AI brain for parsing"""
        
        if not self.api_key or self.api_key == "your_minimax_key_here":
            return self._fallback_parse(text)
        
        prompt = self._build_prompt(text)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self._system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    parsed = self._parse_llm_response(content)
                    
                    for item in parsed:
                        item["source"] = "ai_parsed"
                    
                    return parsed
                else:
                    return self._fallback_parse(text)
                    
        except Exception as e:
            print(f"❌ AI call failed: {e}")
            return self._fallback_parse(text)
    
    def _system_prompt(self) -> str:
        return """You are a nutritional expert for Helios2.

Parse food input and return ALL nutrients with surity.

MACROS: calories, protein, carbohydrates, fats, fiber, water, sugar
VITAMINS: vitamin_a_mcg, vitamin_d_mcg, vitamin_e_mg, vitamin_k_mcg, vitamin_b1_mg, vitamin_b2_mg, vitamin_b3_mg, vitamin_b5_mg, vitamin_b6_mg, vitamin_b7_mcg, vitamin_b9_mcg, vitamin_b12_mcg, vitamin_c_mg
MINERALS: calcium_mg, iron_mg, magnesium_mg, phosphorus_mg, potassium_mg, sodium_mg, zinc_mg, selenium_mcg, copper_mg, manganese_mg

Return JSON array with {value, surity} for each nutrient."""

    def _build_prompt(self, text: str) -> str:
        return f"""Parse: "{text}"

Return JSON array with ALL nutrients (value + surity) for each food."""

    def _parse_llm_response(self, content: str) -> list:
        try:
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed = json.loads(content)
            
            if isinstance(parsed, dict):
                return [parsed]
            return parsed
            
        except Exception as e:
            return self._fallback_parse(content)
    
    def _fallback_parse(self, text: str) -> list:
        """Fallback: Keyword-based estimation"""
        text_lower = text.lower()
        
        food_database = {
            "rice": {"name": "Cooked Jasmine Rice", "calories": 130, "protein": 2.7, "carbs": 28, "fats": 0.3, "fiber": 0.4, "sugar": 0, "serving": 150},
            "curry": {"name": "Thai Green Curry", "calories": 150, "protein": 10, "carbs": 8, "fats": 10, "fiber": 1, "sugar": 2, "serving": 200},
            "chicken": {"name": "Chicken", "calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "fiber": 0, "sugar": 0, "serving": 100},
            "egg": {"name": "Egg", "calories": 155, "protein": 13, "carbs": 1.1, "fats": 11, "fiber": 0, "sugar": 1.1, "serving": 50},
            "apple": {"name": "Apple", "calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2, "fiber": 2.4, "sugar": 10, "serving": 180},
            "bread": {"name": "Bread", "calories": 265, "protein": 9, "carbs": 49, "fats": 3.2, "fiber": 2.7, "sugar": 5, "serving": 30},
            "omelette": {"name": "Omelette", "calories": 154, "protein": 11, "carbs": 0.8, "fats": 12, "fiber": 0, "sugar": 0, "serving": 100},
        }
        
        quantity_map = {"1 bowl": 1, "2 bowl": 2, "3 bowl": 3, "1": 1, "2": 2, "3": 3}
        
        detected_quantity = 1
        for qty_word, qty_val in quantity_map.items():
            if qty_word in text_lower:
                detected_quantity = qty_val
                break
        
        items = []
        for keyword, food_data in food_database.items():
            if keyword in text_lower:
                serving = food_data["serving"]
                multiplier = detected_quantity
                
                items.append({
                    "name": food_data["name"],
                    "quantity": detected_quantity,
                    "unit": "serving",
                    "estimated_grams": serving * multiplier,
                    "surity_percentage": 40,
                    "calories": food_data["calories"] * multiplier,
                    "protein": food_data["protein"] * multiplier,
                    "carbohydrates": food_data["carbs"] * multiplier,
                    "fats": food_data["fats"] * multiplier,
                    "fiber": food_data.get("fiber", 0) * multiplier,
                    "sugar": food_data.get("sugar", 0) * multiplier,
                    "source": "fallback"
                })
        
        if not items:
            items.append({
                "name": "Mixed Meal",
                "quantity": 1,
                "unit": "serving",
                "estimated_grams": 300,
                "surity_percentage": 20,
                "calories": 400,
                "protein": 20,
                "carbohydrates": 40,
                "fats": 15,
                "source": "fallback"
            })
        
        return items


# Singleton instance
llm_parser = LLMParser()
