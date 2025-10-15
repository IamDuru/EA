from pyrogram import filters
from .. import bot, console

@bot.on_message(filters.command("start") & filters.private)
async def start_command(_, message):
    start_text = f"""
🤖 **Welcome to ERA API Bot!**

🎵 **YouTube Audio/Video Downloader API**
• Fast downloads with direct links
• Telegram media storage
• Multiple format support

📡 **API Endpoint:** `https://your-domain.com/try`
📚 **Documentation:** Use /help for commands

👨‍💻 **Owner:** @{console.owner_id}
🔗 **Support:** Coming soon

**Send /help for available commands**
"""
    await message.reply_text(start_text)

@bot.on_message(filters.command("help"))
async def help_command(_, message):
    help_text = """
📚 **Available Commands**

🤖 **General Commands:**
• /start - Welcome message
• /help - Show this help

⚙️ **System Commands (Owner Only):**
• /toggle_direct - Enable/disable direct downloads
• /status - Show system status
• /set_tasks <number> - Set max background tasks

🔑 **API Management (Owner Only):**
• /genpr - Generate permanent unlimited API key
• /gen30 - Generate 30 days unlimited API key
• /gencustom <quota> <days> - Generate custom API key
• /delapi <key> - Delete specific API key
• /listapi - List all API keys with details
• /clean_expired - Clean expired API keys

📊 **Statistics:**
• /stats - Show system, bot and API statistics

📡 **API Usage:**
```
GET https://your-domain.com/try?key=API_KEY&query=SONG_NAME&vid=false
```

**Parameters:**
• `key` - Your API key
• `query` - YouTube URL or search term
• `vid` - true for video, false for audio
"""
    await message.reply_text(help_text)