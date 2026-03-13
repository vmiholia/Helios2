"""
Helios2 LLM Service
Parses natural language food input using LLM
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
        """
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
                    return {"error": f"LLM API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def _system_prompt(self) -> str:
        return """You are a nutritional expert for Helios2 health tracking app.
        
TASK: Parse the user's food input and extract structured nutrient information.

OUTPUT FORMAT: Return valid JSON only, no other text.

For each food item, you must estimate nutrients per 100g and provide a SURITY PERCENTAGE:
- 90-100%: Exact known values (包装食品, verified databases)
- 70-89%: Good estimate based on similar foods
- 50-69%: Rough estimate, might vary
- Below 50%: Very uncertain, guess if needed

MACRONUTRIENTS (per 100g):
- calories (kcal)
- protein (g)
- carbohydrates (g) - include fiber, sugar breakdown
- fats (g) - include saturated, monounsaturated, polyunsaturated
- water (g)

MICRONUTRIENTS (per 100g) - estimate if not sure:
VITAMINS:
- vitamin_A (mcg)
- vitamin_D (mcg)  
- vitamin_E (mg)
- vitamin_K (mcg)
- vitamin_B1_thiamine (mg)
- vitamin_B2_riboflavin (mg)
- vitamin_B3_niacin (mg)
- vitamin_B5_pantothenic_acid (mg)
- vitamin_B6_pyridoxine (mg)
- vitamin_B7_biotin (mcg)
- vitamin_B9_folate (mcg)
- vitamin_B12_cobalamin (mcg)
- vitamin_C (mg)

MINERALS:
- calcium_Ca (mg)
- iron_Fe (mg)
- magnesium_Mg (mg)
- phosphorus_P (mg)
- potassium_K (mg)
- sodium_Na (mg)
- zinc_Zn (mg)
- selenium_Se (mcg)
- copper_Cu (mg)
- manganese_Mn (mg)

IMPORTANT: Always return valid JSON. If unsure about a value, estimate it but lower the surity percentage accordingly."""

    def _build_prompt(self, text: str) -> str:
        return f"""Parse this food input: "{text}"

Current date: {datetime.now().strftime('%Y-%m-%d')}
Current time: {datetime.now().strftime('%H:%M')}

Extract:
1. List of food items with quantities
2. Estimated time of consumption
3. All macronutrients and micronutrients per 100g for each item
4. Your confidence level (surity_percentage) for each item

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
    "water": number,
    "vitamins": {{...}},
    "minerals": {{...}}
}}

If multiple foods, return as JSON array."""

    def _parse_llm_response(self, content: str) -> dict:
        """Parse LLM response to extract JSON"""
        try:
            # Try to find JSON in response
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": content}


# Singleton instance
llm_parser = LLMParser()
