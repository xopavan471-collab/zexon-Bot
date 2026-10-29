import asyncio
import os
import time
import gc
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified, FloodWait

API_ID = 33208732  
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "8830089254:AAEA5XwunZpRRsJj76foeBbwjY33zsNQUKs"
ADMIN_ID = 8562470788  

app = Client(
    "zexon_renamer_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    workdir="./",
    workers=32,
    max_concurrent_transmissions=20,
    ipv6=False
)

user_data = {}
registered_users = set()
total_renamed_files = 0

def humanbytes(size):
    if not size: 
        return "0.00"
    return f"{size / (1024*1024):.2f}"

def stylish_number(text):
    m = {'0':'𝟶','1':'𝟷','2':'𝟸','3':'𝟹','4':'𝟺','5':'𝟻','6':'𝟼','7':'𝟽','8':'𝟾','9':'𝟿','.':'.', '%':'%'}
    return ''.join(m.get(c, c) for c in str(text))

async def progress_for_pyrogram(current, total, status_message, start_time, action_type, last_edit_holder):
    now = time.time()
    
    # 2 sec cooldown
    if (now - last_edit_holder["time"] < 2.0) and current != total:
        return
        
    last_edit_holder["time"] = now
    diff = now - start_time
    if diff <= 0: 
        diff = 1
        
    percentage = (current * 100 / total) if total and total > 0 else 0
    speed = current / diff
    
    if speed > 0:
        eta = int((total - current) / speed)
    else:
        eta = 0

    filled = min(14, int(percentage * 14 / 100))
    bar = "▣" * filled + "▢" * (14 - filled)
    head = "<b>ꜱᴛᴀᴛᴜꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ :</b>\n" if "Download" in action_type else "<b>ꜱᴛᴀᴛᴜꜱ ᴜᴘʟᴏᴀᴅɪɴɢ :</b>\n"
    
    text = (
        f"{head}\n{bar}\n\n"
        f"<blockquote><b>ꜱɪᴢxᴇ :</b> {stylish_number(humanbytes(total))} ᴍʙ\n"
        f"<b>ᴅᴏɴᴇ :</b> {stylish_number(humanbytes(current))} ᴍʙ\n"
        f"<b>ꜱᴘᴇᴇᴅ :</b> {stylish_number(humanbytes(speed))} ᴍʙ\n"
        f"<b>ʟᴇꜰᴛ ᴇᴛᴀ :</b> {stylish_number(eta)} ꜱ</blockquote>\n\n<blockquote><b>𝐓ʜᴀɴᴋꜱ :</b> @Rename_zexon_Bot</blockquote>"
    )

    # MAIN FIX - Same text ko edit karne se rokega
    if last_edit_holder.get("last_text") == text:
        return
    last_edit_holder["last_text"] = text

    try: 
        await status_message.edit_text(text)
    except MessageNotModified:
        pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception: 
        pass

START_TEXT = (
    "<b>𝐇ɪ {name}</b>\n\n"
    "<blockquote><b>𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ 𝐀ᴅᴠᴀɴᴄᴇ 𝐑ᴇɴᴀᴍᴇ 𝐁ᴏᴛ</b></blockquote>\n"
    "<blockquote><i>ᴡᴇ ᴀʀᴇ ᴀᴅᴠᴀɴᴄᴇ ᴀɴᴅ ᴀʟᴍᴏꜱᴛ ꜰᴀꜱᴛ ꜰɪʟᴇ ʀᴇɴᴀᴍᴇ ʙᴏᴛ ᴡɪᴛʜ ʟᴀʀɢᴇʀ ꜱɪᴢᴇ ꜱᴜᴘᴘᴏʀᴛ ꜰɪʟᴇ ᴍᴀxɪᴍᴜᴍ ꜰɪᴠᴇ ʜᴜɴᴅʀᴇᴅ, ᴡᴇ ᴄᴀɴ ꜰᴀꜱᴛ ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ꜰɪʟᴇ, ɪꜰ ʏᴏᴜ ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ꜰɪʟᴇ ᴛʜᴇɴ ꜱᴇɴᴅ ᴍᴇ ɴᴇᴡ ɴᴀᴍᴇ ᴏꜰ ʏᴏᴜʀ ꜰɪʟᴇ ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ ʀᴇɴᴀᴍᴇᴅ ꜰɪʟᴇ ɪɴꜱᴛᴀɴᴛʟʏ.</i></blockquote>\n"
    "<blockquote><b>ᴛʜᴇ ᴍᴀɪɴᴛᴇɴᴇᴅ ʙʏ : ᴢᴇxᴏɴ ᴘᴀᴠᴀɴ</b></blockquote>"
)

START_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇꜱ", url="https://t.me/zexon_Bot_updates"), InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url="https://t.me/zexon_music_Bot")],
    [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/zexon_x")],
    [InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about_btn"), InlineKeyboardButton("ʜᴇʟᴘ", callback_data="help_btn")],
    [InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="close_btn")]
])

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    registered_users.add(message.from_user.id)
    await message.reply_text(text=START_TEXT.format(name=message.from_user.first_name), reply_markup=START_KEYBOARD, disable_web_page_preview=True, quote=True)

@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    try:
        if data == "about_btn":
            about_text = "╭━━━━━━━━━━━━━━━━━➣\n┣⪼ <b><u>ʜᴇʀᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ</u></b>\n┣⪼ ɴᴀᴍᴇ : ʀᴇɴᴀᴍᴇʀ ᴢᴇxᴏɴ ʙᴏᴛ\n┣⪼ ʜᴏᴍᴇ : ꜱɪʟʟʏ ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ\n┣⪼ ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ ᴇɴɢʟɪꜱʜ\n┣⪼ ᴛʜᴇ god : ᴍʀ ᴢᴇxᴏɴ ᴘᴀᴠᴀɴ\n┣⪼ ʜᴇʟᴘ ᴄᴏɴɴᴇᴄᴛ : @zexon_x\n╰━━━━━━━━━━━━━━━━━➣"
            await callback_query.message.edit_text(text=about_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_btn")]]))
        elif data == "help_btn":
            help_text = "<b><u>ʜᴏᴡ ᴛᴏ ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ꜰɪʟᴇ :</u></b>\n𝟷. ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ᴀɴʏ ꜰɪʟᴇ\n𝟸. ᴛʜᴇɴ ꜱᴇɴᴅ ᴍᴇ ɴᴇᴡ ɴᴀᴍᴇ\n𝟹. ᴡᴀɪᴛ ꜱᴀᴍᴇ ᴛɪᴍᴇ ꜰᴏʀ ʀᴇɴᴀᴍɪɴɢ\n𝟺. ᴘʟᴇᴀꜱᴇ ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʙɪɢ ꜰɪʟᴇ"
            await callback_query.message.edit_text(text=help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_btn")]]))
        elif data == "main_menu" or data == "back_btn":
            await callback_query.message.edit_text(text=START_TEXT.format(name=callback_query.from_user.first_name), reply_markup=START_KEYBOARD, disable_web_page_preview=True)
        elif data == "close_btn":
            await callback_query.message.delete()
    except MessageNotModified:
        pass
    except Exception:
        pass

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def bot_status(client: Client, message: Message):
    await message.reply_text(f"📊 **Bot Live Status**\n\n👥 **Total Users:** `{len(registered_users)}`\n📁 **Total Renamed:** `{total_renamed_files}`", quote=True)

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client: Client, message: Message):
    file = message.document or message.video or message.audio
    registered_users.add(message.from_user.id)
    max_limit = 1000 * 1024 * 1024
    if (file.file_size or 0) > max_limit:
        await message.reply_text("Big File Can't Download ⚠️", quote=True)
        return
    original_name = file.file_name or "unknown_file"
    _, ext = os.path.splitext(original_name)
    
    analysing_msg = await message.reply_text("<b>𝐏ʀᴏꜱᴇꜱꜱɪɴɢ...</b>", quote=True)
    await asyncio.sleep(1)
    try:
        info_msg = await analysing_msg.edit_text(f"<blockquote><b>𝐅ɪʟᴇ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ  :</b>\n<b> ɴᴀᴍᴇ :</b> <code>{original_name}</code>\n<b> ꜰɪʟᴇ ꜱɪᴢᴇ :</b> {stylish_number(humanbytes(file.file_size))} ᴍʙ</blockquote>\n<blockquote> <i><b>𝐍ᴏᴡ ꜱᴇɴᴅ ᴍᴇ  ɴᴇᴡ  ɴᴀᴍᴇ </b></i></blockquote>")
    except:
        info_msg = analysing_msg

    user_data[message.from_user.id] = {"media_message": message, "ext": ext, "info_msg": info_msg}

@app.on_message(filters.text & ~filters.command(["start", "status"]))
async def handle_new_name(client: Client, message: Message):
    global total_renamed_files
    user_id = message.from_user.id
    if user_id not in user_data:
        return
    data = user_data.pop(user_id)
    media_msg = data["media_message"]
    ext = data["ext"]
    info_msg = data["info_msg"]
    new_name = message.text.strip()
    if not new_name.endswith(ext):
        new_name += ext

    status_msg = await media_msg.reply_text("<b>𝐏ʀᴏꜱᴇꜱꜱɪɴɢ...</b>", quote=True)
    
    try: await message.delete()
    except: pass
    try: await info_msg.delete()
    except: pass
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    start_time = time.time()
    last_edit = {"time": start_time, "last_text": ""}
    
    file_path = None
    try:
        file_path = await media_msg.download(file_name=f"downloads/{new_name}", progress=progress_for_pyrogram, progress_args=(status_msg, start_time, "Download", last_edit))
    except Exception as e:
        await status_msg.edit_text(f"❌ Download failed: {e}")
        return

    try: await status_msg.edit_text("<b><i>𝐏ʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴜᴘʟᴏᴀᴅɪɴɢ...</i></b>")
    except: pass
    await asyncio.sleep(1)
    
    start_time = time.time()
    last_edit["time"] = 0
    last_edit["last_text"] = ""
    
    try:
        sent_doc = await media_msg.reply_document(document=file_path, file_name=new_name, force_document=True, progress=progress_for_pyrogram, progress_args=(status_msg, start_time, "Upload", last_edit), quote=True)
    except Exception as e:
        try: await status_msg.edit_text(f"❌ Upload failed: {e}")
        except: pass
        return
    finally:
        try: await status_msg.delete()
        except: pass
        if file_path and os.path.exists(file_path): 
            try: os.remove(file_path)
            except: pass
        gc.collect()
        
    total_renamed_files += 1

if __name__ == "__main__":
    print("Bot Running Perfectly...")
    app.run()
