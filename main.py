import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Yahan apna Bot Token dalein
BOT_TOKEN = "8975821926:AAHT9o1zKveOewvGdynjdea1hpa5ulDMwQ0"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Name ke andar agar '<', '>' ya '&' ho toh code crash na ho uske liye safe HTML replace
    first_name = user.first_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if user.first_name else ""
    last_name = user.last_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if user.last_name else "None"

    # 1. Welcome Message
    welcome_text = (
        f"<b>𝐍ᴀᴍᴀꜱᴛᴇ {first_name}</b> ✨\n\n"
        f"<i>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴜꜱᴇʀ ʜɪꜱᴛᴏʀ ʙᴏᴛ\nᴡᴇ ᴄᴀɴ ʜᴇʟᴘ ᴀɴᴅ ᴀʟᴍᴏꜱᴛ ʏᴏᴜ ɢᴇᴛ ʏᴏᴜʀ ᴀʙᴏᴜᴛ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ ᴀʟᴡᴀʏꜱ, ᴘʟᴇᴀꜱᴇ ꜱʜᴀʀᴇ ᴍᴇ ᴡɪᴛʜ ʏᴏᴜʀ ꜰʀɪᴇɴᴅꜱ ɢʀᴏᴜᴘꜱ ᴋᴇᴇᴘ ꜱᴜᴘᴘᴏʀᴛ.</i>\n\n"
        f"<b>ʜᴇʀᴇ ɪꜱ ʏᴏᴜʀ ᴜꜱᴇʀ ᴀʙᴏᴜᴛ ʜɪꜱᴛᴏʀʏ</b>"
    )
    # parse_mode="HTML" add kar diya hai
    await update.message.reply_text(welcome_text, parse_mode="HTML")

    # 2. Profile Photos fetch karna safely
    try:
        photos = await context.bot.get_user_profile_photos(user.id)
        photo_count = photos.total_count if photos else 0
    except Exception:
        photo_count = 0

    # 3. User Info Message
    info_text = (
        f"<b>➻ ᴀʙᴏᴜᴛ ᴜꜱᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ :</b>\n────────────────────\n"
        f"๏ ꜰɪʀꜱᴛ ɴᴀᴍᴇ : {first_name}\n"
        f"๏ ʟᴀꜱᴛ ɴᴀᴍᴇ : {last_name}\n"
        f"๏ ᴜꜱᴇʀɴᴀᴍᴇ : @{user.username if user.username else 'None'}\n"
        f"๏ ᴜꜱᴇʀ ɪᴅ : <code>{user.id}</code>\n"
        f"๏ ʟᴀɴɢᴜᴀɢᴇ : {user.language_code if user.language_code else 'N/A'}\n"
        f"๏ ᴘʀᴏꜰɪʟᴇ ᴘɪᴄᴛᴜʀᴇ : {photo_count}\n────────────────────\n"
    )

    # parse_mode="HTML" add kar diya hai
    await update.message.reply_text(info_text, parse_mode="HTML")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Bot chalu ho gaya hai...")
    app.run_polling()


if __name__ == "__main__":
    main()
    
