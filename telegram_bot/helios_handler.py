"""
Helios2 Telegram Bot (vClaw Integration)
Uses existing vClaw bot to interact with Helios2
"""
import os
import asyncio
import httpx
from datetime import datetime

# Use existing vClaw bot token
TELEGRAM_BOT_TOKEN = "8244118711:AAFf54dYH4VG0Z-Fb-sGjcpev7Pkyx8EvMc"
HELIOS2_API_URL = os.getenv("HELIOS2_API_URL", "http://localhost:8001")


async def handle_food_log(user_id: str, text: str) -> str:
    """Handle food logging via Helios2 API"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HELIOS2_API_URL}/parse_and_log/",
                json={"text": text, "user_id": user_id},
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    return (
                        f"✅ Logged!\n\n"
                        f"Items: {data.get('items_logged', 0)}\n"
                        f"Calories: {data.get('total_calories', 0):.0f} kcal\n"
                        f"Surity: {data.get('average_surity', 0):.0f}%"
                    )
                else:
                    return f"Error: {data.get('message', 'Unknown error')}"
            else:
                return f"API Error: {response.status_code}"
                
    except Exception as e:
        return f"Error: {str(e)}"


async def handle_today_summary(user_id: str) -> str:
    """Get today's nutrient summary"""
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HELIOS2_API_URL}/daily/{user_id}?date={today}")
            data = response.json()
            
            if response.status_code == 404 or data.get("total_calories", 0) == 0:
                return "No food logged today yet! 🍽️\n\nTell me what you ate!"
            
            return (
                f"📊 Today's Summary ({today})\n\n"
                f"🔥 Calories: {data.get('total_calories', 0):.0f} kcal\n"
                f"🥩 Protein: {data.get('total_protein', 0):.1f}g\n"
                f"🍞 Carbs: {data.get('total_carbohydrates', 0):.1f}g\n"
                f"🥑 Fats: {data.get('total_fats', 0):.1f}g\n"
                f"💧 Water: {data.get('total_water', 0):.0f}ml\n"
                f"📈 Avg Surity: {data.get('average_surity', 0):.0f}%"
            )
            
    except Exception as e:
        return f"Error: {str(e)}"


# This file is meant to be imported by the main vClaw bot
# Or run as a standalone webhook handler
if __name__ == "__main__":
    print("Helios2 Bot Module loaded!")
    print(f"API URL: {HELIOS2_API_URL}")
