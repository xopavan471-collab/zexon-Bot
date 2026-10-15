import asyncio
from pyrogram import Client, filters
from playwright.async_api import async_playwright

API_ID = 33208732  # Apni API ID daalein
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "8937292337:AAFoGCvtrkqrRZ25LgKGIdm7DbG8VstcRB0"

app = Client(
    "zexon_bypass_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

JS_BYPASS_SCRIPT = """
(function(){
    const bypassCookies=["adcadg=insurance,online_colleges,study_abroad,finance,loan; max-age=3600; path=/;","eonudb=insurance,online_colleges,study_abroad,finance,loan; max-age=3600; path=/;","_uocat=value; max-age=86400; path=/;"];
    bypassCookies.forEach(cookie=>document.cookie=cookie);
})();
"""

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("👋 Welcome to Zexon Bypass Bot!\n\nLink bhejo bypass karne ke liye! 🚀")

@app.on_message(filters.text & ~filters.command(["start"]))
async def bypass_handler(client, message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply_text("❌ Valid URL bhejiye!")
        return
        
    m = await message.reply_text("⏳ **Bypassing link in headless browser... Please wait!** 🔄")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Script execute cookies set karne ke liye
            await page.add_init_script(JS_BYPASS_SCRIPT)
            
            # Shortener link open karein
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Final URL obtain karein
            final_url = page.url
            await browser.close()
            
            await m.edit_text(
                f"✅ **Bypass Successful!** 🎉\n\n"
                f"🔗 **Original:** {url}\n"
                f"✨ **Final Link:** {final_url}"
            )
    except Exception as e:
        await m.edit_text(f"❌ **Error:** `{str(e)}`")

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    app.run()
    
