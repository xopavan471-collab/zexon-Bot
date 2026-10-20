import os
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Apni Telegram API credentials yahan daalein
API_ID = 33208732       # My.telegram.org se milega
API_HASH = "28626a3063a8161fc374ce904093c4e0"   # My.telegram.org se milega
BOT_TOKEN = "BOT TOKEN" # BotFather se milega

app = Client(
    "fancy_font_pyrogram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- UNICODE CONVERTER FUNCTIONS ---
def convert_style(text: str, upper_start: int, lower_start: int, digit_start: int = None) -> str:
    result = []
    for char in text:
        codepoint = ord(char)
        if 65 <= codepoint <= 90:
            result.append(chr(upper_start + (codepoint - 65)))
        elif 97 <= codepoint <= 122:
            result.append(chr(lower_start + (codepoint - 97)))
        elif 48 <= codepoint <= 57 and digit_start is not None:
            result.append(chr(digit_start + (codepoint - 48)))
        else:
            result.append(char)
    return "".join(result)

def to_fullwidth(text: str) -> str:
    result = []
    for char in text:
        cp = ord(char)
        if 33 <= cp <= 126:
            result.append(chr(cp + 65248))
        elif cp == 32:
            result.append(chr(12288))
        else:
            result.append(char)
    return "".join(result)

def to_small_caps(text: str) -> str:
    small_caps_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ',
        'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
        'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
        'y': 'ʏ', 'z': 'ᴢ'
    }
    return "".join(small_caps_map.get(c.lower(), c).upper() for c in text)

def make_fancy(text: str) -> dict:
    return {
        "Bold": convert_style(text, 0x1D400, 0x1D41A, 0x1D7CE),
        "Italic": convert_style(text, 0x1D434, 0x1D44E),
        "Bold Italic": convert_style(text, 0x1D468, 0x1D482),
        "Sans-Serif": convert_style(text, 0x1D5A0, 0x1D5BA, 0x1D7E2),
        "Sans Bold": convert_style(text, 0x1D5D4, 0x1D5EE, 0x1D7EC),
        "Sans Italic": convert_style(text, 0x1D608, 0x1D622),
        "Sans Bold Italic": convert_style(text, 0x1D63C, 0x1D656),
        "Monospace": convert_style(text, 0x1D670, 0x1D68A, 0x1D7F6),
        "Fullwidth": to_fullwidth(text),
        "Small Caps": to_small_caps(text)
    }

# --- 1. START COMMAND & WELCOME MESSAGE ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    welcome_text = (
        f"<b>𝐇ʏ {message.from_user.first_name}</b>\n\n"
        "<blockquote><b><i>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ꜱᴛʏʟɪꜱʜ ꜰᴀɴᴄʏ ꜰᴏɴᴛꜱ ɢᴇɴᴇʀᴀᴛᴏʀ  ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ʏᴏᴜʀ ꜱᴛʏʟɪꜱʜ ꜰᴀɴᴄʏ ꜰᴏɴᴛ ᴛᴇxᴛ ᴀɴᴅ ᴀʟᴡᴀʏꜱ ʜᴀᴘᴘᴇɴꜱ , ʀᴇᴀᴅʏ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ꜱᴛʏʟɪꜱʜ ꜰᴏɴᴛ ᴛᴇxᴛ ᴊᴜꜱᴛ ᴜꜱᴇ ꜰᴏɴᴛ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ꜰᴏɴᴛ ꜱᴛʏʟᴇ ᴛᴇxᴛ, ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ɢɪᴠᴇ ᴛᴇxᴛ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ɪᴛ ꜰᴀɴᴄʏ ꜰᴏɴᴛ ꜱᴛʏʟᴇ ᴇᴀꜱʏ, ʜᴀᴠᴇ ꜰᴜɴ ɴɪᴄᴇ ᴅᴀʏ ᴇɴᴊᴏʏ ꜰᴜɴ ᴍᴀꜱᴛɪ</i></b></blockquote>\n"
        "<blockquote>**ꜰᴇᴀᴛᴜʀᴇꜱ ✨**\n"
        "<b>• ᴛʀᴀɴꜱꜰᴇʀ ɴᴏʀᴍᴀʟ ᴛᴇxᴛ ɪɴᴛᴏ ꜰᴀɴᴄʏ ꜱᴛʏʟᴇ </b></blockquote>\n"
        "<blockquote><b>• ᴀʟʟ ꜰᴏɴᴛꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ</b></blockquote>\n"
        "<blockquote>**ʜᴏᴡ ᴛᴏ ᴜꜱᴇ :**"
         "<b> ꜱᴇɴᴅ /font ᴛʜᴀᴛ ꜱɪᴅᴇ ᴡʀɪᴛᴇ ʏᴏᴜʀ ᴛᴇxᴛ</b></blockquote>\n"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇꜱ 🔊", url="https://t.me/zexon_Bot_updates"),
            InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ 💬", url="https://t.me/URL_Save_Bot")
        ]
    ])
    
    await message.reply_text(text=welcome_text, reply_markup=buttons, quote=True)

# --- 2. FANCY FONT GENERATOR COMMAND ---
@app.on_message(filters.command("font"))
async def font_generator(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("**Usage 😅 :** `/font [Your Favourite text]`", quote=True)
        return
    
    input_text = " ".join(message.command[1:])
    fonts = make_fancy(input_text)
    
    response = "<blockquote>**Dear, Choose your Favourite Font ✅**\nTap to copy 👇</blockquote>\n\n"
    for style_name, styled_text in fonts.items():
        response += f"• **{style_name}:**\n`{styled_text}`\n\n"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="close_font")]
    ])
    
    await message.reply_text(response, reply_markup=buttons, quote=True)

# --- 3. CLOSE BUTTON CALLBACK ---
@app.on_callback_query(filters.regex("close_font"))
async def close_callback(client: Client, callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        await callback.answer("Already deleted!", show_alert=False)

# --- 4. AUTO REACTION FEATURE ---
REACTION_EMOJI = "🔥"

@app.on_message(filters.channel | filters.group & ~filters.service)
async def auto_reaction(client: Client, message: Message):
    try:
        await client.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji=REACTION_EMOJI
        )
    except Exception as e:
        print(f"Reaction error: {e}")

# Bot Start
print("Pyrogram Bot is running successfully...")
app.run()

