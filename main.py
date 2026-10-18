#!/usr/bin/env python3
import asyncio
import logging
import re
import time
import urllib.parse
import hashlib
import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.enums.button_style import ButtonStyle

# Cloudflare & Anti-Bot bypass ke liye curl_cffi AsyncSession
try:
    from curl_cffi.requests import AsyncSession
except ImportError:
    AsyncSession = None

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8476616777:AAG-iOSBfCQcfJ-4pic2KcfjlmkoVKGBRm8"  # Aapka Bot Token
BYPASS_API_KEY = "bt_bb659baa52dda94ef508aoba1473b3db726efd8fda159f03"  # Aapki api.bypass.tools ki API Key
# =======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== EARNLINK AES DECRYPTION ====================
def decrypt_earnlink_payload(encrypted_hex_str: str, passphrase: str = "root") -> str:
    try:
        try:
            from Crypto.Cipher import AES
        except ImportError:
            AES = None

        data = bytes.fromhex(encrypted_hex_str)
        if not data.startswith(b"Salted__"):
            salt = b""
            ciphertext = data
        else:
            salt = data[8:16]
            ciphertext = data[16:]

        def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
            dt = b""
            d = b""
            while len(dt) < (key_len + iv_len):
                d = hashlib.md5(d + password + salt).digest()
                dt += d
            return dt[:key_len], dt[key_len:key_len + iv_len]

        key, iv = evp_bytes_to_key(passphrase.encode('utf-8'), salt)

        if AES:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(ciphertext)
        else:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()

        pad_len = decrypted[-1]
        if isinstance(pad_len, int) and pad_len <= 16:
            decrypted = decrypted[:-pad_len]

        real_url = decrypted.decode('utf-8', errors='ignore').strip()
        if real_url.startswith("http"):
            return real_url
    except Exception as e:
        logger.error(f"Earnlink AES Decrypt error: {e}")
    return None

async def bypass_earnlink(target_url: str) -> str:
    parsed = urllib.parse.urlparse(target_url)
    query_params = urllib.parse.parse_qs(parsed.query)
    
    if 'o' in query_params:
        encrypted_val = query_params['o'][0]
        res = decrypt_earnlink_payload(encrypted_val)
        if res:
            return res

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(target_url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
                html_text = await response.text()
                o_match = re.search(r'[\?&]o=([a-fA-F0-9]+)', html_text)
                if o_match:
                    enc_data = o_match.group(1)
                    res = decrypt_earnlink_payload(enc_data)
                    if res:
                        return res
                
                link_match = re.search(r'href=["\'](https?://[^\s"\']+)["\']', html_text)
                if link_match:
                    found_url = link_match.group(1)
                    if "earn" not in found_url and "itiexamshala" not in found_url:
                        return found_url
    except Exception as e:
        logger.error(f"Earnlink scraper error: {e}")

    return None

# ==================== GENERAL UNSHORTENERS ====================
async def pure_native_unshorten(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
                final_url = str(response.url)
                
                if final_url and final_url.rstrip('/') != url.rstrip('/'):
                    return final_url

                html_text = await response.text()
                meta_match = re.search(r'content=["\']\d+;\s*url=([^"\']+)["\']', html_text, re.IGNORECASE)
                if meta_match:
                    meta_url = meta_match.group(1).strip()
                    if meta_url.startswith("http"):
                        return meta_url

                loc_match = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', html_text)
                if loc_match:
                    loc_url = loc_match.group(1).strip()
                    if loc_url.startswith("http"):
                        return loc_url
    except Exception as e:
        logger.error(f"Native unshorten error: {e}")

    return None

async def bypass_with_api(target_url: str) -> str:
    if not AsyncSession or not BYPASS_API_KEY:
        return None
        
    try:
        api_url = f"https://api.bypass.tools/bypass?url={urllib.parse.quote(target_url)}"
        headers = {
            "Authorization": f"Bearer {BYPASS_API_KEY}",
            "Accept": "application/json"
        }
        
        async with AsyncSession(impersonate="chrome120") as session:
            resp = await session.get(api_url, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                final_link = data.get("destination") or data.get("url") or data.get("result")
                if final_link and final_link.startswith("http"):
                    return final_link
    except Exception as e:
        logger.error(f"Bypass API error: {e}")
        
    return None

async def bypass_mediafire(target_url: str) -> str:
    if "mediafire.com" not in target_url.lower():
        return None
    if not AsyncSession:
        return None
        
    try:
        async with AsyncSession(impersonate="chrome120") as session:
            resp = await session.get(target_url, allow_redirects=True, timeout=15)
            html = resp.text
            match = re.search(r'href="([^"]+)"\s+id="downloadButton"', html)
            if match:
                direct_link = match.group(1)
                if direct_link.startswith("http"):
                    return direct_link
    except Exception as e:
        logger.error(f"MediaFire bypass error: {e}")
    
    return None

# ==================== MULTI-STEP CHAIN RESOLVER ====================
async def resolve_link_chain(target_url: str) -> str:
    current_url = target_url
    for _ in range(3):
        next_url = None

        if "earn" in current_url.lower() or "o=" in current_url.lower():
            next_url = await bypass_earnlink(current_url)

        if not next_url:
            next_url = await pure_native_unshorten(current_url)

        if not next_url:
            next_url = await bypass_with_api(current_url)

        if not next_url and "mediafire.com" in current_url.lower():
            next_url = await bypass_mediafire(current_url)

        if next_url and next_url != current_url:
            current_url = next_url
        else:
            break

    return current_url if current_url != target_url else None

# ==================== KEYBOARDS (RED STYLE) ====================
def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ᴜᴘᴅᴀᴛᴇꜱ", url="https://t.me/zexon_Bot_updates", style=ButtonStyle.DANGER),
            InlineKeyboardButton(text="ꜱᴜᴘᴘᴏʀᴛᴇᴅ", callback_data="btn_supported", style=ButtonStyle.DANGER)
        ]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="btn_home", style=ButtonStyle.DANGER)
        ]
    ])

# ==================== AIOGRAM HANDLERS ====================
async def start_handler(message: Message):
    user_name = message.from_user.first_name or "User"
    text = (
        f"<b>𝐇ɪ {user_name}</b>\n\n"
        "<blockquote><b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴢᴇxᴏɴ ʙʏᴘᴀꜱꜱ ʙᴏᴛ</b></blockquote>\n"
        "<blockquote><i>ᴡᴇ ᴄᴀɴ ʙʏᴘᴀꜱꜱ ᴘᴀᴘᴜʟᴀʀ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ, ꜱᴇɴᴅ ᴍᴇ ᴀɴʏ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ ᴛʜᴇɴ ɪ'ᴍ  ᴘʀᴏꜱᴇꜱꜱ ʏᴏᴜʀ ʟɪɴᴋ ᴀɴᴅ ɢɪᴠᴇ ʏᴏᴜ ꜰɪɴᴀʟ ʟɪɴᴋ, ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ, ᴘʟᴇᴀꜱᴇ ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ʟɪɴᴋ, ꜱᴇɴᴅ ɴᴏʀᴍᴀʟ ʟɪɴᴋ ᴛᴏ ʜᴀɴʟᴇ ᴅɪꜱɪꜱɪᴏɴ.</i></blockquote>\n"
        "<blockquote><b>ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ</b></blockquote>"
    )
    await message.reply(text, parse_mode=ParseMode.HTML, reply_markup=get_start_keyboard())

async def button_callback_handler(callback: CallbackQuery):
    query_data = callback.data
    await callback.answer()

    if query_data == "btn_supported":
        supported_text = (
            "<b>Supported Websites & Links:</b>\n\n"
            "• <b>Ad-Shorteners:</b> Earnlink (Multi-step AES Decryption)\n"
            "• <b>Normal Shorteners:</b> bit.ly, tinyurl.com, cutt.ly, is.gd\n"
            "• <b>File Storage:</b> mediafire.com\n"
            "• <b>Other Gates:</b> Supported via api.bypass.tools\n\n"
            "<i>Send any supported link to get started!</i>"
        )
        await callback.message.edit_text(text=supported_text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard())
    
    elif query_data == "btn_home":
        user_name = callback.from_user.first_name or "User"
        home_text = (
            f"<b>𝐇ɪ {user_name}</b>\n\n"
            "<blockquote><b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴢᴇxᴏɴ ʙʏᴘᴀꜱꜱ ʙᴏᴛ</b></blockquote>\n"
            "<blockquote><i>ᴡᴇ ᴄᴀɴ ʙʏᴘᴀꜱꜱ ᴘᴀᴘᴜʟᴀʀ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ, ꜱᴇɴᴅ ᴍᴇ ᴀɴʏ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ ᴛʜᴇɴ ɪ'ᴍ  ᴘʀᴏꜱᴇꜱꜱ ʏᴏᴜʀ ʟɪɴᴋ ᴀɴᴅ ɢɪᴠᴇ ʏᴏᴜ ꜰɪɴᴀʟ ʟɪɴᴋ, ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ.</i></blockquote>\n"
            "<blockquote><b>ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ</b></blockquote>"
        )
        await callback.message.edit_text(text=home_text, parse_mode=ParseMode.HTML, reply_markup=get_start_keyboard())

async def auto_link_handler(message: Message):
    text = message.text
    if not text:
        return

    url_match = re.search(r'https?://[^\s]+', text)
    if not url_match:
        return

    target_url = url_match.group(0)
    
    start_time = time.time()
    processing_msg = await message.reply("𝐏ʟᴇᴀꜱᴇ ᴡᴀɪᴛ...")

    result_link = await resolve_link_chain(target_url)
        
    elapsed = round(time.time() - start_time, 2)

    if result_link:
        response_text = (
            f"<blockquote><b>Original Link :</b></blockquote>\n{target_url}\n\n"
            f"<blockquote><b>Bypassed Link :</b></blockquote>\n{result_link}\n\n"
            f"<blockquote><b>Time Elapsed</b> ⧖➙ {elapsed} s</blockquote>\n\n<blockquote><b>𝐏ᴏᴡᴇʀᴇᴅ ʙʏ :</b> @zexon_Bypass_Bot</blockquote>"
        )
    else:
        response_text = (
            f"<blockquote><i>BYPASS FAILED ❌</i></blockquote>\n\n"
            f"<i>Unsupported Link ⚠️</i>\n\n"
            f"<blockquote>Elapsed ⧖➙ {elapsed}s</blockquote>"
        )

    await processing_msg.edit_text(
        text=response_text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

# ==================== MAIN FUNCTION ====================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register handlers
    dp.message.register(start_handler, Command("start"))
    dp.callback_query.register(button_callback_handler, F.data.startswith("btn_"))
    dp.message.register(auto_link_handler, F.text & ~F.text.startswith("/"))

    print("🤖 ZEXON Bypass Bot (Aiogram 3.x with Red Buttons) Started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
