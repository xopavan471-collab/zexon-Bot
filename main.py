import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup - errors aur activity check karne ke liye
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Aapka Bot Token yahan daalein
BOT_TOKEN = "BOT TOKEN"


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 Hello **{user.first_name}**!\n\n"
        f"Main ek **User Info Bot** hoon. Apni ya kisi message ki info nikalne ke liye `/info` command ka use karein ya kisi user ke message ko replay karke `/info` bhejein."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


# /info command handler
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Agar user ne kisi ke message par reply kiya hai, toh us reply waale user ki details lenge
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        # Warna command bhejney waale user ki details lenge
        target_user = update.effective_user

    # User ki profile pictures ki count nikalna
    photos = await context.bot.get_user_profile_photos(target_user.id)
    photo_count = photos.total_count if photos else 0

    # Information format karna
    info_text = (
        f"👤 **USER INFORMATION** 👤\n\n"
        f"🔹 **First Name:** {target_user.first_name}\n"
        f"🔹 **Last Name:** {target_user.last_name if target_user.last_name else 'None'}\n"
        f"🔹 **Username:** @{target_user.username if target_user.username else 'None'}\n"
        f"🔹 **User ID:** `{target_user.id}`\n"
        f"🔹 **Is Bot:** {'Yes' if target_user.is_bot else 'No'}\n"
        f"🔹 **Language Code:** {target_user.language_code if target_user.language_code else 'N/A'}\n"
        f"🔹 **Profile Photos:** {photo_count}\n"
    )

    await update.message.reply_text(info_text, parse_mode="Markdown")


def main():
    # Application build karna
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers register karna
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", user_info))

    print("Bot chalu ho gaya hai...")
    # Bot ko run karna
    app.run_polling()


if __name__ == "__main__":
    main()
  
