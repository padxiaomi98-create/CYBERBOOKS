import os, json, random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# JSON faylni har safar o'qib olish (yangi so'z qo'shilganda botni o'chirmaslik uchun)
def load_data():
    with open("words.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 1. Asosiy Reply Menyu
def get_reply_menu():
    return ReplyKeyboardMarkup([["📚 Quizni boshlash", "📊 Natijalar"]], resize_keyboard=True)

# 2. HSK 1-9 uchun Inline Menyu (3x3 grid)
def get_level_menu():
    data = load_data()
    levels = ["hsk1", "hsk2", "hsk3", "hsk4", "hsk5", "hsk6", "hsk7", "hsk8", "hsk9"]
    keyboard = []
    row = []
    
    for i, level in enumerate(levels):
        # Tugma ustiga daraja nomi va ichida nechta so'z borligini yozish (ixtiyoriy)
        count = len(data.get(level, []))
        button = InlineKeyboardButton(f"{level.upper()} ({count})", callback_data=f"start_{level}")
        row.append(button)
        
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! HSK 3.0 Quiz botiga xush kelibsiz.", reply_markup=get_reply_menu())

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📚 Quizni boshlash":
        await update.message.reply_text("Darajani tanlang:", reply_markup=get_level_menu())
    elif update.message.text == "📊 Natijalar":
        await update.message.reply_text(f"🏆 Oxirgi natijangiz: {context.user_data.get('score', 0)} ball.")

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    
    if query.data.startswith("start_"):
        context.user_data['score'] = 0
        level = query.data.split("_")[1]
    else:
        level = context.user_data.get('current_level', 'hsk1')

    context.user_data['current_level'] = level
    words = data.get(level, [])
    
    if len(words) < 4:
        await query.edit_message_text(f"{level.upper()} darajasida quiz uchun kamida 4 ta so'z bo'lishi kerak!")
        return

    correct = random.choice(words)
    # 3 ta noto'g'ri variantni bazadan tanlash
    others = random.sample([w['translation'] for w in words if w['translation'] != correct['translation']], 3)
    options = others + [correct['translation']]
    random.shuffle(options)
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct['translation']}_{level}")] for opt in options]
    await query.edit_message_text(f"🀄️ So'z: {correct['word']}\n\nTarjimasini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_parts = query.data.split("_")
    user_ans, correct_ans, level = data_parts[1], data_parts[2], data_parts[3]
    
    if user_ans == correct_ans:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        status = "✅ To'g'ri!"
    else:
        status = f"❌ Noto'g'ri! To'g'risi: {correct_ans}"
    
    keyboard = [[InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"next_{level}")]]
    await query.edit_message_text(f"{status}\n\n🏆 Ball: {context.user_data.get('score', 0)}", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(CallbackQueryHandler(quiz_handler, pattern="^(start|next)_"))
    app.add_handler(CallbackQueryHandler(check_answer, pattern="^ans_"))
    app.run_polling()
