"""
Helios2 LLM Service
Parses natural language food input using LLM - with fallback
"""
import os
import json
import httpx
from datetime import datetime


class LLMParser:
    """Parse food input using LLM"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
    
    async def parse_food_text(self, text: str, user_id: str) -> dict:
        """
        Parse natural language food input and return structured data
        If no API key, use fallback estimation
        """
        
        if not self.api_key or self.api_key == "your_api_key_here":
            # Use fallback estimation
            return self._fallback_parse(text)
        
        prompt = self._build_prompt(text)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
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
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return self._parse_llm_response(content)
                else:
                    # Fallback on error
                    return self._fallback_parse(text)
                    
        except Exception as e:
            # Fallback on exception
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> list:
        """Fallback: Estimate nutrients from text without LLM"""
        text_lower = text.lower()
        
        # Simple keyword-based estimation
        items = []
        
        # Detect food items
        food_database = {
            "rice": {"name": "Cooked Jasmine Rice", "calories": 130, "protein": 2.7, "carbs": 28, "fats": 0.3, "fiber": 0.4, "sugar": 0, "serving": 150},
            "curry": {"name": "Thai Green Curry", "calories": 150, "protein": 10, "carbs": 8, "fats": 10, "fiber": 1, "sugar": 2, "serving": 200},
            "chicken": {"name": "Chicken", "calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "fiber": 0, "sugar": 0, "serving": 100},
            "egg": {"name": "Egg", "calories": 155, "protein": 13, "carbs": 1.1, "fats": 11, "fiber": 0, "sugar": 1.1, "serving": 50},
            "apple": {"name": "Apple", "calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2, "fiber": 2.4, "sugar": 10, "serving": 180},
            "bread": {"name": "Bread", "calories": 265, "protein": 9, "carbs": 49, "fats": 3.2, "fiber": 2.7, "sugar": 5, "serving": 30},
            "omelette": {"name": "Omelette", "calories": 154, "protein": 11, "carbs": 0.8, "fats": 12, "serving": 100},
        }
        
        # Simple quantity detection
        quantity_map = {
            "1 bowl": 1, "2 bowl": 2, "3 bowl": 3,
            "1 plate": 1, "2 plate": 2,
            "1 piece": 1, "2 piece": 2,
            "1": 1, "2": 2, "3": 3
        }
        
        # Detect mentioned foods
        detected_quantity = 1
        for qty_word, qty_val in quantity_map.items():
            if qty_word in text_lower:
                detected_quantity = qty_val
                break
        
        # Find matching foods
        for keyword, food_data in food_database.items():
            if keyword in text_lower:
                serving = food_data["serving"]
                multiplier = detected_quantity
                
                items.append({
                    "name": food_data["name"],
                    "quantity": detected_quantity,
                    "unit": "serving",
                    "estimated_grams": serving * multiplier,
                    "surity_percentage": 40,  # Low surity for fallback
                    "calories": food_data["calories"] * multiplier,
                    "protein": food_data["protein"] * multiplier,
                    "carbohydrates": food_data["carbs"] * multiplier,
                    "fats": food_data["fats"] * multiplier,
                    "fiber": food_data["fiber"] * multiplier,
                    "sugar": food_data["sugar"] * multiplier,
                    "water": 0,
                    "saturated_fat": food_data["fats"] * 0.4 * multiplier,
                    "monounsaturated_fat": food_data["fats"] * 0.3 * multiplier,
                    "polyunsaturated_fat": food_data["fats"] * 0.3 * multiplier,
                })
        
        if not items:
            # Default item if nothing detected
            items.append({
                "name": "Mixed Meal",
                "quantity": 1,
                "unit": "serving",
                "estimated_grams": 300,
                "surity_percentage": 20,
                "calories": 400,
                "protein": 20,
                "carbs": 40,
                "fats": 15,
                "fiber": 2,
                "sugar": 3,
                "water": 0,
                "saturated_fat": 5,
                "monounsaturated_fat": 5,
                "polyunsaturated_fat": 5,
            })
        
        return items
    
    def _system_prompt(self) -> str:
        return """You are a nutritional expert for Helios2 health tracking app.
        
TASK: Parse the user's food input and extract structured nutrient information.

OUTPUT FORMAT: Return valid JSON only, no other text.

For each food item, you must estimate nutrients per 100g and provide a SURITY PERCENTAGE:
- 90-100%: Exact known values (packaged foods, verified databases)
- 70-89%: Good estimate based on similar foods
- 50-69%: Rough estimate, might vary
- Below 50%: Very uncertain, guess if needed

MACRONUTRIENTS (per 100g):
- calories (kcal)
- protein (g)
- carbohydrates (g) - include fiber, sugar breakdown
- fats (g) - include saturated, monounsaturated, polyunsaturated
- water (g)

IMPORTANT: Always return valid JSON as an array of items."""

    def _build_prompt(self, text: str) -> str:
        return f"""Parse this food input: "{text}"

Return as JSON array with this structure for each item:
{{
    "name": "food name",
    "quantity": number,
    "unit": "g/piece/serving",
    "estimated_grams": number,
    "surity_percentage": 0-100,
    "calories": number,
    "protein": number,
    "carbohydrates": number,
    "fiber": number,
    "sugar": number,
    "fats": number,
    "saturated_fat": number,
    "monounsaturated_fat": number,
    "polyunsaturated_fat": number,
    "water": number
}}"""

    def _parse_llm_response(self, content: str) -> dict:
        """Parse LLM response to extract JSON"""
        try:
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
        except json.JSONDecodeError:
            return [{"error": "Failed to parse LLM response", "raw": content}]


# Singleton instance
llm_parser = LLMParser()
