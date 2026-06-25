import os, json, random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
with open("words.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Asosiy Menyuni Yaratish (BotFather uslubi)
def get_main_menu():
    levels = ["hsk1", "hsk2", "hsk3", "hsk4", "hsk5", "hsk6", "hsk7", "hsk8", "hsk9"]
    keyboard = []
    row = []
    for i, level in enumerate(levels):
        row.append(InlineKeyboardButton(level.upper(), callback_data=f"start_{level}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(keyboard)

# 2. Savol berish funksiyasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Darajani tanlang va bilimingizni do'stlaringiz bilan sinang:", reply_markup=get_main_menu())

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    level = query.data.split("_")[1]
    words = data.get(level, [])
    
    if len(words) < 4:
        await query.edit_message_text("Ushbu darajada so'zlar yetarli emas. Iltimos, bazani boyiting!")
        return

    # To'g'ri so'z va 3 ta noto'g'ri variant
    correct = random.choice(words)
    others = random.sample([w['translation'] for w in words if w['translation'] != correct['translation']], 3)
    options = others + [correct['translation']]
    random.shuffle(options)
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct['translation']}_{level}")] for opt in options]
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")])
    
    await query.edit_message_text(f"🀄️ So'z: {correct['word']}\n\nTarjimasini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

# 3. Javobni tekshirish
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_parts = query.data.split("_")
    user_ans, correct_ans, level = data_parts[1], data_parts[2], data_parts[3]
    
    if user_ans == correct_ans:
        text = "✅ To'g'ri! "
    else:
        text = f"❌ Noto'g'ri! To'g'risi: {correct_ans}\n"
    
    # "Keyingi" tugmasi
    keyboard = [[InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"start_{level}")],
                [InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="main_menu")]]
    
    await query.edit_message_text(f"{text}\n\nDo'stlaringizga ham ulashing!", reply_markup=InlineKeyboardMarkup(keyboard))

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("Darajani tanlang:", reply_markup=get_main_menu())

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(quiz_handler, pattern="^start_"))
    app.add_handler(CallbackQueryHandler(check_answer, pattern="^ans_"))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.run_polling()
