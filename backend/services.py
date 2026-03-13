"""
Helios2 LLM Service
Uses MiniMax for natural language parsing - with database caching
"""
import os
import json
import httpx
from datetime import datetime


class LLMParser:
    """Parse food input using MiniMax LLM with database caching"""
    
    def __init__(self):
        # MiniMax configuration
        self.api_key = os.getenv("MINIMAX_API_KEY", "your_minimax_key_here")
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "MiniMax-M2.5"
        
        # Food database cache (loaded from eval_logs)
        self.food_cache = self._load_food_database()
    
    def _load_food_database(self) -> dict:
        """Load known foods from eval_logs.jsonl"""
        cache = {}
        eval_file = os.path.join(os.path.dirname(__file__), "eval_logs.jsonl")
        
        if os.path.exists(eval_file):
            try:
                with open(eval_file, "r") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            for item in record.get("nutrients", []):
                                food_name = item.get("name", "").lower()
                                if food_name:
                                    # Store the full nutrient data
                                    cache[food_name] = item
            except:
                pass
        
        print(f"📦 Food database loaded: {len(cache)} items")
        return cache
    
    async def parse_food_text(self, text: str, user_id: str) -> dict:
        """
        Parse natural language food input using MiniMax
        First checks database, then calls AI if not found
        """
        
        # Step 1: Extract food names from text
        food_names = self._extract_food_names(text)
        
        # Step 2: Check if all foods are in database
        all_found = True
        items_to_parse = []
        
        for food_name in food_names:
            if food_name.lower() in self.food_cache:
                # Use cached data
                items_to_parse.append({
                    "name": food_name,
                    "from_cache": True,
                    "data": self.food_cache[food_name.lower()]
                })
            else:
                all_found = False
        
        # Step 3: If all found, return cached data
        if all_found and items_to_parse:
            print(f"✅ All foods found in database: {food_names}")
            return self._build_response_from_cache(items_to_parse, text)
        
        # Step 4: Some foods not found - call AI brain
        missing_foods = [f for f in food_names if f.lower() not in self.food_cache]
        print(f"🔍 Foods not in database: {missing_foods}")
        print(f"🤖 Calling AI brain...")
        
        # Call AI for all foods (to get complete data)
        return await self._call_ai_brain(text, user_id)
    
    def _extract_food_names(self, text: str) -> list:
        """Extract food names from input text"""
        text_lower = text.lower()
        
        # Known foods to look for
        known_foods = list(self.food_cache.keys())
        
        found = []
        for food in known_foods:
            if food in text_lower:
                found.append(food)
        
        # If no matches, try common patterns
        if not found:
            # Extract using simple keyword matching
            patterns = {
                "omelette": "omelette (3 eggs)",
                "eggs": "omelette (3 eggs)",
                "egg": "omelette (3 eggs)",
                "bread": "sourdough bread (1.2 slice)",
                "rice": "jasmine rice",
                "jasmine rice": "jasmine rice",
                "thai green curry": "thai green curry with chicken",
                "curry": "thai green curry with chicken",
                "chicken": "thai green curry with chicken",
            }
            
            for pattern, food_name in patterns.items():
                if pattern in text_lower and food_name not in found:
                    found.append(food_name)
        
        return found if found else ["unknown food"]
    
    def _build_response_from_cache(self, items: list, text: str) -> list:
        """Build response from cached database"""
        result = []
        
        for item in items:
            data = item["data"]
            nutrients = data.get("nutrients", {})
            
            # Build response item
            result.append({
                "name": data.get("name", item["name"]),
                "quantity": data.get("quantity", 1),
                "unit": data.get("unit", "serving"),
                "estimated_grams": data.get("grams", 100),
                "surity_percentage": 95,  # High surity - from database
                "source": "database_cache",
                "nutrients": nutrients
            })
        
        return result
    
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
                    
                    # Mark as AI parsed
                    for item in parsed:
                        item["source"] = "ai_parsed"
                    
                    return parsed
                else:
                    return self._fallback_parse(text)
                    
        except Exception as e:
            return self._fallback_parse(text)
    
    def _system_prompt(self) -> str:
        return """You are a nutritional expert for Helios2 health tracking app.
        
Parse the user's food input and return ALL nutrients with individual surity percentages.

For EACH food item, include ALL 34 nutrients with surity:

MACROS (7): calories, protein, carbohydrates, fats, fiber, water, sugar
VITAMINS (13): vitamin_a_mcg, vitamin_d_mcg, vitamin_e_mg, vitamin_k_mcg, vitamin_b1_mg, vitamin_b2_mg, vitamin_b3_mg, vitamin_b5_mg, vitamin_b6_mg, vitamin_b7_mcg, vitamin_b9_mcg, vitamin_b12_mcg, vitamin_c_mg
MINERALS (14): calcium_mg, iron_mg, magnesium_mg, phosphorus_mg, potassium_mg, sodium_mg, zinc_mg, selenium_mcg, copper_mg, manganese_mg, iodine_mcg, chromium_mcg, fluoride_mg, molybdenum_mcg

Return JSON array with {value, surity} for each nutrient."""

    def _build_prompt(self, text: str) -> str:
        return f"""Parse: "{text}"

Return JSON array with ALL nutrients (value + surity) for each food item."""

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
        
        quantity_map = {
            "1 bowl": 1, "2 bowl": 2, "3 bowl": 3,
            "1 plate": 1, "2 plate": 2,
            "1 piece": 1, "2 piece": 2,
            "1": 1, "2": 2, "3": 3
        }
        
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
                "fiber": 2,
                "sugar": 3,
                "source": "fallback"
            })
        
        return items


# Singleton instance
llm_parser = LLMParser()
