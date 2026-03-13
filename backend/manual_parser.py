"""
Manual Food Parser using AI Brain
Use this when user sends food text - parse with AI brain
"""

FOOD_PARSE_PROMPT = """You are a nutritional expert for Helios2 health tracker.

Parse this food input and return JSON array with nutrients per 100g:

Input: "{input_text}"

Current date: {date}

Return ONLY valid JSON array like:
[{{"name": "Food Name", "quantity": 1, "unit": "bowl/piece/serving", "estimated_grams": 150, "surity_percentage": 85, "calories": 130, "protein": 2.7, "carbohydrates": 28, "fats": 0.3, "fiber": 0.4, "sugar": 0, "water": 0}}]

Rules:
- Estimate portion sizes based on common knowledge (1 bowl = 150-200g, 1 piece = 50-100g, 1 egg = 50g)
- surity_percentage: 90-100 if exact match, 70-89 if good estimate, below 70 if uncertain
- Include fiber, sugar, water where applicable
- If multiple foods, return array with all items"""


def parse_food_with_ai(input_text: str) -> str:
    """Return the prompt for AI to parse food"""
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = FOOD_PARSE_PROMPT.format(
        input_text=input_text,
        date=date
    )
    
    return prompt
