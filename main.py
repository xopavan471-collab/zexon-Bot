import logging
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==================== CONFIGURATION ====================
# Yahan apna Telegram Bot Token daalna hai jo aapko BotFather se mila hai:
BOT_TOKEN = "8476616777:AAG-iOSBfCQcfJ-4pic2KcfjlmkoVKGBRm8"
# =======================================================

# Logging setup taaki errors terminal me dikhein
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def bypass_shortener(target_url: str) -> str:
    """
    Core Bypass Engine: Redirection aur Form/Scraping logic
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # Step 1: Follow direct redirects
            async with session.get(target_url, allow_redirects=True, timeout=10) as response:
                final_url = str(response.url)
                html_content = await response.text()

            # Step 2: HTML Scraping agar page par form ya tags ho
            if "<form" in html_content.lower():
                soup = BeautifulSoup(html_content, "html.parser")
                form = soup.find("form")
                if form and form.get("action"):
                    action_url = form.get("action")
                    return f"Form Detected!\nAction URL: {action_url}"
                
                for a in soup.find_all("a", href=True):
                    href = a['href']
                    if "http" in href and "google" not in href:
                        return href

            return final_url

        except Exception as e:
            return f"Error aa gaya: {str(e)}"

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Main aapka Link Bypass Bot hoon.\n\n"
        "Link bypass karne ke liye yeh command use karein:\n"
        "`/bypass https://get2short.com/your-link`",
        parse_mode="Markdown"
    )

# /bypass command handler
async def bypass_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Kripya link bhi dein! Example: `/bypass <url>`", parse_mode="Markdown")
        return

    target_url = context.args[0]
    processing_msg = await update.message.reply_text("⏳ Link bypass ho raha hai, thoda intezaar karein...")

    # Bypass function ko call karein
    result_link = await bypass_shortener(target_url)

    # User ko final result bhejein
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_msg.message_id,
        text=f"✅ **Bypass Successful!**\n\n🔗 **Final Link:**\n`{result_link}`",
        parse_mode="Markdown"
    )

def main():
    # Bot Application initialize karein
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers add karein
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bypass", bypass_command))

    print("🤖 Bot successfully start ho gaya hai...")
    # Bot ko run karein
    application.run_polling()

if __name__ == "__main__":
    main()
        
