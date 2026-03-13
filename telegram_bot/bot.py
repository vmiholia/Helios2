"""
Helios2 Telegram Bot
Interact with Helios2 via Telegram
"""
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx
from datetime import datetime

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
HELIOS2_API_URL = os.getenv("HELIOS2_API_URL", "http://localhost:8001")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Welcome to Helios2! 🥗\n\n"
        "I'm your health tracker bot.\n\n"
        "Just tell me what you ate, for example:\n"
        "\"at 9 am i ate apple and 3 egg omelette\"\n\n"
        "Commands:\n"
        "/today - Show today's nutrient summary\n"
        "/log - Log a food item\n"
        "/search - Search food database"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "Helios2 Help:\n\n"
        "📝 Just type what you ate!\n"
        "Example: \"had 2 eggs and toast for breakfast\"\n\n"
        "Commands:\n"
        "/today - View today's intake\n"
        "/search [food] - Search food database\n"
        "/clear - Clear today's log"
    )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's nutrient summary"""
    user_id = str(update.effective_user.id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HELIOS2_API_URL}/daily/{user_id}?date={today}")
            
            if response.status_code == 404:
                await update.message.reply_text("No food logged today yet! 🍽️")
                return
            
            data = response.json()
            
            summary = f"📊 Today's Summary ({today})\n\n"
            summary += f"🔥 Calories: {data.get('total_calories', 0):.0f} kcal\n"
            summary += f"🥩 Protein: {data.get('total_protein', 0):.1f}g\n"
            summary += f"🍞 Carbs: {data.get('total_carbohydrates', 0):.1f}g\n"
            summary += f"🥑 Fats: {data.get('total_fats', 0):.1f}g\n"
            summary += f"💧 Water: {data.get('total_water', 0):.0f}ml\n"
            summary += f"📈 Avg Surity: {data.get('average_surity', 0):.0f}%"
            
            await update.message.reply_text(summary)
            
    except Exception as e:
        await update.message.reply_text(f"Error fetching data: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming food log messages"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Send "typing" action
    await update.message.chat.send_action("typing")
    
    try:
        # Call the API to parse and log
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HELIOS2_API_URL}/parse_and_log/",
                json={"text": text, "user_id": user_id},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "not_implemented":
                    # LLM parsing not ready - use fallback
                    await update.message.reply_text(
                        "🤖 AI parsing is still being set up!\n\n"
                        "For now, please use the /search command to find foods, "
                        "then I'll guide you through logging them."
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Logged: {text}\n\n"
                        f"Calories: {data.get('calories', 0):.0f} kcal\n"
                        f"Surity: {data.get('surity_percentage', 0):.0f}%"
                    )
            else:
                await update.message.reply_text(f"Error: {response.text}")
                
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for food items"""
    if not context.args:
        await update.message.reply_text("Usage: /search [food name]")
        return
    
    query = " ".join(context.args)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HELIOS2_API_URL}/food/search/{query}")
            foods = response.json()
            
            if not foods:
                await update.message.reply_text(f"No foods found for '{query}'")
                return
            
            message = f"🔍 Search results for '{query}':\n\n"
            for food in foods[:10]:
                message += f"• {food['name']} - {food['calories']:.0f} kcal/100g (Surity: {food['surity_percentage']:.0f}%)\n"
            
            await update.message.reply_text(message)
            
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


def main():
    """Run the bot"""
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Please set TELEGRAM_BOT_TOKEN in your environment!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Helios2 Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
