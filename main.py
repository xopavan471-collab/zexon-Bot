import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

# Bot configuration (Apna API_ID, API_HASH aur BOT_TOKEN yaha daalein)
API_ID = "33208732"
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "9168309428:AAE8sogWyIgeS3KG8oKJJVxH-BA8dYaf_hg"

app = Client("ZexonAllInOneBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Quality selection ke liye inline buttons layout
def get_quality_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 360p ⏳", callback_data="dl_360"),
                InlineKeyboardButton("🎬 480p ⏳", callback_data="dl_480")
            ],
            [
                InlineKeyboardButton("🎬 720p ⏳", callback_data="dl_720"),
                InlineKeyboardButton("🎬 1080p ⏳", callback_data="dl_1080")
            ],
            [
                InlineKeyboardButton("🎵 Audio 320kbps (MP3) ⏳", callback_data="dl_mp3_320")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
    )

@app.on_message(filters.text & filters.private & (filters.regex("http://") | filters.regex("https://")))
async def link_handler(client: Client, message: Message):
    url = message.text.strip()
    
    # Step 1: Checking... message bhejna
    status_msg = await message.reply_text("Checking... 🔍")
    
    # Thoda sa pause simulate karne ke liye ya yt-dlp info extract karne ke liye
    try:
        ydl_opts = {'extract_flat': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Social Media Video/Audio')
    except Exception:
        title = "Analyzed social video."

    # Step 2: Downloading status update karna
    await status_msg.edit_text("Downloading... ⏳")
    
    # Kuch seconds baad ya process ke baad quality options show karna
    caption = (
        f"**Zexon All-in-One Bot:** Link analyzed! ⬇️\n"
        f"Platform: Supported social media link.\n"
        f"Title: {title}\n\n"
        f"Apni pasand ki quality select karein:"
    )
    
    await status_msg.delete()
    await message.reply_text(caption, reply_markup=get_quality_keyboard())

@app.on_callback_query(filters.regex("^dl_"))
async def download_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    await callback_query.answer(f"Processing selection: {data}", show_alert=False)
    await callback_query.message.edit_text(f"✅ Selected option processed. Downloading file... (Feature under execution)")

@app.on_callback_query(filters.regex("^close$"))
async def close_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()

# Bot start karne ke liye
if __name__ == "__main__":
    print("Zexon All-in-One Bot is starting...")
    app.run()
