import os
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

with open("words.json", "r", encoding="utf-8") as f:
    data = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("HSK 1 so'zlarini boshlash", callback_data='hsk1')]]
    await update.message.reply_text("HSK 3.0 botiga xush kelibsiz!", reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    word = data['hsk1'][0]
    await query.edit_message_text(f"So'z: {word['word']}\nPinyin: {word['pinyin']}\nTarjimasi: {word['translation']}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(quiz))
    app.run_polling()
