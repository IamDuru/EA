import hashlib, os, aiohttp
from datetime import datetime, timedelta
from pyrogram import filters
from .. import bot, console
from ..database import apidb

async def batbin(text):
    BASE = "https://batbin.me/"
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE}api/v2/paste", data=text) as resp:
            data = await resp.json() if 'application/json' in resp.headers.get('content-type', '') else await resp.text()
    return BASE + data["message"] if data.get("success") else None

# Auto cleanup removed - now happens on-demand when API is accessed

def gen_key():
    return hashlib.sha256(os.urandom(32)).hexdigest()[:32]

@bot.on_message(filters.command("genpr") & filters.user(console.owner_id))
async def gen_permanent(_, message):
    try:
        key = gen_key()
        data = {"api_key": key, "plan": "permanent", "daily_limit": -1, "monthly_limit": -1, "created_at": datetime.utcnow(), "expires_at": None, "usage": {}, "monthly_usage": {}}
        apidb.insert_one(data)
        await message.reply_text(f"✅ Permanent API Key:\n\n`{key}`\n\nPlan: Permanent Unlimited")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@bot.on_message(filters.command("gen30") & filters.user(console.owner_id))
async def gen_30_days(_, message):
    try:
        key = gen_key()
        expires = datetime.utcnow() + timedelta(days=30)
        data = {"api_key": key, "plan": "30days", "daily_limit": -1, "monthly_limit": -1, "created_at": datetime.utcnow(), "expires_at": expires, "usage": {}, "monthly_usage": {}}
        apidb.insert_one(data)
        await message.reply_text(f"✅ 30 Days Unlimited API Key:\n\n`{key}`\n\nExpires: {expires.strftime('%Y-%m-%d')}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@bot.on_message(filters.command("gencustom") & filters.user(console.owner_id))
async def gen_custom(_, message):
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.reply_text("Usage: /gencustom <daily_quota> <days>")
            return
        quota, days = int(args[1]), int(args[2])
        if quota <= 0 or days <= 0:
            await message.reply_text("❌ Daily quota and days must be positive numbers")
            return
        key = gen_key()
        expires = datetime.utcnow() + timedelta(days=days)
        data = {"api_key": key, "plan": "custom", "daily_limit": quota, "monthly_limit": quota * 30, "created_at": datetime.utcnow(), "expires_at": expires, "usage": {}, "monthly_usage": {}}
        apidb.insert_one(data)
        await message.reply_text(f"✅ Custom API Key:\n\n`{key}`\n\nDaily Limit: {quota}\nExpires: {expires.strftime('%Y-%m-%d')}")
    except ValueError:
        await message.reply_text("❌ Please provide valid numbers for quota and days")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@bot.on_message(filters.command("delapi") & filters.user(console.owner_id))
async def delete_api(_, message):
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text("Usage: /delapi <api_key>")
            return
        api_key = args[1]
        result = await apidb.delete_one({"api_key": api_key})
        if result.deleted_count > 0:
            await message.reply_text(f"✅ API Key deleted: `{api_key}`")
        else:
            await message.reply_text(f"❌ API Key not found: `{api_key}`")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@bot.on_message(filters.command("listapi") & filters.user(console.owner_id))
async def list_apis(_, message):
    try:
        apis = []
        async for api in apidb.find({}):
            key = api.get("api_key", "N/A")
            plan = api.get("plan", "N/A")
            expires = api.get("expires_at")
            expires_str = expires.strftime("%Y-%m-%d") if expires else "Never"
            daily_limit = api.get("daily_limit", 0)
            usage = api.get("usage", {})
            total_requests = sum(usage.values())

            # Calculate recent usage
            today = datetime.utcnow().strftime("%Y-%m-%d")
            week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            month_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

            today_req = usage.get(today, 0)
            week_req = sum(usage.get(date, 0) for date in usage if date >= week_ago)
            month_req = sum(usage.get(date, 0) for date in usage if date >= month_ago)

            apis.append(f"""🔑 API Key: {key}
📋 Plan: {plan}
⏰ Expires: {expires_str}
📊 Daily Limit: {daily_limit}
📈 Today: {today_req} | Week: {week_req} | Month: {month_req} | Total: {total_requests}
{'-'*50}""")

        if not apis:
            await message.reply_text("📭 No API keys found")
            return

        response = "📋 **API Keys Details**\n\n" + "\n".join(apis)

        if len(response) > 4000:
            paste_url = await batbin(response)
            if paste_url:
                await message.reply_text(f"📋 **API Keys Details**\n\n📄 Too long, view here: {paste_url}")
            else:
                await message.reply_text("❌ Failed to create paste link")
        else:
            await message.reply_text(response)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@bot.on_message(filters.command("clean_expired") & filters.user(console.owner_id))
async def clean_expired_apis(_, message):
    try:
        from datetime import datetime
        result = await apidb.delete_many({"expires_at": {"$lt": datetime.utcnow()}})
        deleted_count = result.deleted_count
        await message.reply_text(f"🧹 Cleaned {deleted_count} expired API keys")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")