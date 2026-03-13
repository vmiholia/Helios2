"""
vClaw Telegram Bot - Helios2 Integration
Listens to vClaw Telegram bot messages and routes food input to Helios2
"""
import os
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
TELEGRAM_BOT_TOKEN = "8244118711:AAFf54dYH4VG0Z-Fb-sGjcpev7Pkyx8EvMc"
HELIOS2_API_URL = os.getenv("HELIOS2_API_URL", "http://localhost:8001")

# Keywords to trigger Helios2
FOOD_KEYWORDS = [
    "ate", "had", "eating", "ate", "eaten",
    "log", "track", "consumed", "breakfast", "lunch", "dinner",
    "food", "calories", "nutrients", "macros", "protein", "carbs", "fats"
]

SUMMARY_KEYWORDS = [
    "today", "summary", "today's", "nutrients", "macros", "calories"
]


def is_food_message(text: str) -> bool:
    """Check if message is food-related"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FOOD_KEYWORDS)


def is_summary_request(text: str) -> bool:
    """Check if user wants summary"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SUMMARY_KEYWORDS)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if not update.message or not update.message.text:
        return
    
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Skip commands
    if text.startswith('/'):
        return
    
    # Check if it's a food message
    if is_food_message(text):
        await update.message.chat.send_action("typing")
        
        # Call Helios2 API
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
                        await update.message.reply_text(
                            f"✅ Logged to Helios2!\n\n"
                            f"Items: {data.get('items_logged', 0)}\n"
                            f"Calories: {data.get('total_calories', 0):.0f} kcal\n"
                            f"Surity: {data.get('average_surity', 0):.0f}%"
                        )
                    else:
                        await update.message.reply_text(
                            f"⚠️ {data.get('message', 'Error logging food')}"
                        )
                else:
                    await update.message.reply_text(
                        f"❌ Helios2 API Error: {response.status_code}"
                    )
                    
        except httpx.ConnectError:
            await update.message.reply_text(
                "❌ Cannot connect to Helios2 API.\n"
                "Is the backend running? (Run: cd Helios2/backend && python -m uvicorn main:app)"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # Check if it's a summary request
    elif is_summary_request(text):
        await update.message.chat.send_action("typing")
        
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{HELIOS2_API_URL}/daily/{user_id}?date={today}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    await update.message.reply_text(
                        f"📊 Today's Summary ({today})\n\n"
                        f"🔥 Calories: {data.get('total_calories', 0):.0f} kcal\n"
                        f"🥩 Protein: {data.get('total_protein', 0):.1f}g\n"
                        f"🍞 Carbs: {data.get('total_carbohydrates', 0):.1f}g\n"
                        f"🥑 Fats: {data.get('total_fats', 0):.1f}g\n"
                        f"💧 Water: {data.get('total_water', 0):.0f}ml\n"
                        f"📈 Avg Surity: {data.get('average_surity', 0):.0f}%"
                    )
                else:
                    await update.message.reply_text("No food logged today! 🍽️")
                    
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    await update.message.reply_text(
        "🥗 Helios2 Connected!\n\n"
        "I can now track your food and nutrients.\n\n"
        "Just tell me what you ate, for example:\n"
        "\"at 9 am i ate apple and 3 egg omelette\"\n\n"
        "Or ask for today's summary:\n"
        "\"how many calories today?\""
    )


def main():
    """Run the bot"""
    print("🤖 vClaw Helios2 Integration starting...")
    print(f"Helios2 API: {HELIOS2_API_URL}")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("👂 Listening for food messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
