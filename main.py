import asyncio
from pyrogram import Client, filters
import aiohttp
from urllib.parse import urlparse

# Apni Telegram API details aur Bot Token yahan daalein
API_ID = 33208732  # Apni api_id daalein
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "8937292337:AAFoGCvtrkqrRZ25LgKGIdm7DbG8VstcRB0"

app = Client(
    "zexon_bypass_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "👋 **Welcome to Zexon Bypass Bot!**\n\n"
        "Mujhe koi bhi shortener link bhejo, aur main turant use bypass karke aapko final link de dunga! 🚀"
    )

@app.on_message(filters.text & ~filters.command(["start"]))
async def bypass_handler(client, message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        await message.reply_text("❌ Kripya ek valid URL bhejo jo 'http' ya 'https' se start hota ho!")
        return
    
    m = await message.reply_text("⏳ **Bypassing link... Please wait!** 🔄")
    
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        # Worker API endpoint jo aapne share kiya tha
        api_url = f"https://bhootbypass.redbhoot505.workers.dev/?host={hostname}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    result_link = await resp.text()
                    await m.edit_text(
                        f"✅ **Bypass Successful!** 🎉\n\n"
                        f"🔗 **Original Link:** {url}\n"
                        f"✨ **Final Link:** {result_link}"
                    )
                else:
                    await m.edit_text("❌ Bypass karne mein kuch issue aaya, please dobara try karo!")
                    
    except Exception as e:
        await m.edit_text(f"❌ **Error:** `{str(e)}`")

if __name__ == "__main__":
    print("🤖 Zexon Bypass Bot is starting...")
    app.run()
