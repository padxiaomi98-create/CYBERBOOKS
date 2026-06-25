import os, json, random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Tokenni yuklash
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# JSON bazani yuklash
with open("words.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Menyular
def get_reply_menu():
    return ReplyKeyboardMarkup([["📚 Quizni boshlash", "📊 Natijalar"]], resize_keyboard=True)

def get_level_menu():
    levels = ["hsk1", "hsk2", "hsk3", "hsk4", "hsk5", "hsk6", "hsk7", "hsk8", "hsk9"]
    keyboard = [
        [InlineKeyboardButton(l.upper(), callback_data=f"start_{l}")] 
        for l in levels
    ]
    # 3x3 formatda tugmalar
    chunks = [keyboard[i:i+3] for i in range(0, len(keyboard), 3)]
    return InlineKeyboardMarkup(chunks)

# Handlerlar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("HSK 3.0 botiga xush kelibsiz!", reply_markup=get_reply_menu())

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📚 Quizni boshlash":
        await update.message.reply_text("Darajani tanlang:", reply_markup=get_level_menu())
    elif update.message.text == "📊 Natijalar":
        await update.message.reply_text(f"Sizning joriy ballingiz: {context.user_data.get('score', 0)}")

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("start_"):
        context.user_data['score'] = 0
        level = query.data.split("_")[1]
    else:
        level = context.user_data.get('current_level', 'hsk1')

    context.user_data['current_level'] = level
    words = data.get(level, [])
    
    if not words or len(words) < 4:
        await query.edit_message_text(f"{level.upper()} darajasida so'zlar yetarli emas (kamida 4 ta bo'lishi kerak).")
        return

    correct = random.choice(words)
    others = random.sample([w['translation'] for w in words if w['translation'] != correct['translation']], 3)
    options = others + [correct['translation']]
    random.shuffle(options)
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct['translation']}_{level}")] for opt in options]
    await query.edit_message_text(f"So'z: {correct['word']}\nTarjimasini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, user_ans, correct_ans, level = query.data.split("_")
    
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
