import os, json, random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

def load_data():
    with open("words.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_reply_menu():
    return ReplyKeyboardMarkup([["📚 Quizni boshlash", "📊 Natijalar"]], resize_keyboard=True)

def get_level_menu():
    data = load_data()
    levels = ["hsk1", "hsk2", "hsk3", "hsk4", "hsk5", "hsk6", "hsk7", "hsk8", "hsk9"]
    keyboard = []
    row = []
    for i, level in enumerate(levels):
        count = len(data.get(level, []))
        row.append(InlineKeyboardButton(f"{level.upper()} ({count})", callback_data=f"start_{level}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Smart HSK Quiz botiga xush kelibsiz.", reply_markup=get_reply_menu())

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📚 Quizni boshlash":
        await update.message.reply_text("Darajani tanlang:", reply_markup=get_level_menu())
    elif update.message.text == "📊 Natijalar":
        score = context.user_data.get('score', 0)
        wrong_count = len(context.user_data.get('wrong_words', []))
        await update.message.reply_text(f"🏆 Ball: {score}\n⚠️ Takrorlashingiz kerak bo'lgan so'zlar: {wrong_count} ta.")

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    
    # 1. Yangi quiz boshlanganda sanagichni 0 qilish
    if query.data.startswith("start_"):
        context.user_data['score'] = 0
        context.user_data['wrong_words'] = []
        context.user_data['question_count'] = 0
        level = query.data.split("_")[1]
    else:
        level = context.user_data.get('current_level', 'hsk1')

    # 2. Savollar sonini oshirish
    context.user_data['question_count'] += 1
    
    # 3. 4 ta savoldan keyin yakunlash
    if context.user_data['question_count'] > 4:
        await finish_quiz(update, context)
        return

    context.user_data['current_level'] = level
    words = data.get(level, [])
    
    if len(words) < 4:
        await query.edit_message_text(f"{level.upper()} darajasida so'zlar yetarli emas!")
        return

    # Smart tanlov
    wrong_words = context.user_data.get('wrong_words', [])
    if wrong_words and random.random() < 0.6:
        correct = next(w for w in words if w['translation'] == random.choice(wrong_words))
    else:
        correct = random.choice(words)

    others = random.sample([w['translation'] for w in words if w['translation'] != correct['translation']], 3)
    options = others + [correct['translation']]
    random.shuffle(options)
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct['translation']}_{level}")] for opt in options]
    await query.edit_message_text(
        f"Savol №{context.user_data['question_count']}/4\n🀄️ So'z: {correct['word']}\n\nTarjimasini tanlang:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, user_ans, correct_ans, level = query.data.split("_")
    
    wrong_words = context.user_data.get('wrong_words', [])
    if user_ans == correct_ans:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        if correct_ans in wrong_words:
            wrong_words.remove(correct_ans)
        status = "✅ To'g'ri!"
    else:
        if correct_ans not in wrong_words:
            wrong_words.append(correct_ans)
        status = f"❌ Noto'g'ri! To'g'risi: {correct_ans}"
    
    context.user_data['wrong_words'] = wrong_words
    keyboard = [[InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"next_{level}")]]
    await query.edit_message_text(f"{status}\n\n🏆 Ball: {context.user_data.get('score', 0)}", reply_markup=InlineKeyboardMarkup(keyboard))

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    score = context.user_data.get('score', 0)
    wrong_count = len(context.user_data.get('wrong_words', []))
    
    text = (f"🏁 Quiz yakunlandi!\n\n"
            f"🏆 Yakuniy natija: {score}/4 ball.\n"
            f"⚠️ Xato qilingan so'zlar: {wrong_count} ta.\n\n"
            f"Boshqa darajani tanlash uchun menyudan foydalaning.")
    await query.edit_message_text(text=text, reply_markup=None)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(CallbackQueryHandler(quiz_handler, pattern="^(start|next)_"))
    app.add_handler(CallbackQueryHandler(check_answer, pattern="^ans_"))
    app.run_polling()
