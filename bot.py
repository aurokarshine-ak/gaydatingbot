import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Conversation States
GENDER, AGE, LOOKING_FOR, BIO = range(4)
user_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "မင်္ဂလာပါဗျာ! Myanmar Gay Dating Bot မှ ကြိုဆိုပါတယ်။\n"
        "Matching စလုပ်ဖို့ သင့်ရဲ့ ကိုယ်ရေးအချက်အလက်လေး အရင်ဖြည့်ရအောင်။\n\n"
        "သင်က Top လား၊ Bottom လားဗျာ?",
        reply_markup=ReplyKeyboardMarkup([['Top', 'Bottom']], one_time_keyboard=True)
    )
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gender'] = update.message.text
    await update.message.reply_text("သင့်အသက် ဘယ်လောက်လဲဗျာ?", reply_markup=ReplyKeyboardRemove())
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text(
        "ဘယ်သူတွေနဲ့ Match လုပ်ချင်လဲဗျာ?",
        reply_markup=ReplyKeyboardMarkup([['Top ရှာမယ်', 'Bottom ရှာမယ်', 'မရွေးပါ']], one_time_keyboard=True)
    )
    return LOOKING_FOR

async def looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['looking_for'] = update.message.text
    await update.message.reply_text("သင့်အကြောင်း ရှင်းလင်းချက် (Bio) အနည်းငယ် ရေးပေးပါဦးဗျာ။")
    return BIO

async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['bio'] = update.message.text
    context.user_data['username'] = user.username if user.username else "No Username"
    user_db[user.id] = context.user_data
    await update.message.reply_text("မှတ်ပုံတင်လို့ အောင်မြင်သွားပါပြီ! 🎉\n\nတခြားသူတွေကို ရှာဖွေဖို့အတွက် /find လို့ ရိုက်ထည့်လိုက်ပါဗျာ။")
    return ConversationHandler.END

async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_user_id = update.message.from_user.id
    if current_user_id not in user_db:
        await update.message.reply_text("အရင်ဆုံး /start ကိုနှိပ်ပြီး Profile အရင်ဆောက်ပေးပါဦး။")
        return
        
    found = False
    for user_id, data in user_db.items():
        if user_id != current_user_id:
            await update.message.reply_text(
                f"✨ Match တစ်ယောက် ရှာတွေ့ပါတယ်။ ✨\n\n"
                f"အသက်: {data['age']}\n"
                f"အမျိုးအစား: {data['gender']}\n"
                f"အကြောင်းအရာ: {data['bio']}\n"
                f"စကားပြောရန်: @{data['username']}"
            )
            found = True
            break
            
    if not found:
        await update.message.reply_text("စိတ်မရှိပါနဲ့ဦးဗျာ၊ လောလောဆယ် Database ထဲမှာ လူအသစ် မရှိသေးလို့ နောက်မှ ပြန်စမ်းကြည့်ပေးပါဦး။ 🥺")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    # Railway ရဲ့ Variables ထဲက BOT_TOKEN ကို လှမ်းဖတ်တာပါ
    TOKEN = os.getenv("BOT_TOKEN") 
    
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, looking_for)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('find', find_match))
    
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling()

if __name__ == '__main__':
    main()
