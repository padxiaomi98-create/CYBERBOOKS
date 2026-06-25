import os, json, random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

load_dotenv()
# words.json faylini o'qib olish
with open("words.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Reply menyu (Pastki tugmalar)
def get_reply_menu():
    keyboard = [["📚 Quizni boshlash", "📊 Natijalar"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# 2. Inline menyu (Darajalar)
def get_level_menu():
    levels = ["hsk1", "hsk2", "hsk3", "hsk4", "hsk5", "hsk6", "hsk7", "hsk8", "hsk9"]
    keyboard = []
    row = []
    for i, level in enumerate(levels):
        row.append(InlineKeyboardButton(level.upper(), callback_data=f"start_{level}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("HSK 3.0 Quiz botiga xush kelibsiz!", reply_markup=get_reply_menu())

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📚 Quizni boshlash":
        await update.message.reply_text("Darajani tanlang:", reply_markup=get_level_menu())
    elif text == "📊 Natijalar":
        score = context.user_data.get('score', 0)
        await update.message.reply_text(f"Sizning oxirgi natijangiz: {score} ball.")

# 3. Quiz mantig'i
async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Yangi daraja tanlansa, ballni nolga tenglaymiz
    if query.data.startswith("start_"):
        context.user_data['score'] = 0
        level = query.data.split("_")[1]
    else:
        # Keyingi savol uchun joriy darajani olish
        level = context.user_data.get('current_level', 'hsk1')

    context.user_data['current_level'] = level
    words = data.get(level, [])
    
    if not words:
        await query.edit_message_text("Ushbu darajada so'zlar topilmadi.")
        return

    correct = random.choice(words)
    others = random.sample([w['translation'] for w in words if w['translation'] != correct['translation']], min(3, len(words)-1))
    options = others + [correct['translation']]
    random.shuffle(options)
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct['translation']}_{level}")] for opt in options]
    await query.edit_message_text(f"So'z: {correct['word']}\nTarjimasini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

# 4. Javobni tekshirish va ball
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, user_ans, correct_ans, level = query.data.split("_")
    
    if user_ans == correct_ans:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        status = "✅ To'g'ri!"
    else:
        status = f"❌ Noto'g'ri! To'g'risi: {correct_ans}"
    
    keyboard = [[InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"next_{level}")],
                [InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="main")]]
    
    await query.edit_message_text(f"{status}\n\n🏆 Ball: {context.user_data.get('score', 0)}", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(CallbackQueryHandler(quiz_handler, pattern="^(start|next)_"))
    app.add_handler(CallbackQueryHandler(check_answer, pattern="^ans_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("Darajani tanlang:", reply_markup=get_level_menu()), pattern="^main$"))
    app.run_polling()
