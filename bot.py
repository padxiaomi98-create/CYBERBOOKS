import os, json, random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ... load_data funksiyasi avvalgidek qoladi ...

async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    
    if query.data.startswith("start_"):
        context.user_data['score'] = 0
        context.user_data['wrong_words'] = [] # Noto'g'ri topilgan so'zlar uchun xotira
        level = query.data.split("_")[1]
    else:
        level = context.user_data.get('current_level', 'hsk1')

    context.user_data['current_level'] = level
    words = data.get(level, [])
    
    if len(words) < 4:
        await query.edit_message_text(f"{level.upper()} darajasida so'zlar yetarli emas!")
        return

    # MANTIQ: Agar noto'g'ri topilgan so'zlar bo'lsa, ulardan birini tanla, aks holda tasodifiy so'z
    wrong_list = context.user_data.get('wrong_words', [])
    if wrong_list and random.random() < 0.6: # 60% ehtimollik bilan xato topilgan so'zni qayta berish
        correct = next(w for w in words if w['translation'] == random.choice(wrong_list))
    else:
        correct = random.choice(words)

    # 3 ta noto'g'ri variant tanlash
    others = random.sample([w['translation'] for w in words if w['translation'] != correct['translation']], 3)
    options = others + [correct['translation']]
    random.shuffle(options)
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}_{correct['translation']}_{level}")] for opt in options]
    await query.edit_message_text(f"🀄️ So'z: {correct['word']}\n\nTarjimasini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, user_ans, correct_ans, level = query.data.split("_")
    
    if user_ans == correct_ans:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        # Agar to'g'ri topsa, so'zni xato ro'yxatidan o'chirib tashlaymiz
        if correct_ans in context.user_data.get('wrong_words', []):
            context.user_data['wrong_words'].remove(correct_ans)
        status = "✅ To'g'ri!"
    else:
        # Noto'g'ri topsa, so'zni ro'yxatga qo'shamiz
        if correct_ans not in context.user_data.get('wrong_words', []):
            context.user_data['wrong_words'].append(correct_ans)
        status = f"❌ Noto'g'ri! To'g'risi: {correct_ans}"
    
    keyboard = [[InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"next_{level}")]]
    await query.edit_message_text(f"{status}\n\n🏆 Ball: {context.user_data.get('score', 0)}", reply_markup=InlineKeyboardMarkup(keyboard))
