import asyncio
import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

API_ID = 33208732  
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "MEWWWW GHOP GHOP 😂"
ADMIN_ID = 8562470788

REQUIREMENTS_CHANNEL = -1004334558910
UPDATE_CHANNEL_USERNAME = "zexon_Bot_updates"
UPDATE_CHANNEL_INVITE = "https://t.me/zexon_Bot_updates"

app = Client(
    "zexon_yt_downloader_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    workdir="./",
    workers=16
)

user_yt_links = {}
START_TEXT = (
    "<b>𝐇ɪ {name} ✨</b>\n\n"
    "<blockquote><b>ᴡᴇʟᴄᴏᴍᴇ ʏᴏᴜ ᴛᴜʙᴇ ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ</b></blockquote>\n"
    "<blockquote><b>ᴡᴇ ᴄᴀɴ ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʏᴏᴜ ᴛᴜʙᴇ ᴀᴜᴅɪᴏ ᴀɴᴅ ᴠɪᴅᴇᴏ ꜱᴇᴄᴜʀᴇ, ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜ ᴛᴜʙᴇ ᴠɪᴅᴇᴏ ʟɪɴᴋ ᴀɴᴅ ɢɪᴠᴇ ʏᴏᴜ ᴏᴘᴛɪᴏɴꜱ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴀᴜᴅɪᴏ ᴀɴᴅ ᴠɪᴅᴇᴏ, ᴡʜᴇɴ ʏᴏᴜ ᴄʜᴏᴏꜱɪɴɢ ʏᴏᴜʀ ᴠɪᴅᴇᴏ ᴀᴜᴅɪᴏ ꜰᴏʀᴍᴀᴛ ᴛʜᴇɴ ᴡᴇ ᴅᴏᴡɴʟᴏᴀᴅ ꜰʀᴏᴍ ʏᴏᴜʀ ᴄʜᴏɪᴄᴇ ᴀɴᴅ ɢɪᴠᴇ ʏᴏᴜ ᴠɪᴅᴇᴏ ᴀᴜᴅɪᴏ ɪɴꜱᴛᴀɴᴛʟʏ.</b></blockquote>\n"
    "<blockquote><b>ɪꜰ ʏᴏᴜ ᴀʀᴇ ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʟɪɴᴋ</b></blockquote>"
)

def save_user(user):
    try:
        users_file = "users.txt"
        user_id = str(user.id)
        existing_users = set()
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                existing_users = set(f.read().splitlines())
        if user_id not in existing_users:
            with open(users_file, "a", encoding="utf-8") as f:
                f.write(f"{user_id}\n")
    except Exception:
        pass

def log_history(user, action_type, title, link):
    try:
        history_file = "download_history.txt"
        name = f"{user.first_name} {user.last_name or ''}".strip()
        log_entry = f"User: {name} (ID: {user.id}) | Action: {action_type} | Title: {title} | Link: {link}\n"
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

# --- YAHI MAIN FIX HAI ---
async def check_subscription(client, user_id):
    try:
        user_member = await client.get_chat_member(UPDATE_CHANNEL_USERNAME, user_id)
        print(f"User Status: {user_member.status}")
        status = str(user_member.status).lower()
        # left / kicked nahi hai to allow hai (owner, admin, member sab)
        if "left" not in status and "kicked" not in status:
            return True
        return False
    except Exception as e:
        print(f"F-Sub Check Error: {e}")
        return False

@app.on_message(filters.command("start") & filters.incoming)
async def start(client: Client, message: Message):
    user = message.from_user
    save_user(user)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    if not await check_subscription(client, user.id):
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📢", url=UPDATE_CHANNEL_INVITE)],
            [InlineKeyboardButton("ᴛʀʏ ᴀɢᴀɪɴ 🔄", callback_data="check_sub")]
        ])
        await message.reply_text(
            "<b>ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ⚠️\n\nᴅᴇᴀʀ, ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴍʏ ᴏᴡɴᴇʀ ᴢᴇxᴏɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ, ᴛʜᴇɴ ᴄʟɪᴄᴋ 'ᴛʀʏ ᴀɢᴀɪɴ'.</b>",
            reply_markup=join_markup
        )
        return
    await message.reply_text(
        text=START_TEXT.format(name=user.first_name),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇꜱ 🔊", url=UPDATE_CHANNEL_INVITE),
             InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ 💬", url="https://t.me/URL_Save_Bot")]
        ]),
        disable_web_page_preview=True
    )

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID) & filters.incoming)
async def stats(client: Client, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    users_file = "users.txt"
    total_users = 0
    if os.path.exists(users_file):
        with open(users_file, "r", encoding="utf-8") as f:
            total_users = len(f.read().splitlines())
    await message.reply_text(f"<b>📊 Bot Statistics:\n\n👥 Total Unique Users: <code>{total_users}</code></b>")

@app.on_message(filters.text & (filters.regex(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/.+")) & filters.incoming)
async def youtube_link_handler(client: Client, message: Message):
    user = message.from_user
    save_user(user)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    if not await check_subscription(client, user.id):
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📢", url=UPDATE_CHANNEL_INVITE)],
            [InlineKeyboardButton("ᴛʀʏ ᴀɢᴀɪɴ 🔄", callback_data="check_sub")]
        ])
        await message.reply_text(
            "<b>ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ⚠️</b>\n\n<b>ᴘʟᴇᴀꜱᴇ ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴍʏ ᴏᴡɴᴇʀ ᴢᴇxᴏɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ, ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ 'ᴛʀʏ ᴀɢᴀɪɴ'</b> 🤨",
            reply_markup=join_markup
        )
        return
    url = message.text.strip()
    status_msg = await message.reply_text("<b>𝐏ʀᴏꜱᴇꜱꜱɪɴɢ...⏳</b>")
    loop = asyncio.get_event_loop()
    def fetch_info_with_cookie(use_cookie=False):
        ydl_opts = {'quiet': True}
        if use_cookie and os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    try:
        info = None
        try:
            info = await loop.run_in_executor(None, lambda: fetch_info_with_cookie(use_cookie=False))
        except Exception:
            info = await loop.run_in_executor(None, lambda: fetch_info_with_cookie(use_cookie=True))
        title = info.get('title', 'YouTube Video')
        thumbnail = info.get('thumbnail', 'https://ibb.co/6R0590P') 
        duration = info.get('duration', 0)
        user_yt_links[user.id] = url
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("𝙰𝚄𝙳𝙸𝙾 🎵", callback_data="dl_audio"),
             InlineKeyboardButton("𝚅𝙸𝙳𝙴𝙾 🎬", callback_data="dl_video")],
            [InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="close_btn")]
        ])
        caption = f"<b>🎬 {title}</b>\n\n<b>ᴅᴜʀᴀᴛɪᴏɴ :</b> <code>{duration} ꜱᴇᴄᴏɴᴅꜱ</code>\n\n<b><i>ᴄʜᴏᴏꜱᴇ ʏᴏᴜʀ ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴏʀᴍᴀᴛ :</i></b>"
        await status_msg.delete()
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        await message.reply_photo(photo=thumbnail, caption=caption, reply_markup=keyboard)
    except Exception as e:
        await status_msg.edit_text(f"❌ **Failed to fetch video:** `{e}`")

@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    user = callback_query.from_user
    if data == "close_btn":
        try: await callback_query.message.delete()
        except Exception: pass
        return
    if data == "check_sub":
        await client.send_chat_action(chat_id, ChatAction.TYPING)
        if await check_subscription(client, user_id):
            await callback_query.message.edit_text("<b>ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ 🎉\n\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴊᴏɪɴɪɴɢ ᴍʏ ᴄʜᴀɴɴᴇʟ ɴᴏᴡ ʏᴏᴜ ꜱᴛᴀʀᴛ ᴀɢᴀɪɴ ᴀɴᴅ ᴄᴏɴᴛɪɴᴜᴇ</b>")
        else:
            await callback_query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴍʏ ᴄʜᴀɴɴᴇʟ ❌", show_alert=True)
        return
    if not await check_subscription(client, user_id):
        await callback_query.answer("ᴘʟᴇᴀꜱᴇ ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴍʏ ᴏᴡɴᴇʀ ᴢᴇxᴏɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ ⚠️", show_alert=True)
        return
    if user_id not in user_yt_links:
        await callback_query.answer("Session expired Please send the YouTube link again.", show_alert=True)
        return
    url = user_yt_links[user_id]
    if data == "dl_audio":
        await callback_query.answer("Please wait Downloading...", show_alert=False)
        await client.send_chat_action(chat_id, ChatAction.TYPING)
        status_msg = await callback_query.message.reply_text("<b>𝐍ᴏᴡ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...⏳</b>")
        if not os.path.exists("downloads"): os.makedirs("downloads")
        file_path = None
        try:
            loop = asyncio.get_event_loop()
            def download_audio_with_cookie(use_cookie=False):
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': 'downloads/%(id)s.%(ext)s',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                }
                if use_cookie and os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3", info.get('title', 'Audio'), info.get('uploader', 'Unknown')
            try: file_path, title, uploader = await loop.run_in_executor(None, lambda: download_audio_with_cookie(use_cookie=False))
            except Exception: file_path, title, uploader = await loop.run_in_executor(None, lambda: download_audio_with_cookie(use_cookie=True))
            log_history(user, "AUDIO", title, url)
            await status_msg.edit_text("<b>𝐍ᴏᴡ ᴜᴘʟᴏᴀᴅɪɴɢ...⏳</b>")
            await client.send_chat_action(chat_id, ChatAction.UPLOAD_AUDIO)
            await client.send_audio(chat_id=chat_id, audio=file_path, title=title, performer=uploader, caption=f"<b>🎵 {title}</b>\n\n<b><blockquote>𝐏ᴏᴡᴇʀᴇᴅ : @zexon_You_tube_saver_Bot</blockquote></b>")
            await status_msg.delete()
        except Exception as e: await status_msg.edit_text(f"❌ **Audio Download Failed:** `{e}`")
        finally:
            if file_path and os.path.exists(file_path):
                try: os.remove(file_path)
                except Exception: pass
    elif data == "dl_video":
        await callback_query.answer("Please wait Downloading...", show_alert=False)
        await client.send_chat_action(chat_id, ChatAction.TYPING)
        status_msg = await callback_query.message.reply_text("<b>𝐍ᴏᴡ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...⏳</b>")
        if not os.path.exists("downloads"): os.makedirs("downloads")
        if "shorts" in url: strict_format = 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4] / best'
        else: strict_format = 'bv*[height<=480][ext=mp4]+ba[ext=m4a]/b[height<=480][ext=mp4] / best'
        formats_to_try = [strict_format, 'best']
        file_path = None; success = False; last_error = None; title = "Video"; duration = 0
        loop = asyncio.get_event_loop()
        for current_format in formats_to_try:
            for use_cookie in [False, True]:
                try:
                    def download_video():
                        ydl_opts = {'format': current_format,'outtmpl': 'downloads/%(id)s.%(ext)s','max_filesize': 500 * 1024 * 1024,'merge_output_format': 'mp4'}
                        if use_cookie and os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            return ydl.prepare_filename(info), info.get('title', 'Video'), info.get('duration', 0)
                    file_path, title, duration = await loop.run_in_executor(None, download_video)
                    success = True; break
                except Exception as e: last_error = e; continue
            if success: break
        if success and file_path:
            log_history(user, "VIDEO", title, url)
            try:
                await status_msg.edit_text("<b>𝐍ᴏᴡ ᴜᴘʟᴏᴀᴅɪɴɢ...⏳</b>")
                await client.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO)
                await client.send_video(chat_id=chat_id, video=file_path, caption=f"<b>{title}</b>\n\n<b><blockquote>𝐏ᴏᴡᴇʀᴇᴅ : @zexon_You_tube_saver_Bot</blockquote></b>", duration=duration, supports_streaming=True)
                await status_msg.delete()
            except Exception as e: await status_msg.edit_text(f"❌ **Upload Failed:** `{e}`")
            finally:
                if file_path and os.path.exists(file_path):
                    try: os.remove(file_path)
                    except Exception: pass
        else:
            await status_msg.edit_text(f"❌ **Video Download Failed:** `{last_error}`")
            if file_path and os.path.exists(file_path):
                try: os.remove(file_path)
                except Exception: pass

if __name__ == "__main__":
    print("YouTube Downloader Bot Running...")
    app.run()
