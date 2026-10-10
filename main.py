import os, re, asyncio, time
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
from mega import Mega
import gdown

API_ID = "33208732"
API_HASH = "HASH"
BOT_TOKEN = "BOT TOKEN"

app = Client("zexon_uploader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User ka data yaad rakhne ke liye
user_data = {}

# Link pehchanne ke liye
def get_link_type(url):
    if "mediafire.com" in url: return "mediafire"
    if "mega.nz" in url or "mega.co.nz" in url: return "mega"
    if "drive.google.com" in url: return "gdrive"
    return "direct"

async def download_with_ytdlp(url, custom_name):
    ydl_opts = {
        'outtmpl': f'downloads/{custom_name}',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    # Mediafire / Gdrive ke liye yt-dlp best hai
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info) if 'entries' not in info else f"downloads/{custom_name}"

@app.on_message(filters.private & filters.text)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Step 2: Agar user ne rename bhej diya hai
    if user_id in user_data and user_data[user_id].get("waiting_for_name"):
        link = user_data[user_id]["link"]
        new_name = text
        ask_msg_id = user_data[user_id]["ask_msg_id"]

        # Request aur Send me new name wala msg delete
        try:
            await client.delete_messages(message.chat.id, [message.id, ask_msg_id])
        except: pass

        user_data[user_id]["waiting_for_name"] = False

        status = await message.reply_text(f"📥 **Downloading...**\n`{new_name}`")

        try:
            os.makedirs("downloads", exist_ok=True)
            file_path = f"downloads/{new_name}"

            link_type = get_link_type(link)

            if link_type == "mega":
                mega = Mega()
                m = mega.login() # anonymous
                m.download_url(link, dest_path="downloads", dest_filename=new_name)
            elif link_type == "gdrive":
                # GDrive ID nikalna
                file_id = re.findall(r'/d/([a-zA-Z0-9-_]+)', link)
                if file_id:
                    gdown.download(id=file_id[0], output=file_path, quiet=False)
                else:
                    gdown.download(url=link, output=file_path, quiet=False)
            else: # mediafire + direct
                await download_with_ytdlp(link, new_name)

            await status.edit_text("📤 **Uploading to Telegram...**")

            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=f"✅ **Uploaded:** `{new_name}`\nBy @zexon_x",
                force_document=True
            )
            os.remove(file_path)
            await status.delete()

        except Exception as e:
            await status.edit_text(f"❌ Error: `{e}`")

        user_data.pop(user_id, None)
        return

    # Step 1: Nayi Link aayi hai
    if "http" in text:
        user_data[user_id] = {"link": text, "waiting_for_name": True}
        ask_msg = await message.reply_text(
            "✏️ **Send me new name**\n\nJaise: `my_movie.mkv`"
        )
        user_data[user_id]["ask_msg_id"] = ask_msg.id

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Namaste MR ZEXON! 👋\n\nMain **All-in-One Uploader** hoon.\nMediaFire / MEGA / G-Drive ki link bhejo, main rename karke upload kar dunga.\n\nJust send link!"
    )

print("ZEXON Uploader Started...")
app.run()
