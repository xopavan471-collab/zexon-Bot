import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = "9168309428:AAE8sogWyIgeS3KG8oKJJVxH-BA8dYaf_hg"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Step 1: Link aate hi Info nikal ke same look dikhao
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url:
        return

    context.user_data['last_url'] = url
    await update.message.reply_text("⏳ Fetching...")

    # Sirf info nikalna hai, download nahi
    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Video')
        thumbnail = info.get('thumbnail')
        duration = info.get('duration_string', '')
        
        # Available qualities check
        formats = info.get('formats', [])
        heights = set([f.get('height') for f in formats if f.get('height')])
        
        # Button layout - Bilkul tere screenshot jaisa
        keyboard = []
        row1 = []
        row2 = []
        if 360 in heights or True: # hamesha dikhana hai
            row1.append(InlineKeyboardButton("🎬 360p (⏳)", callback_data="360"))
        if 480 in heights or True:
            row1.append(InlineKeyboardButton("🎬 480p (⏳)", callback_data="480"))
        
        if 720 in heights or True:
            row2.append(InlineKeyboardButton("🎬 720p (⏳)", callback_data="720"))
        if 1080 in heights or True:
            row2.append(InlineKeyboardButton("🎬 1080p (⏳)", callback_data="1080"))

        keyboard.append(row1)
        keyboard.append(row2)
        keyboard.append([InlineKeyboardButton("🎵 Audio", callback_data="audio")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Same look - Photo + Title + Buttons
        caption = f"🍿 {title}\n\n🔥 FF Panel Bot | Select Quality 👇"
        # Agar thumbnail hai toh photo ke sath bhejo
        if thumbnail:
            await update.message.reply_photo(photo=thumbnail, caption=caption, reply_markup=reply_markup)
        else:
            await update.message.reply_text(caption, reply_markup=reply_markup)

# Step 2: Quality select pe download
async def download_on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('last_url')
    quality = query.data
    
    await query.edit_message_caption(caption=f"⏳ Downloading {quality}... Ruk ja bhai")

    format_map = {
        "360": "best[height<=360][ext=mp4]/best",
        "480": "best[height<=480][ext=mp4]/best",
        "720": "best[height<=720][ext=mp4]/best",
        "1080": "best[height<=1080][ext=mp4]/best",
        "audio": "bestaudio/best"
    }

    ydl_opts = {
        'format': format_map.get(quality, 'best'),
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    }
    if quality == "audio":
        ydl_opts.update({
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if quality == "audio":
                file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Bhej de
            if quality == "audio":
                await query.message.reply_audio(audio=open(file_path, 'rb'), title=info.get('title'))
            else:
                await query.message.reply_video(video=open(file_path, 'rb'), caption=f"✅ {quality}p Downloaded")
            
            os.remove(file_path)
            await query.edit_message_caption(caption=f"✅ Done - {quality}")
    except Exception as e:
        await query.message.reply_text(f"Error: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(download_on_click))

print("Bot Ready - Same look as screenshot")
app.run_polling()
