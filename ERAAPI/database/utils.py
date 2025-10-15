import aiohttp
import re
from urllib.parse import urlparse
from pyrogram import Client

# Assuming bot and bot_token are available; if not, they need to be imported or passed
# For now, keeping as is, assuming they are accessible in the module context

async def get_cdn_url(message_link: str, bot, bot_token: str):
    parsed = urlparse(message_link)
    parts = parsed.path.strip("/").split("/")
    channel = parts[0]
    msg_id = int(parts[1])

    msg = await bot.get_messages(channel, int(msg_id))
    media = msg.audio or msg.document or msg.voice
    if not media:
        return None

    file_id = media.file_id

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        ) as resp:
            data = await resp.json()
            try:
                file_path = data["result"]["file_path"]
            except Exception:
                return None

            return f"https://api.telegram.org/file/bot{bot_token}/{file_path}"



def parse_query(query: str) -> str:
    if match := re.search(r'(?:v=|\/(?:embed|v|shorts|live)\/|youtu\.be\/)([A-Za-z0-9_-]{11})', query):
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return query



def convert_to_seconds(duration: str) -> int:
    parts = list(map(int, duration.split(":")))
    total = 0
    multiplier = 1

    for value in reversed(parts):
        total += value * multiplier
        multiplier *= 60

    return total


def format_duration(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if sec > 0 or not parts:
        parts.append(f"{sec}s")

    return " ".join(parts)