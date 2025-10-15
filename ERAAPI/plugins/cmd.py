
import psutil, datetime, logging
from pyrogram import filters
from .. import bot, console
from ..database import get_task, set_task, del_task, audiodb, videodb, apidb

logger = logging.getLogger("EraApi")



@bot.on_message(filters.command("toggle_direct") & filters.user(console.owner_id))
async def toggle_direct_download(_, message):
    logger.info(f"🔄 Toggle direct download command from user {message.from_user.id}")
    try:
        current = await get_task("direct_download_enabled", console.direct_download_enabled)
        new_val = not current
        await set_task("direct_download_enabled", new_val)
        console.direct_download_enabled = new_val
        status = "true" if new_val else "false"
        await message.reply_text(f"Direct download is now {status}")
        logger.info(f"✅ Direct download toggled to {status}")
    except Exception as e:
        logger.error(f"❌ Error in toggle_direct: {e}")
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.command("status") & filters.user(console.owner_id))
async def status_command(_, message):
    logger.info(f"📊 Status command from user {message.from_user.id}")
    try:
        direct_enabled = await get_task("direct_download_enabled", console.direct_download_enabled)
        max_tasks = await get_task("max_background_tasks", console.max_background_tasks)
        status = "true" if direct_enabled else "false"
        await message.reply_text(f"Direct download: {status}\nMax background tasks: {max_tasks}")
        logger.info(f"✅ Status sent: direct={status}, tasks={max_tasks}")
    except Exception as e:
        logger.error(f"❌ Error in status command: {e}")
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.command("set_tasks") & filters.user(console.owner_id))
async def set_max_tasks(_, message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("Usage: /set_tasks <number>")
            return
        new_val = int(args[1])
        if new_val < 1 or new_val > 20:
            await message.reply_text("Please choose a number between 1 and 20")
            return

        # Delete old value first
        old_val = await get_task("max_background_tasks", console.max_background_tasks)
        if old_val != console.max_background_tasks:  # Only delete if custom value set
            await del_task("max_background_tasks")

        # Set new value
        await set_task("max_background_tasks", new_val)
        console.max_background_tasks = new_val
        await message.reply_text(f"Max background tasks set to {console.max_background_tasks}")
    except ValueError:
        await message.reply_text("Please provide a valid number")

@bot.on_message(filters.command("stats") & filters.user(console.owner_id))
async def stats_command(_, message):
    try:
        # System stats
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())

        # Bot stats
        bot_users = 0  # TODO: implement user counting
        bot_chats = 0  # TODO: implement chat counting

        # API stats
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        this_week = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        this_month = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        # Count total API keys
        total_apis = await apidb.count_documents({})

        # Count media in database
        total_audio = await audiodb.count_documents({})
        total_video = await videodb.count_documents({})

        # Calculate API usage stats
        today_requests = 0
        week_requests = 0
        month_requests = 0
        total_requests = 0

        async for user in apidb.find({}):
            usage = user.get("usage", {})
            monthly_usage = user.get("monthly_usage", {})

            # Daily
            today_requests += usage.get(today, 0)

            # Weekly
            for date in usage:
                if date >= this_week:
                    week_requests += usage[date]

            # Monthly
            for date in usage:
                if date >= this_month:
                    month_requests += usage[date]

            # Total
            total_requests += sum(usage.values())

        stats_text = f"""
📊 **System Statistics**

🖥️ **System:**
• CPU Usage: {cpu}%
• RAM: {ram.percent}% ({ram.used//1024//1024}MB/{ram.total//1024//1024}MB)
• Disk: {disk.percent}% ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)
• Uptime: {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m

🤖 **Bot:**
• Total Users: {bot_users}
• Total Chats: {bot_chats}

📡 **API Statistics**
• Total API Keys: {total_apis}
• Stored Audio: {total_audio}
• Stored Video: {total_video}

📈 **Requests Today:** {today_requests}
📈 **Requests This Week:** {week_requests}
📈 **Requests This Month:** {month_requests}
📈 **Total Requests:** {total_requests}

🔄 **Media Downloads:**
• Audio Downloads: {total_audio}
• Video Downloads: {total_video}
"""

        await message.reply_text(stats_text)
    except Exception as e:
        await message.reply_text(f"❌ Stats Error: {e}")