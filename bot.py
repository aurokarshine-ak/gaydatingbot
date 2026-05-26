import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Conversation States
GENDER, AGE, PROFILE_PHOTO, LOOKING_FOR, BIO = range(5)

# In-memory Databases
user_db = {}    # { user_id: {gender, age, photo_file_id, looking_for, bio, username} }
likes_db = {}   # { user_id: set( liked_user_ids ) }

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
    await update.message.reply_text("✨ သင့်ရဲ့ Profile ဓာတ်ပုံတစ်ပုံ ပို့ပေးပါဦးဗျာ။")
    return PROFILE_PHOTO

async def profile_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("ကျေးဇူးပြု၍ ဓာတ်ပုံစစ်စစ်တစ်ပုံ ပို့ပေးပါဗျာ။")
        return PROFILE_PHOTO
        
    photo_file_id = update.message.photo[-1].file_id
    context.user_data['photo_file_id'] = photo_file_id
    
    await update.message.reply_text(
        "ဘယ်သူတွေနဲ့ Match လုပ်ချင်လဲဗျာ?",
        reply_markup=ReplyKeyboardMarkup([['Top ရှာမယ်', 'Bottom ရှာမယ်', 'မရွေးပါ']], one_time_keyboard=True)
    )
    return LOOKING_FOR

async def looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['looking_for'] = update.message.text
    await update.message.reply_text("သင့်အကြောင်း ရှင်းလင်းချက် (Bio) အနည်းငယ် ရေးပေးပါဦးဗျာ။", reply_markup=ReplyKeyboardRemove())
    return BIO

async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['bio'] = update.message.text
    context.user_data['username'] = user.username if user.username else "No Username"
    
    user_db[user.id] = context.user_data
    if user.id not in likes_db:
        likes_db[user.id] = set()
        
    await update.message.reply_text("မှတ်ပုံတင်လို့ အောင်မြင်သွားပါပြီ! 🎉\n\nတခြားသူတွေကို ရှာဖွေဖို့အတွက် /find လို့ ရိုက်ထည့်လိုက်ပါဗျာ။")
    await update.message.reply_photo(
        photo=context.user_data['photo_file_id'],
        caption=f"📝 သင့် Profile-\nအသက်: {context.user_data['age']}\nအမျိုးအစား: {context.user_data['gender']}\nရှာနေတာ: {context.user_data['looking_for']}\nBio: {context.user_data['bio']}"
    )
    return ConversationHandler.END

async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_user_id = update.message.from_user.id
    if current_user_id not in user_db:
        await update.message.reply_text("အရင်ဆုံး /start ကိုနှိပ်ပြီး Profile အရင်ဆောက်ပေးပါဦး။")
        return
        
    # ကိုယ် Like ထားပြီးသားလူတွေကို ဖယ်ထုတ်ပြီး ရှာမယ်
    my_likes = likes_db.get(current_user_id, set())
    
    found_user_id = None
    found_data = None
    
    for u_id, data in user_db.items():
        if u_id != current_user_id and u_id not in my_likes:
            found_user_id = u_id
            found_data = data
            break
            
    if found_user_id and found_data:
        # Inline Buttons (Like နဲ့ Next ခလုတ်)
        keyboard = [
            [
                InlineKeyboardButton("❤️ Like", callback_data=f"like_{found_user_id}"),
                InlineKeyboardButton("❌ Next", callback_data="next_match")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=found_data['photo_file_id'],
            caption=f"✨ Match လောင်းလျာ ရှာတွေ့ပါတယ် ✨\n\n"
                    f"အသက်: {found_data['age']}\n"
                    f"အမျိုးအစား: {found_data['gender']}\n"
                    f"Bio: {found_data['bio']}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("စိတ်မရှိပါနဲ့ဦးဗျာ၊ လောလောဆယ် သင့်အတွက် လူအသစ် မရှိသေးလို့ နောက်မှ ပြန်စမ်းကြည့်ပေးပါဦး။ 🥺")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_user_id = query.from_user.id
    data = query.data
    
    if data.startswith("like_"):
        liked_user_id = int(data.split("_")[1])
        
        # ကိုယ့်ရဲ့ Like Database ထဲ ထည့်လိုက်မယ်
        if current_user_id not in likes_db:
            likes_db[current_user_id] = set()
        likes_db[current_user_id].add(liked_user_id)
        
        # တစ်ဖက်လူကလည်း ကိုယ့်ကို ပြန် Like ထားလား စစ်မယ် (Match စစ်ဆေးခြင်း)
        other_user_likes = likes_db.get(liked_user_id, set())
        
        if current_user_id in other_user_likes:
            # **MATCH ဖြစ်သွားပြီ!**
            other_user_data = user_db.get(liked_user_id)
            current_user_data = user_db.get(current_user_id)
            
            # ကိုယ့်ဆီ စာပို့မယ်
            await query.edit_message_caption(
                caption=query.message.caption + f"\n\n🎉 **It's a Match!** 🎉\nသူ့ကို @{other_user_data['username']} မှာ လှမ်းနှုတ်ဆက်လိုက်ပါဗျာ။"
            )
            
            # ဟိုဘက်လူဆီကိုလည်း Bot ကနေ အလိုအလျောက် သွားသတိပေးမယ်
            try:
                await context.bot.send_message(
                    chat_id=liked_user_id,
                    text=f"🎉 **Match အသစ် ရပါပြီ!** 🎉\n\n@{current_user_data['username']} က သင့်ကို ပြန်ပြီး Like လုပ်လိုက်လို့ အပြန်အလှန် Match ဖြစ်သွားပါပြီဗျာ။ သွားရောက် စကားပြောနိုင်ပါပြီ။"
                )
            except Exception as e:
                logging.error(f"Failed to send match notification to {liked_user_id}: {e}")
        else:
            # Like လိုက်ပေမယ့် ဟိုဘက်က မ Like သေးရင်
            await query.edit_message_caption(caption=query.message.caption + "\n\n❤️ သူ့ကို Like လုပ်လိုက်ပါပြီ။ (သူက ပြန် Like ရင် Match ဖြစ်မှာပါ)")
            
    elif data == "next_match":
        # Next နှိပ်ရင် အရင် message ကို ဖြတ်ပြီး နောက်တစ်ယောက် ထပ်ရှာပေးမယ်
        await query.message.delete()
        # Message ပြန်ပို့ဖို့ အဆင်ပြေအောင် update အတု ဖန်တီးပြီး find_match ကို ခေါ်တာပါ
        class DummyMessage:
            def __init__(self, from_user, chat_id, bot):
                self.from_user = from_user
                self.chat_id = chat_id
                self.bot = bot
            async def reply_text(self, text, **kwargs):
                return await self.bot.send_message(chat_id=self.chat_id, text=text, **kwargs)
            async def reply_photo(self, photo, caption, reply_markup=None, **kwargs):
                return await self.bot.send_photo(chat_id=self.chat_id, photo=photo, caption=caption, reply_markup=reply_markup, **kwargs)
                
    update.message = DummyMessage(query.from_user, query.message.chat_id, context.bot)
    await find_match(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("BOT_TOKEN") 
    if not TOKEN:
        print("Error: BOT_TOKEN not found.")
        return

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            PROFILE_PHOTO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, profile_photo)],
            LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, looking_for)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('find', find_match))
    application.add_handler(CallbackQueryHandler(button_handler)) # Like/Next ခလုတ်တွေ ဖတ်ဖို့
    
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling()

if __name__ == '__main__':
    main()
