import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

# Apne bot credentials yahan daalein ya environment variables use karein
API_ID = "33208732"
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "9168309428:AAE8sogWyIgeS3KG8oKJJVxH-BA8dYaf_hg"

app = Client("ZexonAllInOneBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

# Common headers for yt-dlp to bypass bot detection on YouTube/Facebook
YT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_quality_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 360p", callback_data="dl_360"),
                InlineKeyboardButton("🎬 480p", callback_data="dl_480")
            ],
            [
                InlineKeyboardButton("🎬 720p", callback_data="dl_720"),
                InlineKeyboardButton("🎬 1080p", callback_data="dl_1080")
            ],
            [
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_mp3")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
    )

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    welcome_text = (
        f"**👋 Welcome to Zexon All-in-One Downloader Bot!**\n\n"
        f"Yahan aap Instagram, YouTube aur Facebook ke links bhej kar asani se media download kar sakte hain.\n\n"
        f"Bas koi bhi link yahan bhejhiye! 🚀"
    )
    await message.reply_text(welcome_text)

@app.on_message(filters.text & filters.private & (filters.regex("http://") | filters.regex("https://")))
async def link_handler(client: Client, message: Message):
    url = message.text.strip()
    status_msg = await message.reply_text("Checking... 🔍")
    
    # Instagram ke liye direct download flow
    if "instagram.com" in url:
        await status_msg.edit_text("Downloading... ⏳")
        
        output_template = f"downloads/{message.from_user.id}_%(id)s.%(ext)s"
        os.makedirs("downloads", exist_ok=True)
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'http_headers': YT_HEADERS,
        }
        
        try:
            def download_insta():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info_dict)
                    return file_path, info_dict.get('title', 'Instagram Video')

            loop = asyncio.get_event_loop()
            file_path, title = await loop.run_in_executor(None, download_insta)
            
            await status_msg.edit_text("Uploading... 📤")
            await message.reply_video(video=file_path, caption=title)
            await status_msg.delete()
            
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            await status_msg.edit_text(f"❌ Failed: {str(e)}")
            
    else:
        # YouTube ya Facebook ke liye thumbnail aur quality options show karna
        try:
            ydl_opts = {
                'quiet': True, 
                'no_warnings': True,
                'http_headers': YT_HEADERS
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Social Media Video')
                thumbnail = info.get('thumbnail', None)
                duration = info.get('duration', 0)
                
            user_data[message.from_user.id] = {'url': url, 'title': title}
            await status_msg.delete()
            
            caption = (
                f"📥 **Video Found!**\n\n"
                f"📌 **Title:** {title}\n"
                f"⏱ **Duration:** {duration} seconds\n\n"
                f"Apni pasand ki quality select karein:"
            )
            
            if thumbnail:
                await message.reply_photo(photo=thumbnail, caption=caption, reply_markup=get_quality_keyboard())
            else:
                await message.reply_text(caption, reply_markup=get_quality_keyboard())
                
        except Exception as e:
            await status_msg.edit_text(f"❌ Error analyzing link: {str(e)}")

@app.on_callback_query(filters.regex("^dl_"))
async def download_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if user_id not in user_data:
        await callback_query.answer("Session expired! Please send the link again.", show_alert=True)
        return
        
    url = user_data[user_id]['url']
    format_type = data.split("_")[1]
    
    # Post ko delete karke Downloading... start karna
    await callback_query.message.delete()
    status_msg = await client.send_message(callback_query.message.chat.id, "Downloading... ⏳ Please wait.")
    
    output_template = f"downloads/{user_id}_%(id)s.%(ext)s"
    os.makedirs("downloads", exist_ok=True)
    
    if format_type == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'http_headers': YT_HEADERS,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        res_map = {"360": "360", "480": "480", "720": "720", "1080": "1080"}
        height = res_map.get(format_type, "720")
        ydl_opts = {
            'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best',
            'outtmpl': output_template,
            'http_headers': YT_HEADERS,
            'merge_output_format': 'mp4',
        }
        
    try:
        def download_file():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                if format_type == "mp3":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"
                return file_path, info_dict.get('title', 'Media')

        loop = asyncio.get_event_loop()
        file_path, title = await loop.run_in_executor(None, download_file)
        
        await status_msg.edit_text("Uploading to Telegram... 📤")
        
        if format_type == "mp3":
            await client.send_audio(chat_id=callback_query.message.chat.id, audio=file_path, caption=title)
        else:
            await client.send_video(chat_id=callback_query.message.chat.id, video=file_path, caption=title)
            
        await status_msg.delete()
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Download Failed: {str(e)}")

@app.on_callback_query(filters.regex("^close$"))
async def close_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()

if __name__ == "__main__":
    print("Zexon All-in-One Bot is starting...")
    app.run()
