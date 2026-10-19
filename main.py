#!/usr/bin/env python3
import asyncio
import logging
import re
import time
import urllib.parse
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Cloudflare & Anti-Bot bypass ke liye curl_cffi AsyncSession
try:
    from curl_cffi.requests import AsyncSession
except ImportError:
    AsyncSession = None

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8476616777:AAHuixXmf0u0_qh0oMNSrk9JjkD-Xl_sfLQ"  # Aapka Bot Token
BYPASS_API_KEY = "bl_live_1699d4c4a63d873862fc4dae6db68570033c"  # Aapki api.bypass.tools ki API Key
# =======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def pure_native_unshorten(url: str) -> str:
    """
    Bit.ly, tinyurl, cutt.ly, is.gd jaise normal short links ko direct unshorten karna.
    """
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
    """
    bypass link ki official API ka use karke shortener links bypass karna.
    """
    if not AsyncSession or not BYPASS_API_KEY:
        return None
        
    try:
        api_url = f"https://bypass-links.com/api/v1/bypass?url={urllib.parse.quote(target_url)}"
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
    """
    MediaFire link se direct downloadable file link extract karna.
    """
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

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇꜱ", url="https://t.me/zexon_Bot_updates"),
            InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛᴇᴅ", callback_data="btn_supported")
        ]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="btn_home")
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "User"
    
    text = (
        f"<b>𝐇ɪ {user_name}</b>\n\n"
        "<blockquote><b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴢᴇxᴏɴ ʙʏᴘᴀꜱꜱ ʙᴏᴛ</b></blockquote>\n"
        "<blockquote><i>ᴡᴇ ᴄᴀɴ ʙʏᴘᴀꜱꜱ ᴘᴀᴘᴜʟᴀʀ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ, ꜱᴇɴᴅ ᴍᴇ ᴀɴʏ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ ᴛʜᴇɴ ɪ'ᴍ  ᴘʀᴏꜱᴇꜱꜱ ʏᴏᴜʀ ʟɪɴᴋ ᴀɴᴅ ɢɪᴠᴇ ʏᴏᴜ ꜰɪɴᴀʟ ʟɪɴᴋ, ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ, ᴘʟᴇᴀꜱᴇ ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ʟɪɴᴋ, ꜱᴇɴᴅ ɴᴏʀᴍᴀʟ ʟɪɴᴋ ᴛᴏ ʜᴀɴᴅʟᴇ ᴅɪꜱɪꜱɪᴏɴ.</i></blockquote>\n"
        "<blockquote><b>ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ</b></blockquote>"
    )

    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_start_keyboard())
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=get_start_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "btn_update":
        await query.answer("Bot is already running on the latest version! 🚀", show_alert=True)
    
    elif query.data == "btn_supported":
        supported_text = (
            "<b>Supported Websites & Links:</b>\n\n"
            "• <b>Normal Shorteners:</b> bit.ly, tinyurl.com, cutt.ly, is.gd\n"
            "• <b>File Storage:</b> mediafire.com\n"
            "• <b>Ad-Shorteners & Gates:</b> Supported via api.bypass.tools\n\n"
            "<i>Send any supported link to get started!</i>"
        )
        await query.edit_message_text(text=supported_text, parse_mode="HTML", reply_markup=get_back_keyboard())
    
    elif query.data == "btn_home":
        user_name = query.from_user.first_name or "User"
        home_text = (
            f"<b>𝐇ɪ {user_name}</b>\n\n"
            "<blockquote><b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴢᴇxᴏɴ ʙʏᴘᴀꜱꜱ ʙᴏᴛ</b></blockquote>\n"
            "<blockquote><i>ᴡᴇ ᴄᴀɴ ʙʏᴘᴀꜱꜱ ᴘᴀᴘᴜʟᴀʀ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ, ꜱᴇɴᴅ ᴍᴇ ᴀɴʏ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ ᴛʜᴇɴ ɪ'ᴍ  ᴘʀᴏꜱᴇꜱꜱ ʏᴏᴜʀ ʟɪɴᴋ ᴀɴດ ɢɪᴠᴇ ʏᴏᴜ ꜰɪɴᴀʟ ʟɪɴᴋ, ʀᴇᴀᴅʏ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ, ᴘʟᴇᴀꜱᴇ ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ʟɪɴᴋ, ꜱᴇɴᴅ ɴᴏʀᴍᴀʟ ʟɪɴᴋ ᴛᴏ ʜᴀɴᴅʟᴇ ᴅɪꜱɪꜱɪᴏɴ.</i></blockquote>\n"
            "<blockquote><b>ᴅᴏɴ'ᴛ ꜱᴇɴᴅ ʜɪɢʜ ꜱʜᴏʀᴛɴᴇʀ ʟɪɴᴋ</b></blockquote>"
        )
        await query.edit_message_text(text=home_text, parse_mode="HTML", reply_markup=get_start_keyboard())

async def auto_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    url_match = re.search(r'https?://[^\s]+', text)
    if not url_match:
        return

    target_url = url_match.group(0)
    
    start_time = time.time()
    processing_msg = await update.message.reply_text("𝐏ʟᴇᴀꜱᴇ ᴡᴀɪᴛ...")

    # 1. Sabse pehle normal links (bit.ly, tinyurl, cutt.ly) ke liye native unshortener try karo
    result_link = await pure_native_unshorten(target_url)

    # 2. Agar wahan se na aaye, toh official api.bypass.tools API se try karo
    if not result_link:
        result_link = await bypass_with_api(target_url)

    # 3. Agar MediaFire hai toh direct scraper use karo
    if not result_link and "mediafire.com" in target_url.lower():
        result_link = await bypass_mediafire(target_url)
        
    elapsed = round(time.time() - start_time, 2)

    if result_link:
        response_text = (
            f"<blockquote><b>Original Link :</b></blockquote>\n{target_url}\n"
            f"<blockquote><b>Bypassed Link :</b></blockquote>\n{result_link}\n\n"
            f"<blockquote><b>Time Elapsed</b> ⧖➙ {elapsed} s</blockquote>\n\n<blockquote><b>𝐏ᴏᴡᴇʀᴇᴅ ʙʏ :</b> @zexon_Bypass_Bot</blockquote>"
        )
    else:
        response_text = (
            f"<blockquote><i>BYPASS FAILED ❌</i></blockquote>\n\n"
            f"<i>Unsupported Link ⚠️</i>\n\n"
            f"<blockquote>Elapsed ⧖➙ {elapsed}s</blockquote>"
        )

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_msg.message_id,
        text=response_text,
        disable_web_page_preview=True,
        parse_mode="HTML"
    )

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_link_handler))

    print("🤖 zexon Bypass Bot (API Integrated) start ho gaya hai!")
    application.run_polling()

if __name__ == "__main__":
    main()
                
