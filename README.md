# Helios2
Telegram-based health tracker with detailed macro & micro nutrient tracking.

## Project Structure
- `/backend` - FastAPI backend for food logging and nutrient calculation
- `/telegram_bot` - Telegram bot interface

## Setup
1. Install dependencies: `pip install -r backend/requirements.txt`
2. Configure `.env` files
3. Run the backend: `python -m uvicorn backend.main:app --reload`
4. Run the telegram bot: `python -m telegram_bot.bot`

## Features
- Natural language food input (e.g., "at 9 am i ate apple and 3 egg omlette")
- Detailed macro & micro nutrient tracking
- Surity percentage for nutrient confidence
- Telegram bot interface
