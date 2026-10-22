from __future__ import annotations
import asyncio, json, logging, os, re, sqlite3, tempfile, time, requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs
from yt_dlp import YoutubeDL

TOKEN = "8986816218:AAHnfkyvQtaV_N_GaPa738zCqeFZuHzFkxU"
MAX_AUDIO_BYTES = 49_000_000
DOWNLOAD_TIMEOUT_SECONDS = 45
USER_DB_PATH = Path(os.environ.get("USER_DB_PATH", "bot_users.sqlite3"))
SUPPORTED_HOSTS = ("youtube.com","youtu.be","instagram.com","facebook.com","fb.watch",)
LAST_URLS: dict[int, str] = {}

def parse_admin_ids() -> set[int]:
    admin_ids: set[int] = set()
    for value in os.environ.get("ADMIN_USER_IDS", "").split(","):
        value = value.strip()
        if value.lstrip("-").isdigit(): admin_ids.add(int(value))
    return admin_ids

ADMIN_USER_IDS = parse_admin_ids() or {8562470788}

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=os.environ.get("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("zexon-music-bot")

def init_user_store() -> None:
    with sqlite3.connect(USER_DB_PATH) as c:
        c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT NOT NULL DEFAULT '', first_name TEXT NOT NULL DEFAULT '', last_name TEXT NOT NULL DEFAULT '', language_code TEXT NOT NULL DEFAULT '', first_seen_at INTEGER NOT NULL, last_activity_at INTEGER NOT NULL, download_count INTEGER NOT NULL DEFAULT 0)")

def record_user(user: dict[str, Any], download: bool = False) -> None:
    user_id = user.get("id")
    if not isinstance(user_id, int): return
    now = int(time.time())
    with sqlite3.connect(USER_DB_PATH) as c:
        c.execute("INSERT INTO users (user_id, username, first_name, last_name, language_code, first_seen_at, last_activity_at, download_count) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=CASE WHEN excluded.username<>'' THEN excluded.username ELSE users.username END, first_name=CASE WHEN excluded.first_name<>'' THEN excluded.first_name ELSE users.first_name END, last_name=CASE WHEN excluded.last_name<>'' THEN excluded.last_name ELSE users.last_name END, language_code=CASE WHEN excluded.language_code<>'' THEN excluded.language_code ELSE users.language_code END, last_activity_at=excluded.last_activity_at, download_count=users.download_count+excluded.download_count",
        (user_id, str(user.get("username") or ""), str(user.get("first_name") or ""), str(user.get("last_name") or ""), str(user.get("language_code") or ""), now, now, 1 if download else 0))

def safe_record_user(user: dict[str, Any], download: bool = False) -> None:
    try: record_user(user, download)
    except sqlite3.Error: logger.exception("DB fail")

def format_user_time(timestamp: int) -> str: return datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def get_bot_stats() -> tuple[int, int]:
    try:
        with sqlite3.connect(USER_DB_PATH) as c:
            cur1 = c.execute("SELECT COUNT(*) FROM users")
            total_users = cur1.fetchone()[0] or 0
            cur2 = c.execute("SELECT SUM(download_count) FROM users")
            total_downloads = cur2.fetchone()[0] or 0
            return total_users, total_downloads
    except sqlite3.Error:
        logger.exception("DB stats fail")
        return 0, 0

def is_supported_url(value: str) -> bool:
    try: parsed=urlparse(value)
    except ValueError: return False
    hostname=(parsed.hostname or "").lower().removeprefix("www.")
    return parsed.scheme in {"http","https"} and any(hostname==h or hostname.endswith(f".{h}") for h in SUPPORTED_HOSTS)

def is_youtube_url(value: str) -> bool:
    try: hostname=(urlparse(value).hostname or "").lower().removeprefix("www.")
    except ValueError: return False
    return hostname=="youtube.com" or hostname.endswith(".youtube.com") or hostname=="youtu.be"

def clean_filename(value: str, fallback: str = "audio") -> str:
    cleaned=re.sub(r"[^\w\s.-]","",value,flags=re.UNICODE); cleaned=re.sub(r"\s+"," ",cleaned).strip(); return cleaned[:100] or fallback

def get_youtube_id(url: str) -> str | None:
    try:
        parsed=urlparse(url)
        hostname=(parsed.hostname or "").lower().removeprefix("www.")
        if "youtu.be" in hostname: return parsed.path.lstrip("/").split("?")[0].split("&")[0][:11]
        qs=parse_qs(parsed.query)
        if "v" in qs: return qs["v"][0][:11]
        m=re.search(r"/(?:shorts|embed|watch)/([^/?&]+)", parsed.path)
        if m: return m.group(1)[:11]
    except Exception: pass
    m = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return m.group(1) if m else None

def extract_thumbnail(url: str) -> tuple[str | None, str]:
    options={"quiet":True,"no_warnings":True,"skip_download":True,"noplaylist":True,"socket_timeout":DOWNLOAD_TIMEOUT_SECONDS}
    title = "Thumbnail"
    thumbnail = None
    try:
        with YoutubeDL(options) as ydl:
            info=ydl.extract_info(url, download=False)
            title = info.get("title") or "Thumbnail"
            thumbnail = info.get("thumbnail")
    except Exception:
        pass

    if not thumbnail and is_youtube_url(url):
        vid=get_youtube_id(url)
        if vid:
            thumbnail = f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"

    return thumbnail, title

def download_audio(url: str, directory: str) -> tuple[Path, str]:
    hdr = {"User-Agent": "Mozilla/5.0"}
    if is_youtube_url(url):
        video_id = get_youtube_id(url)
        if not video_id: raise ValueError("invalid_youtube_url")
        for server in ["https://pipedapi.kavin.rocks", "https://api.piped.private.coffee", "https://pipedapi.adminforge.de"]:
            try:
                res = requests.get(f"{server}/streams/{video_id}", headers=hdr, timeout=20)
                if res.status_code!= 200: continue
                data = res.json()
                streams = data.get("audioStreams", [])
                if not streams: continue
                title = data.get("title", "audio")[:80]
                best = sorted(streams, key=lambda x: x.get('bitrate',0), reverse=True)[0]
                dl_url = best.get("url")
                if not dl_url: continue
                safe_name = clean_filename(title, video_id)
                path = Path(directory) / f"{safe_name}.mp3"
                with requests.get(dl_url, headers=hdr, stream=True, timeout=60) as dl:
                    with open(path, 'wb') as f:
                        for chunk in dl.iter_content(8192): f.write(chunk)
                if path.stat().st_size > 5000:
                    return path, title
            except Exception as e:
                logger.warning(f"Piped fail {server}: {e}")

    for client_name in ["android", "ios", "mweb", "web"]:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(directory, "%(title).80s.%(ext)s"),
                "noplaylist": True, "restrictfilenames": False, "quiet": True, "no_warnings": True,
                "socket_timeout": DOWNLOAD_TIMEOUT_SECONDS, "nocheckcertificate": True,
                "extractor_args": {"youtube": {"player_client": [client_name]}} if is_youtube_url(url) else {},
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title") or "audio"
                mp3s = list(Path(directory).glob("*.mp3"))
                if not mp3s: mp3s = list(Path(directory).glob("*.*"))
                if mp3s:
                    audio_path = mp3s[0]
                    if audio_path.suffix!= ".mp3":
                        new_path = audio_path.with_suffix(".mp3")
                        audio_path.rename(new_path)
                        audio_path = new_path
                    if audio_path.stat().st_size > MAX_AUDIO_BYTES: raise ValueError("audio_too_large")
                    return audio_path, title
        except Exception as e:
            logger.warning(f"yt-dlp {client_name} fail: {e}")
            continue
    raise ValueError("this link can't download")

class TelegramAPIError(RuntimeError): pass

async def telegram_request(client: Any, method: str, data: dict[str, Any] | None = None, files: dict[str, Any] | None = None, timeout: float = 40) -> Any:
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    proxies = {
        "http": "http://proxy.server:3128",
        "https": "http://proxy.server:3128"
    }

    def _do_post():
        for attempt in range(3):
            try:
                response = requests.post(url, data=data, files=files, timeout=timeout, proxies=proxies)
                return response.json()
            except Exception as e:
                if attempt == 2:
                    return {"ok": False, "description": str(e)}
                time.sleep(2)

    payload = await asyncio.to_thread(_do_post)
    if not payload.get("ok"): raise TelegramAPIError(f"{method}: {payload.get('description')}")
    return payload.get("result")

async def send_message(client: Any, chat_id: int, text: str, keyboard=None) -> Any:
    data={"chat_id":str(chat_id),"text":text,"parse_mode":"HTML"}
    if keyboard: data["reply_markup"]=json.dumps({"inline_keyboard":keyboard},ensure_ascii=False)
    return await telegram_request(client,"sendMessage",data=data)

async def edit_message(client: Any, chat_id: int, message_id: int, text: str, keyboard=None) -> None:
    data={"chat_id":str(chat_id),"message_id":str(message_id),"text":text,"parse_mode":"HTML"}
    if keyboard: data["reply_markup"]=json.dumps({"inline_keyboard":keyboard},ensure_ascii=False)
    try: await telegram_request(client,"editMessageText",data=data)
    except TelegramAPIError: pass

async def delete_message(client: Any, chat_id: int, message_id: int) -> None:
    try: await telegram_request(client,"deleteMessage",data={"chat_id":str(chat_id),"message_id":str(message_id)})
    except TelegramAPIError: pass

async def answer_callback(client: Any, callback_id: str) -> None:
    try: await telegram_request(client,"answerCallbackQuery",data={"callback_query_id":callback_id})
    except TelegramAPIError: pass

async def send_photo(client: Any, chat_id: int, photo: str) -> Any:
    return await telegram_request(client,"sendPhoto",data={"chat_id":str(chat_id),"photo":photo})

async def send_audio(client: Any, chat_id: int, audio_path: Path, title: str) -> Any:
    with audio_path.open("rb") as f:
        safe_title = clean_filename(title)
        return await telegram_request(
            client,
            "sendAudio",
            data={
                "chat_id": str(chat_id),
                "title": safe_title
            },
            files={"audio": (f"{safe_title}.mp3", f, "audio/mpeg")},
            timeout=75
        )

def start_keyboard():
    return [
        [{"text":"ᴜᴘᴅᴀᴛᴇꜱ","url":"https://t.me/zexon_Bot_updates"},{"text":"ꜱᴜᴘᴘᴏʀᴛ","url":"https://t.me/URL_Save_Bot"}],
        [{"text":"ᴀʙᴏᴜᴛ","callback_data":"about"},{"text":"ꜱʜᴀʀᴇ","url":"https://t.me/zexon_music_Bot"}],
        [{"text":"ᴅᴇᴠᴇʟᴏᴘᴇʀ","url":"https://t.me/zexon_x"}],
        [{"text":"ᴄʟᴏꜱᴇ","callback_data":"close"}]
    ]

def back_keyboard():
    return [[{"text":"🔙 ʙᴀᴄᴋ","callback_data":"home"}]]

async def handle_start(client: Any, chat_id: int, first_name: str) -> None:
    await send_message(client,chat_id,
        f"<b>𝐇ɪ, {first_name} ✨</b> \n\n"
        "<i>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ɪɴꜱᴛᴀɢʀᴀᴍ ꜰᴀᴄᴇʙᴏᴋ ᴍᴜꜱɪᴄ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴏᴛ.</i>\n"
        "<i>ᴡᴇ ᴄᴀɴ ꜱᴀᴠᴇ ᴍᴜꜱɪᴄ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ꜰᴏʀᴍ ɪɴꜱᴛᴀɢʀᴀᴍ ꜰᴀᴄᴇʙᴏᴏᴋ ꜱᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ</i>\n"
        "<i>ɪꜰ ʏᴏᴜ ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ʟɪɴᴋ ᴀɴᴅ ɢᴇᴛ ᴍᴜꜱɪᴄ ᴛʜᴜᴍʙɴᴀɪʟ ꜰᴀꜱᴛ ꜱᴇᴄᴜʀᴇ ɪɴꜱᴛᴀɴᴛʟʏ</i>\n\n"
        "ꜱᴛʏʟɪꜱʜ ᴍᴀɪɴᴛᴇɴᴇᴅ : ᴢᴇxᴏɴ",
        keyboard=start_keyboard())

async def handle_stats(client: Any, chat_id: int, user_id: int) -> None:
    if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
        return
    total_users, total_downloads = get_bot_stats()
    stats_text = (
        "📊 <b><u>The About users :</u></b>\n\n"
        f"• <b>Total Users :</b> <code>{total_users}</code>\n"
        f"• <b>Total Downloads :</b> <code>{total_downloads}</code>"
    )
    await send_message(client, chat_id, stats_text)

async def handle_message(client: Any, message: dict[str, Any]) -> None:
    chat=message.get("chat",{}); chat_id=chat.get("id"); text=(message.get("text") or "").strip()
    if not isinstance(chat_id,int) or not text: return
    sender=message.get("from") or {}
    if isinstance(sender,dict): await asyncio.to_thread(safe_record_user,sender)
    command=text.split(maxsplit=1)[0].split("@",1)[0].lower()

    if command=="/start":
        await handle_start(client,chat_id,(sender.get("first_name") if isinstance(sender,dict) else None) or "दोस्त")
        return
    if command in ["/stats", "/status", "/users"]:
        sender_id = sender.get("id") if isinstance(sender, dict) else 0
        await handle_stats(client, chat_id, sender_id)
        return

    if not is_supported_url(text): await send_message(client,chat_id,"<i>𝑫𝒆𝒂𝒓, 𝒔𝒆𝒏𝒅 𝒎𝒆 𝒚𝒐𝒖 𝒕𝒖𝒃𝒆 𝑰𝒏𝒔𝒕𝒂𝒈𝒓𝒂𝒎 𝑭𝒂𝒄𝒆𝒃𝒐𝒐𝒌 𝑳𝒊𝒏𝒌 🔗</i>"); return
    LAST_URLS[chat_id]=text
    await send_message(client,chat_id,"<b>𝐒ᴇʟᴇᴄᴛ 𝐅ᴏʀᴍᴀᴛ :</b>\n",keyboard=[[{"text":"𝐀ᴜᴅɪᴏ 🎵","callback_data":"music"},{"text":"𝐓ʜᴜᴍʙɴᴀɪʟ 🖼️","callback_data":"thumb"}]])

async def handle_callback(client: Any, callback: dict[str, Any]) -> None:
    callback_user=callback.get("from") or {}
    if isinstance(callback_user,dict): await asyncio.to_thread(safe_record_user,callback_user)
    callback_id=callback.get("id")
    if isinstance(callback_id,str): await answer_callback(client,callback_id)
    message=callback.get("message") or {}; chat_id=(message.get("chat") or {}).get("id"); message_id=message.get("message_id"); choice=callback.get("data")
    if not isinstance(chat_id,int) or not isinstance(message_id,int): return

    if choice=="about":
        about_text = (
            "<b>➻ ᴍʏ ᴀʙᴏᴜᴛ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ</b>\n"
            "• <b>ɴᴀᴍᴇ :</b> ᴢᴇxᴏɴ ᴍᴜꜱɪᴄ ʙᴏᴛ\n"
            "• <b>ʜᴏᴍᴇ :</b> ᴘʏᴛʜᴏɴᴀɴʏᴡᴇʀᴇ\n"
            "• <b>ʟᴀɴɢᴜᴀɢᴇ :</b> ᴘʏᴛʜᴏɴ ᴇɴɢʟɪꜱʜ\n"
            "• <b>ꜱᴇʀᴠᴇʀ :</b> ᴘʏᴛʜᴏɴ ᴠᴇʀꜱɪᴏɴ\n\n"
        )
        await edit_message(client, chat_id, message_id, about_text, keyboard=back_keyboard())
        return

    if choice=="help":
        help_text = "📖 <b>Help Guide:</b>\n\n<i>Simply send any YouTube, Instagram or Facebook link, then select Audio or Thumbnail!</i>\n\n<b>Contact:</b> <code>@zexon_x</code>"
        await edit_message(client, chat_id, message_id, help_text, keyboard=back_keyboard())
        return

    if choice=="home":
        first_name = callback_user.get("first_name") or "दोस्त"
        home_text = (
            f"<b>𝐇ɪ, {first_name} ✨</b> \n\n"
            "<i>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ɪɴꜱᴛᴀɢʀᴀᴍ ꜰᴀᴄᴇʙᴏᴋ ᴍᴜꜱɪᴄ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴏᴛ</i>\n"
            "<i>ᴡᴇ ꜱᴀᴠᴇ ᴍᴜꜱɪᴄ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ꜰᴏʀᴍ ɪɴꜱᴛᴀɢʀᴀᴍ ꜰᴀᴄᴇʙᴏᴏᴋ ꜱᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ</i>\n"
            "<i>ɪꜰ ʏᴏᴜ ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ʟɪɴᴋ ᴀɴᴅ ɢᴇᴛ ᴍᴜꜱɪᴄ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ꜰᴀꜱᴛ ꜱᴇᴄᴜʀᴇ ɪɴꜱᴛᴀɴᴛʟʏ.</i>\n\n"
            "ꜱᴛʏʟɪꜱʜ ᴍᴀɪɴᴛᴇɴᴇᴅ : ᴢᴇxᴏɴ"
        )
        await edit_message(client, chat_id, message_id, home_text, keyboard=start_keyboard())
        return

    if choice=="close":
        await delete_message(client, chat_id, message_id)
        return

    url=LAST_URLS.get(chat_id)
    if not url: await edit_message(client,chat_id,message_id,"<i>Send supported Link 🔗</i>"); return

    if choice=="thumb":
        await edit_message(client,chat_id,message_id,"Downloading...⏳")
        try:
            thumbnail,title=await asyncio.to_thread(extract_thumbnail,url)
            if not thumbnail: raise ValueError("thumbnail_missing")
            await send_photo(client,chat_id,thumbnail)
            if isinstance(callback_user,dict): await asyncio.to_thread(safe_record_user,callback_user,True)
            await delete_message(client,chat_id,message_id)
        except Exception:
            logger.exception("Thumb fail"); await edit_message(client,chat_id,message_id,"<b>download Failed! ❌</b>")
        return

    if choice!="music": return
    await edit_message(client,chat_id,message_id,"Downloading...⏳")
    try:
        with tempfile.TemporaryDirectory(prefix="zexon-") as directory:
            audio_path,title=await asyncio.to_thread(download_audio,url,directory)
            await send_audio(client,chat_id,audio_path,title)
            if isinstance(callback_user,dict): await asyncio.to_thread(safe_record_user,callback_user,True)
        await delete_message(client,chat_id,message_id)
    except ValueError as error:
        msg="<i>this audio Telegram size limit For Big</i>" if str(error)=="audio_too_large" else "<b>Audio Download Failed ❌</b>"
        await edit_message(client,chat_id,message_id,msg)
    except Exception:
        logger.exception("Audio fail"); await edit_message(client,chat_id,message_id,"<b>Audio download Failed send Link public content ❌</b>")

async def handle_update(client: Any, update: dict[str, Any]) -> None:
    if isinstance(update.get("message"),dict): await handle_message(client,update["message"])
    elif isinstance(update.get("callback_query"),dict): await handle_callback(client,update["callback_query"])

async def poll_updates() -> None:
    offset=0
    bot=await telegram_request(None,"getMe")
    logger.info("Started as @%s", bot.get("username","unknown"))
    await telegram_request(None,"deleteWebhook",data={"drop_pending_updates":"false"})
    while True:
        try:
            updates=await telegram_request(None,"getUpdates",data={"offset":str(offset),"timeout":"25","allowed_updates":json.dumps(["message","callback_query"])},timeout=35)
            for update in updates or []:
                offset=max(offset,int(update["update_id"])+1); await handle_update(None,update)
        except Exception as e:
            logger.warning(f"Polling error: {e}")
            await asyncio.sleep(5)

def main() -> None:
    if not TOKEN or "BOT TOKEN" in TOKEN: raise SystemExit("BOT_TOKEN env missing")
    init_user_store(); asyncio.run(poll_updates())

if __name__=="__main__": main()
