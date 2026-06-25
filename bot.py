import os
import json
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

with open("words.json", "r", encoding="utf-8") as f:
    data = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"HSK {i}", callback_data=f"quiz_hsk{i}")] for i in range(1, 2)]
    await update.message.reply_text("Darajani tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    level = query.data.split("_")[1] # 'hsk1'
    words = data.get(level, [])
    
    if len(words) < 4:
        await query.edit_message_text("Quiz uchun kamida 4 ta so'z kerak!")
        return

    # To'g'ri so'zni tanlash
    correct_word = random.choice(words)
    
    # 3 ta noto'g'ri variant tanlash
    options = [correct_word['translation']]
    while len(options) < 4:
        wrong = random.choice(words)['translation']
        if wrong not in options:
            options.append(wrong)
    
    random.shuffle(options) # Variantlarni aralashtirish
    
    # Tugmalarni yaratish
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct_word['translation']}")] for opt in options]
    
    await query.edit_message_text(
        f"So'z: {correct_word['word']}\n\nTarjimasini toping:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, user_ans, correct_ans = query.data.split("_")
    
    if user_ans == correct_ans:
        await query.answer("✅ To'g'ri!", show_alert=True)
    else:
        await query.answer(f"❌ Noto'g'ri! To'g'ri javob: {correct_ans}", show_alert=True)
    
    # Yangi savol berish uchun
    await quiz_handler(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(quiz_handler, pattern="^quiz_"))
    app.add_handler(CallbackQueryHandler(check_answer, pattern="^ans_"))
    app.run_polling()
