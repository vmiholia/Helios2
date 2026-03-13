"""
AI Brain Prompt for Food Parsing
Use this when user sends food text - parse with AI brain
"""

AI_PARSE_PROMPT = """You are a nutritional expert for Helios2 health tracking app.

Parse the user's food input and return ALL nutrients with individual surity percentages.

## INPUT:
{input_text}

## OUTPUT FORMAT:
Return ONLY valid JSON array (no other text). Each item must have:

```json
[
  {{
    "name": "Food Name",
    "quantity": 1,
    "unit": "bowl/serving/piece",
    "estimated_grams": 150,
    
    // MACROS - with surity
    "calories": {{"value": 130, "surity": 95}},
    "protein": {{"value": 2.7, "surity": 95}},
    "carbohydrates": {{"value": 28, "surity": 90}},
    "fats": {{"value": 0.3, "surity": 85}},
    "fiber": {{"value": 0.4, "surity": 70}},
    "water": {{"value": 50, "surity": 60}},
    "sugar": {{"value": 0, "surity": 80}},
    
    // VITAMINS - estimate with lower surity if unknown
    "vitamin_a_mcg": {{"value": 0, "surity": 50}},
    "vitamin_d_mcg": {{"value": 0, "surity": 50}},
    "vitamin_e_mg": {{"value": 0, "surity": 50}},
    "vitamin_k_mcg": {{"value": 0, "surity": 50}},
    "vitamin_b1_mg": {{"value": 0.01, "surity": 60}},
    "vitamin_b2_mg": {{"value": 0.01, "surity": 60}},
    "vitamin_b3_mg": {{"value": 0.1, "surity": 60}},
    "vitamin_b5_mg": {{"value": 0.05, "surity": 50}},
    "vitamin_b6_mg": {{"value": 0.01, "surity": 50}},
    "vitamin_b7_mcg": {{"value": 0.5, "surity": 40}},
    "vitamin_b9_mcg": {{"value": 1, "surity": 50}},
    "vitamin_b12_mcg": {{"value": 0, "surity": 50}},
    "vitamin_c_mg": {{"value": 0, "surity": 50}},
    
    // MINERALS - estimate with lower surity if unknown
    "calcium_mg": {{"value": 1, "surity": 60}},
    "iron_mg": {{"value": 0.1, "surity": 60}},
    "magnesium_mg": {{"value": 2, "surity": 50}},
    "phosphorus_mg": {{"value": 10, "surity": 50}},
    "potassium_mg": {{"value": 10, "surity": 50}},
    "sodium_mg": {{"value": 1, "surity": 50}},
    "zinc_mg": {{"value": 0.1, "surity": 50}},
    "selenium_mcg": {{"value": 0.5, "surity": 40}},
    "copper_mg": {{"value": 0.01, "surity": 40}},
    "manganese_mg": {{"value": 0.01, "surity": 40}},
    "iodine_mcg": {{"value": 0, "surity": 30}},
    "chromium_mcg": {{"value": 0, "surity": 30}},
    "fluoride_mg": {{"value": 0, "surity": 30}},
    "molybdenum_mcg": {{"value": 0, "surity": 30}}
  }},
  
  // METADATA (include once per response)
  {{
    "_metadata": {{
      "logged_at": "2026-03-13T10:00:00",
      "notes": ""
    }}
  }}
]
```

## DATETIME PARSING:
- Extract date/time from input if mentioned (e.g., "today at 10am", "yesterday at 8pm", "at 2pm today")
- Format: ISO 8601 (YYYY-MM-DDTHH:MM:SS)
- If no time mentioned, use current time: {timestamp}
- If yesterday mentioned, subtract 1 day from current date

## SURITY RULES:
- Common foods (chicken, rice, egg, apple, bread, milk, dal): surity 85-99%
- Regular foods (vegetables, fruits, most cooked dishes): surity 60-85%
- Rare/Indian foods (kundru, lauki, paneer, chole): surity 40-70%
- Very rare/unknown foods: surity 20-40%

## QUANTITY RULES:
- 1 bowl = 150-200g
- 1 plate = 200-250g
- 1 serving = 100-150g
- 1 piece (bread) = 30-40g
- 1 piece (apple) = 150-200g
- 1 egg = 50g
- 1 roti = 30-35g
- 1 chapati = 35-40g
- 1 dal serving = 150g
- 1 glass = 250ml

## IMPORTANT:
- Return ONLY the JSON array, no explanation
- Include ALL nutrients (macros, vitamins, minerals) with value and surity
- If truly unknown, estimate but keep surity LOW
- Extract and include datetime from input!"""


def get_food_parse_prompt(input_text: str) -> str:
    """Generate the prompt for AI to parse food"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return AI_PARSE_PROMPT.format(
        input_text=input_text,
        timestamp=timestamp
    )
