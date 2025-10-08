import aiohttp, asyncio, os, re, requests, signal
import sys, time, uvicorn, yt_dlp

from bson import ObjectId
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyQuery

from pyrogram import Client, filters
from contextlib import asynccontextmanager
from urllib.parse import urlparse, parse_qs
from motor.motor_asyncio import AsyncIOMotorClient
from youtubesearchpython.__future__ import VideosSearch
from .console import (
    api_id, api_hash, bot_token, owner_id,
    audio_channel_id, video_channel_id, api_key
)
from .database import audio_db, video_db, main_client
from .plugins.mp3_functions import mp3_from_search, mp3_from_youtube_id

bot = Client(
    "ERAAPI",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
)




def get_public_ip() -> str:
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        return "127.0.0.1"

PUBLIC_IP = get_public_ip()


def safe_filename(name: str, ext: str) -> str:
    # Remove invalid filesystem characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Strip leading/trailing spaces
    name = name.strip()
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return f"{name}{ext}"



async def download_media(video_id: str, video: bool, channel_id: int):
    # First try using mp3_functions for audio downloads
    if not video:
        try:
            mp3_link = await mp3_from_youtube_id(video_id)
            if mp3_link:
                # Create a temporary info dict for mp3 downloads
                info = {
                    'id': video_id,
                    'title': f"Downloaded via MP3 Service - {video_id}",
                    'duration': 0
                }
                filepath = os.path.join("downloads", f"{video_id}.mp3")
                
                # Download the mp3 file
                async with aiohttp.ClientSession() as session:
                    async with session.get(mp3_link) as response:
                        if response.status == 200:
                            with open(filepath, 'wb') as f:
                                f.write(await response.read())
                            return filepath, info
        except Exception as e:
            print(f"MP3 functions failed: {e}, falling back to yt-dlp")

    # Fallback to yt-dlp with cookies if mp3_functions fails or for video
    url = f"https://www.youtube.com/watch?v={video_id}"
    loop = asyncio.get_running_loop()

    def media_dl():
        fmt = (
            "bestaudio/best"
            if not video
            else "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])"
        )
        ext = "mp3" if not video else "mp4"
        opts = {
            "format": fmt,
            "outtmpl": f"downloads/%(id)s.{ext}",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }

        # Always use cookies.txt if it exists
        if os.path.exists("cookies.txt"):
            opts["cookiefile"] = "cookies.txt"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filepath = os.path.join("downloads", f"{info['id']}.{ext}")
            if os.path.exists(filepath):
                return filepath, info
            ydl.download([url])
            return filepath, info

    filepath, info = await loop.run_in_executor(None, media_dl)
    return filepath, info


def clean_mongo(doc: dict) -> dict:
    if not doc:
        return {}
    doc = dict(doc)
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])  # or remove completely
        doc.pop("_id")   # if you don’t want it at all
    return doc


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await main_client.admin.command("ping")
    except Exception:
        print("⚠️ Invalid MongoDB URL")
        sys.exit()

    await bot.start()
    try:
        await bot.send_message(owener_id, " AUDIO CHANNEL STARTED ✅")
    except Exception as e:
        print(f"⚠️ Audio notify failed: {e} – Check admin access")

    try:
        await bot.send_message(owener_id, " VIDEO CHANNEL STARTED ✅")
    except Exception as e:
        print(f"⚠️ Video notify failed: {e} – Check admin access")

    yield

    print("Shutting down...")
    await bot.stop()
    print("Bot stopped")


app = FastAPI(title="YouTube API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key Authentication
api_key_query = APIKeyQuery(name="key", auto_error=False)

async def verify_api_key(api_key_param: str = Depends(api_key_query)):
    if not api_key_param:
        raise HTTPException(status_code=401, detail="API key missing")
    if api_key_param != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key_param

@app.get("/")
async def root():
    return {}



@app.get("/query")
async def search_videos(
    query: str = Query(..., description="Search term"),
    video: bool = Query(False, description="True for video, False for audio"),
    api_key_param: str = Depends(verify_api_key)
):
    db = video_db if video else audio_db

    # 1. First try mp3_functions for audio searches
    if not video:
        try:
            mp3_result = await mp3_from_search(query)
            if mp3_result and "mp3" in mp3_result:
                mp3_data = mp3_result["mp3"]
                return {
                    "link": mp3_data["link"],
                    "type": "audio",
                    "title": mp3_data["title"],
                    "size": mp3_data.get("size", "Unknown")
                }
        except Exception as e:
            print(f"MP3 search failed: {e}, falling back to YouTube search")

    # 2. Search YouTube
    result = await VideosSearch(query, limit=1).next()
    items = result.get("result", [])
    if not items:
        return {}

    v = items[0]
    vid_id = v["id"]
    duration_str = v.get("duration")

    # 2. Detect live streams
    if not duration_str or duration_str.lower() == "live":
        return {}

    # 3. Check cache
    cached = await db.find_one({"id": vid_id})
    if cached:
        return clean_mongo(cached)

    # 4. Parse duration string into seconds
    parts = list(map(int, duration_str.split(":")))
    if len(parts) == 3:
        hrs, mins, secs = parts
    elif len(parts) == 2:
        hrs, mins, secs = 0, parts[0], parts[1]
    else:
        hrs, mins, secs = 0, 0, parts[0]
    duration_seconds = hrs * 3600 + mins * 60 + secs

    # 5. Choose appropriate channel for audio/video
    target_channel_id = video_channel_id if video else audio_channel_id

    # 6. Download media (cookies.txt used automatically if exists)
    filepath, info = await download_media(vid_id, video, target_channel_id)

    # 6. Prepare safe file name
    ext = os.path.splitext(filepath)[1]
    file_name = safe_filename(v["title"], ext)

    # 7. Send to Telegram channel
    tg_msg = await (bot.send_document if video else bot.send_audio)(
        chat_id=target_channel_id, **{
            ("document" if video else "audio"): filepath,
            "title": v["title"], "performer": "@EraVibesXbot",
            "duration": duration_seconds, "file_name": file_name})
    
    print(f"{'📹 Video' if video else '🎵 Audio'} sent to channel {target_channel_id}")
    file_id = (tg_msg.document if video else tg_msg.audio).file_id


    # 8. Get Telegram download URL
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        ) as resp:
            data = await resp.json()
            file_path = data["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

    # 9. Save record
    record = {
        "id": vid_id,
        "title": v["title"],
        "artist": "@EraVibesXbot",
        "duration_str": duration_str,
        "duration_sec": duration_seconds,
        "file_id": file_id,
        "channel": v.get("channel", {}).get("name"),
        "thumbnail": v.get("thumbnails", [{}])[0].get("url"),
        "stream_url": f"https://t.me/c/{str(target_channel_id)[4:]}/{tg_msg.id}",
        "download_url": download_url,
        "telegram_channel_id": target_channel_id,
        "media_type": "video" if video else "audio",
    }
    await db.insert_one(record)

    # 10. Cleanup local file
    try:
        os.remove(filepath)
    except OSError:
        pass

    # Return only stream_url and media_type to user
    return {
        "link": record.get("stream_url"),
        "type": record.get("media_type")
    }



@bot.on_message(filters.command("start") & filters.private)
async def start_message_private(client, message):
    return await message.reply_text(f"**Hello, {message.from_user.mention}**")


if __name__ == "__main__":
    uvicorn.run("Erixter:app", host="0.0.0.0", port=5000, reload=False)


