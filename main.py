import asyncio
from pyrogram import Client, filters
from playwright.async_api import async_playwright
from urllib.parse import urlparse

API_ID = 33208732  # Apni API ID daalein
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
    await message.reply_text("👋 Welcome to Zexon Bypass Bot!\n\nLink bhejo bypass karne ke liye! 🚀")

@app.on_message(filters.text & ~filters.command(["start"]))
async def bypass_handler(client, message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply_text("❌ Valid URL bhejiye!")
        return
        
    m = await message.reply_text("⏳ **Bypassing link using worker script... Please wait!** 🔄")
    
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Shortener link open karein
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wahi exact bookmarklet script inject karein jo aap use karte ho!
            injection_js = f"""
            (function(){{
                var s = document.createElement('script');
                s.src = 'https://bhootbypass.redbhoot505.workers.dev/?host={hostname}';
                document.body.appendChild(s);
            }})();
            """
            
            await page.evaluate(injection_js)
            
            # Wait karein jab tak page final redirect na ho jaye
            try:
                await page.wait_for_function(
                    f"window.location.hostname !== '{hostname}'",
                    timeout=30000
                )
            except Exception:
                await asyncio.sleep(6)
                
            # Extra wait for redirects
            await asyncio.sleep(3)
            
            final_url = page.url
            await browser.close()
            
            if final_url == url:
                await m.edit_text("⚠️ Bypass complete nahi ho paya. Dobara try karein!")
            else:
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
    
