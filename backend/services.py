"""
Helios2 LLM Service
Uses MiniMax for natural language parsing
"""
import os
import json
import httpx
from datetime import datetime


class LLMParser:
    """Parse food input using MiniMax LLM"""
    
    def __init__(self):
        # MiniMax configuration
        self.api_key = os.getenv("MINIMAX_API_KEY", "your_minimax_key_here")
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "MiniMax-M2.5"
    
    async def parse_food_text(self, text: str, user_id: str) -> dict:
        """
        Parse natural language food input using MiniMax
        Falls back to keyword matching if API fails
        """
        
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
                    
                    # If successful, mark as LLM source
                    for item in parsed:
                        item["source"] = "llm"
                    
                    return parsed
                else:
                    # Fallback on error
                    return self._fallback_parse(text)
                    
        except Exception as e:
            # Fallback on exception
            return self._fallback_parse(text)
    
    def _system_prompt(self) -> str:
        return """You are a nutritional expert for Helios2 health tracking app.
        
TASK: Parse the user's food input and extract structured nutrient information.

OUTPUT FORMAT: Return valid JSON array only, no other text.

For each food item, provide:
- name: food name
- quantity: number
- unit: g/piece/serving
- estimated_grams: total weight in grams
- surity_percentage: 0-100 (how confident you are)
- calories, protein, carbohydrates, fats, fiber, sugar (per 100g)

IMPORTANT: Return ONLY valid JSON array like:
[{"name": "Rice", "quantity": 1, "unit": "bowl", "estimated_grams": 150, "surity_percentage": 80, "calories": 130, "protein": 2.7, "carbohydrates": 28, "fats": 0.3, "fiber": 0.4, "sugar": 0}]"""

    def _build_prompt(self, text: str) -> str:
        return f"""Parse this food input and return nutrients per 100g:

Input: "{text}"

Current time: {datetime.now().strftime('%H:%M')}

Return a JSON array of food items with all nutrient values per 100g."""

    def _parse_llm_response(self, content: str) -> list:
        """Parse LLM response to extract JSON"""
        try:
            content = content.strip()
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed = json.loads(content)
            
            # Ensure it's a list
            if isinstance(parsed, dict):
                return [parsed]
            return parsed
            
        except Exception as e:
            # Return fallback on parse error
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
