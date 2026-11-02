import asyncio
import gc
import json
import math
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.raw import types
import requests

# --- CONFIG ---
API_ID = 33208732
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "9091943258:AAH4QKu5MJ3Tg4ZTThBAUi7GR-xO6fl1BiQ"
ADMIN_ID = 8562470788

REQUIRED_CHANNEL = -1004334558910
CHANNEL_URL = "https://t.me/zexon_Bot_updates"

MEDIAFIRE_MAX_SIZE = 800* 1024 * 1024
DIRECT_MAX_SIZE = 800 * 1024 * 1024

REACTION_EMOJIS = ["🎉", "🥺", "😅", "⚡", "😊", "🙏", "🔥", "😍", "😘", "😐", "😌", "😃", "😂", "😭", "🙃", "🤭", "🤨", "😈", "👻", "👍"]

USERS_FILE = "users.json"
executor = ThreadPoolExecutor(max_workers=2)

USER_RENAME_STATES = {}
USER_COOLDOWNS = {}

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_users(s):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(s), f)
    except Exception:
        pass

users_set = load_users()
def add_user(uid):
    if uid not in users_set:
        users_set.add(uid)
        save_users(users_set)

def get_random_emoji():
    return random.choice(REACTION_EMOJIS)

def human_readable_size(b):
    if not b: return "0 MB"
    n = ("B", "KB", "MB", "GB")
    i = int(math.floor(math.log(b, 1024))) if b > 0 else 0
    p = math.pow(1024, i)
    return f"{round(b/p, 2)} MB" if i <= 2 else f"{round(b/p, 2)} GB"

def get_progress_bar(p):
    t = 16
    if p >= 99.5:
        return "▣" * t
    c = int((p / 100) * t)
    c = min(max(c, 0), t - 1)
    return "▣" * c + "▢" * (t - c)

def format_eta(seconds):
    if seconds <= 0:
        return "0 S"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{secs} S"

def safe_remove(p):
    try:
        if p and os.path.exists(p):
            os.remove(p)
    except Exception:
        pass
    finally:
        gc.collect()

async def check_join(client, user_id):
    try:
        member = await client.get_chat_member(REQUIRED_CHANNEL, user_id)
        if str(member.status) in ["ChatMemberStatus.MEMBER", "ChatMemberStatus.ADMINISTRATOR", "ChatMemberStatus.OWNER", "member", "administrator", "creator"]:
            return True
        return False
    except Exception:
        return False

def get_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join channel 💠", url=CHANNEL_URL)],
        [InlineKeyboardButton("Click to verify ✅", callback_data="check_joined")]
    ])

def extract_mediafire_link(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                btn = soup.find("a", id="downloadButton") or soup.find("a", class_=re.compile("input|download", re.I))
                if btn and btn.get("href"):
                    dlink = btn["href"]
                    if dlink.startswith("//"): dlink = "https:" + dlink
                    fname_div = soup.find("div", class_="filename")
                    fname = fname_div.text.strip() if fname_div else dlink.split("/")[-1].split("?")[0]
                    try:
                        h = requests.head(dlink, headers=headers, allow_redirects=True, timeout=20)
                        fsize = int(h.headers.get("content-length", 0))
                    except Exception: fsize = 0
                    return dlink, fsize, fname
        except Exception:
            time.sleep(2)
    return None, None, None

def extract_devuploads_link(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                data = {}
                for input_tag in soup.find_all("input"):
                    if input_tag.get("name"):
                        data[input_tag.get("name")] = input_tag.get("value", "")
                post_r = requests.post(url, data=data, headers=headers, timeout=30)
                if post_r.status_code == 200:
                    post_soup = BeautifulSoup(post_r.text, "html.parser")
                    download_btn = post_soup.find("a", class_="download-btn") or post_soup.find("a", id="downloadbtn")
                    if download_btn and download_btn.get("href"):
                        dlink = download_btn["href"]
                        fname = dlink.split("/")[-1].split("?")[0]
                        try:
                            h = requests.head(dlink, headers=headers, allow_redirects=True, timeout=20)
                            fsize = int(h.headers.get("content-length", 0))
                        except Exception: fsize = 0
                        return dlink, fsize, fname
        except Exception:
            time.sleep(2)
    return None, None, None

app = Client("zexon_url_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def react_user_message(message):
    try:
        emoji = get_random_emoji()
        await app.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=types.ReactionEmoji(emoticon=emoji))
    except Exception:
        pass

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    add_user(message.from_user.id)
    await react_user_message(message)

    if not await check_join(client, message.from_user.id):
        await message.reply_text("<b>ᴅᴇᴀʀ, ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴠᴇʀɪꜰʏ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ 🔐</b>", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
        return

    welcome_text = (
        f"<b>𝐇ᴇʟʟᴏ <code>{message.from_user.first_name}</code> !!</b>\n\n"
        "<blockquote><b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴜʀʟ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ ⎈</b></blockquote>\n"
        "<blockquote><i>ᴅᴇᴀʀ, ɪ ᴀᴍ ʏᴏᴜʀ ᴜʀʟ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ ᴅᴏᴡɴʟᴏᴀᴅ ᴀɴʏ ᴍᴀɢɴᴇᴛ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ ꜰʀᴏᴍ ᴅᴏᴄᴜᴍᴇɴᴛ ꜰɪʟᴇ ᴀɴᴅ ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ꜱᴀᴍᴇ ʟɪɴᴋ ᴍᴇᴅɪᴀ ꜰɪʀᴇ ᴅᴜᴘʟᴏᴀᴅ ɴᴇᴛ ᴀɴᴅ ᴍᴏʀᴇ, ᴛʜᴇ ꜱᴇɴᴅ ᴍᴇ ᴍᴇᴅɪᴀ ꜰɪʀᴇ ʟɪɴᴋ ᴀɴᴏᴛʜᴇʀ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ ᴀɴᴅ ɪ ᴡɪʟʟ ᴛʜɪꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀɴᴅ ꜱᴇɴᴅ ʏᴏᴜ ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ ɪɴꜱᴛᴀɴᴛʟʏ.</i></blockquote>\n"
        "<blockquote><b>ᴘʟᴇᴀꜱᴇ ꜱʜᴀʀᴇ ᴀɴᴅ ɢɪᴠᴇ ꜱᴜᴘᴘᴏʀᴛ ༗</b></blockquote>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇꜱ", url="https://t.me/zexon_Bot_updates")],
        [InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url="https://t.me/zexon_music_Bot"), InlineKeyboardButton("ʜᴇʟᴩ", url="https://t.me/zexon_x")],
        [InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="bot_close")],
    ])
    await message.reply_text(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex("check_joined"))
async def check_joined_cb(client, callback_query):
    uid = callback_query.from_user.id
    if await check_join(client, uid):
        try: await callback_query.message.delete()
        except Exception: pass
        await client.send_message(uid, "<b>ᴠᴇʀɪꜰɪᴇᴅ ɴᴏᴡ ᴄᴏɴᴛɪɴᴜᴇ 🎉</b>", parse_mode=ParseMode.HTML)
    else:
        await callback_query.answer("𝚈𝙾𝚄 𝙰𝚁𝙴 𝙽𝙾𝚃 𝙹𝙾𝙸𝙽𝙴𝙳 𝙼𝚈 𝙲𝙷𝙰𝙽𝙽𝙴𝙻, 𝙵𝙸𝚁𝚂𝚃 𝙹𝙾𝙸𝙽 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 𝚃𝙷𝙴𝙽 𝙲𝙻𝙸𝙲𝙺 𝚅𝙴𝚁𝙸𝙵𝙸𝙴𝙳 ❌", show_alert=True)

@app.on_callback_query(filters.regex("bot_close"))
async def close_cb(client, callback_query):
    try: await callback_query.message.delete()
    except Exception: pass

@app.on_message(filters.text & ~filters.command(["start"]))
async def process(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    local_file = None

    if user_id in USER_COOLDOWNS and time.time() < USER_COOLDOWNS[user_id]:
        remaining = int(USER_COOLDOWNS[user_id] - time.time())
        await message.reply_text(f"<b>Please wait <code>{remaining}s</code> before sending next request!</b>", parse_mode=ParseMode.HTML)
        return

    loop = asyncio.get_running_loop()

    if user_id in USER_RENAME_STATES:
        link_data = USER_RENAME_STATES.pop(user_id)
        original_url = link_data["url"]
        is_mf = link_data["is_mf"]
        is_dev = link_data["is_dev"]
        dlink = link_data.get("dlink")
        fsize = link_data.get("fsize", 0)
        oname = link_data.get("fname", "downloaded_document.bin")
        prompt_id = link_data.get("prompt_msg_id")
        user_msg_id = link_data.get("user_msg_id")
        chat_id = message.chat.id

        if prompt_id:
            try: await client.delete_messages(chat_id=chat_id, message_ids=[prompt_id])
            except Exception: pass
        try: await client.delete_messages(chat_id=chat_id, message_ids=[message.id])
        except Exception: pass

        status_msg = await client.send_message(chat_id, "𝐏ʀᴏꜱᴇꜱꜱɪɴɢ...⏳", parse_mode=ParseMode.HTML, reply_to_message_id=user_msg_id)
        await asyncio.sleep(2)

        try:
            if not dlink:
                if is_mf:
                    dlink, fsize, oname = await loop.run_in_executor(executor, extract_mediafire_link, original_url)
                elif is_dev:
                    dlink, fsize, oname = await loop.run_in_executor(executor, extract_devuploads_link, original_url)
                else:
                    dlink = original_url

            if not dlink:
                await status_msg.edit_text("The Download Failed ❌", parse_mode=ParseMode.HTML)
                return

            local_file = f"{user_id}_{int(time.time())}_{oname}"
            new_name = text
            if "." not in new_name:
                ext = os.path.splitext(oname)[1]
                new_name = new_name + ext

            def dl_file():
                downloaded = 0
                start = time.time()
                last = [0]
                headers = {"User-Agent": "Mozilla/5.0"}
                with requests.get(dlink, headers=headers, stream=True, timeout=1200) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("content-length", 0)) or fsize or 0
                    with open(local_file, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1 * 1024 * 1024):
                            if not chunk: continue
                            f.write(chunk)
                            downloaded += len(chunk)
                            now = time.time()
                            is_complete = (downloaded >= total and total > 0)
                            if total > 0 and (now - last[0] > 10.0 or is_complete):
                                last[0] = now
                                percent = 100.0 if is_complete else ((downloaded / total) * 100)
                                speed = downloaded / (now - start + 0.001)
                                eta = 0 if is_complete else (total - downloaded) / speed if speed > 0 else 0
                                bar = get_progress_bar(percent)
                                txt = (
                                     f"<b><i>𝐌ᴇᴅɪᴀ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ :</i></b>\n\n"
                                     f"<code>{bar}</code>\n\n"
                                     f"<blockquote>💾 Size : {human_readable_size(total)}\n"
                                     f"📦 Done : {human_readable_size(downloaded)}\n"
                                     f"⚙️ Speed : {human_readable_size(speed)}\n"
                                     f"⏰ Left Eta : {format_eta(eta)}</blockquote>\n\n"
                                     f"<blockquote><b> 𝐓ʜᴀɴᴋꜱ :</b> @URL_Uploadex_Bot </blockquote>"
                                )
                                try:
                                    fut = asyncio.run_coroutine_threadsafe(status_msg.edit_text(txt, parse_mode=ParseMode.HTML), loop)
                                    fut.result(timeout=3)
                                except Exception: pass

            await loop.run_in_executor(executor, dl_file)

            new_file_path = os.path.join(os.path.dirname(local_file) or ".", new_name)
            os.rename(local_file, new_file_path)

            await status_msg.edit_text("<b><i>𝐏ʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴜᴘʟᴏᴀᴅɪɴɢ...</i></b>", parse_mode=ParseMode.HTML)
            await asyncio.sleep(1)

            upload_start = [time.time()]
            last_up = [0]

            async def upload_progress(current, total):
                now = time.time()
                is_complete = (current >= total and total > 0)
                percent = 100.0 if is_complete else ((current / total) * 100 if total > 0 else 0)
                if not is_complete and (now - last_up[0] < 10.0): return
                last_up[0] = now
                speed = current / (now - upload_start[0] + 0.001)
                eta = 0 if is_complete else ((total - current) / speed if speed > 0 else 0)
                bar = get_progress_bar(percent)
                txt = (
                    f"<b><i>𝐌ᴇᴅɪᴀ ᴜᴘʟᴏᴀᴅɪɴɢ :</i></b>\n\n"
                    f"<code>{bar}</code>\n\n"
                    f"<blockquote>💾 Size : {human_readable_size(total)}\n"
                    f"📦 Done : {human_readable_size(current)}\n"
                    f"⚙️ Speed : {human_readable_size(speed)}\n"
                    f"⏰ Left Eta : {format_eta(eta)}</blockquote>\n\n"
                    f"<blockquote><b>𝐓ʜᴀɴᴋꜱ : @URL_Uploadex_Bot </blockquote>"
                )
                try: await status_msg.edit_text(txt, parse_mode=ParseMode.HTML)
                except Exception: pass

            await client.send_document(
                chat_id=message.chat.id,
                document=new_file_path,
                file_name=new_name,
                progress=upload_progress,
                force_document=True,
                reply_to_message_id=user_msg_id
            )

            try: await status_msg.delete()
            except Exception: pass

            USER_COOLDOWNS[user_id] = time.time() + 30
            await client.send_message(chat_id, "<b>ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ ᴍᴇ 😊</b>", parse_mode=ParseMode.HTML)

        except Exception as e:
            try: await status_msg.edit_text(f"❌ Error: <code>{str(e)}</code>", parse_mode=ParseMode.HTML)
            except Exception: pass
        finally:
            safe_remove(local_file)
            if 'new_file_path' in locals():
                safe_remove(new_file_path)
            gc.collect()
        return

    add_user(user_id)
    await react_user_message(message)
    if not await check_join(client, user_id):
        await message.reply_text("<b>ᴅᴇᴀʀ, ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴠᴇʀɪꜰʏ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ 🤨</b>", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
        return

    is_mf = "mediafire.com" in text
    is_dev = "devuploads.com" in text

    if is_mf or is_dev:
        proc_msg = await message.reply_text("𝐏ʀᴏꜱᴇꜱꜱɪɴɢ...⏳", parse_mode=ParseMode.HTML, reply_to_message_id=message.id)
        await asyncio.sleep(2)
        if is_mf:
            dlink, fsize, fname = await loop.run_in_executor(executor, extract_mediafire_link, text)
        else:
            dlink, fsize, fname = await loop.run_in_executor(executor, extract_devuploads_link, text)

        if not dlink:
            await proc_msg.edit_text("<b>This Link Expired ❌</b>", parse_mode=ParseMode.HTML)
            return

        USER_RENAME_STATES[user_id] = {
            "url": text, "dlink": dlink, "fsize": fsize, "fname": fname,
            "is_mf": is_mf, "is_dev": is_dev, "prompt_msg_id": proc_msg.id, "user_msg_id": message.id
        }

        txt = (
            f"<b>𝐅ɪʟᴇ 𝐍ᴀᴍᴇ :</b> <code>{fname}</code>\n"
            f"<b>ꜱɪᴢᴇ :</b> <code>{human_readable_size(fsize)}</code>\n\n"
            f"<b>𝐍ᴏᴡ ꜱᴇɴᴅ ᴍᴇ ɴᴇᴡ ɴᴀᴍᴇ</b>"
        )
        await proc_msg.edit_text(txt, parse_mode=ParseMode.HTML)
        return

    if text.startswith("http://") or text.startswith("https://"):
        proc_msg = await message.reply_text("𝐏ʀᴏꜱᴇꜱꜱɪɴɢ...⏳", parse_mode=ParseMode.HTML, reply_to_message_id=message.id)
        try:
            head_r = requests.head(text, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=20)
            fsize = int(head_r.headers.get("content-length", 0))
        except Exception:
            fsize = 0

        fname = text.split("/")[-1].split("?")[0]
        if not fname or "." not in fname:
            fname = "downloaded_document.bin"

        USER_RENAME_STATES[user_id] = {
            "url": text, "dlink": text, "fsize": fsize, "fname": fname,
            "is_mf": False, "is_dev": False, "prompt_msg_id": proc_msg.id, "user_msg_id": message.id
        }

        txt = (
            f"<b>𝐅ɪʟᴇ 𝐍ᴀᴍᴇ :</b> <code>{fname}</code>\n"
            f"<b>ꜱɪᴢᴇ :</b> <code>{human_readable_size(fsize)}</code>\n\n"
            f"<b>𝐍ᴏᴡ ꜱᴇɴᴅ ᴍᴇ ɴᴇᴡ ɴᴀᴍᴇ </b>"
        )
        await proc_msg.edit_text(txt, parse_mode=ParseMode.HTML)
        return
    else:
        await message.reply_text("<b>Please send a valid MediaFire, Devuploads, or Direct File Link! ❌</b>", parse_mode=ParseMode.HTML)

if __name__ == "__main__":
    print("URL Uploader Bot Starting Successfully")
    app.run()
