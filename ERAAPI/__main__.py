import aiohttp, asyncio, os, uvicorn, json
from fastapi import FastAPI, Query
from pyrogram import idle
from DvisSearch import FastYoutubeSearch

from . import console, app, bot
from .database import (
    is_served_audio, is_served_video, add_served_video, add_served_audio,
    get_served_audio, get_served_video, get_task, check_api_key, parse_query, 
    convert_to_seconds, get_dowmp3, get_dowmp4, download_audio, download_video,
    get_task
)

# Semaphore for max parallel background downloads
background_semaphore = asyncio.Semaphore(console.max_background_tasks)



@app.get("/")
async def home():
    return {}


@app.get("/try")
async def get_media_url(
    key: str = Query(..., description="API key for authentication"),
    query: str = Query(..., description="Search term or YouTube URL"),
    vid: bool = Query(False, description="True for video, False for audio")
):
    check_api_key(key)
    if not query:
        return {"error": "Query is required"}

    search_query = parse_query(query)
    search = FastYoutubeSearch(search_query, max_results=1)
    result = json.loads(search.to_json())["videos"]

    if not result:
        return {}

    video = result[0]
    title = video["title"]
    id = video["id"]
    duration = video["duration"]
    link = video["link"]

    if not duration:
        return {}

    # Check if already served
    is_media = (is_served_video if vid else is_served_audio)(id)
    if is_media:
        served_media = (get_served_video if vid else get_served_audio)(id)
        return {"link": served_media["link"]}

    # If direct download enabled, try direct providers first
    direct_enabled = await get_task("direct_download_enabled", console.direct_download_enabled)
    if direct_enabled:
        try:
            dowmp3 = (await get_dowmp3(id)).get("dowmp3")
            dowmp4 = (await get_dowmp4(id)).get("dowmp4")
            direct_link = dowmp4 if vid else dowmp3

            if direct_link and direct_link.startswith("http"):
                # Start background upload task
                asyncio.create_task(background_upload(direct_link, id, vid, title, duration))
                return {"link": direct_link}
        except Exception:
            pass  # Fall back to yt_dlp

    # Fallback to yt_dlp download and upload
    try:
        file, _ = await (download_video if vid else download_audio)(link)
    except Exception as e:
        return {"error": f"Failed to download {'video' if vid else 'audio'}: {str(e)}"}

    try:
        if not os.path.exists(file):
            return {"error": f"Downloaded file not found: {file}"}

        if vid:
            sent = await bot.send_document(
                console.channel_id,
                document=file,
                duration=convert_to_seconds(duration),
                performer="@ERAAPI",
                title=title,
            )
        else:
            sent = await bot.send_audio(
                console.channel_id,
                audio=file,
                duration=convert_to_seconds(duration),
                performer="@ERAAPI",
                title=title,
            )
    except Exception as e:
        return {"error": f"Failed to upload {'video' if vid else 'audio'}: {str(e)}"}

    link_out = sent.link
    (add_served_video if vid else add_served_audio)(id, link_out)
    if os.path.exists(file):
        os.remove(file)

    return {"link": link_out}


async def background_upload(direct_link: str, id: str, vid: bool, title: str, duration: str):
    async with background_semaphore:
        try:
            # Download directly
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_link) as resp:
                    if resp.status == 200:
                        temp_file = f"temp_{id}.{'mp4' if vid else 'mp3'}"
                        with open(temp_file, 'wb') as f:
                            f.write(await resp.read())

            # Upload to TG
            if os.path.exists(temp_file):
                if vid:
                    sent = await bot.send_document(
                        console.channel_id,
                        document=temp_file,
                        duration=convert_to_seconds(duration),
                        performer="@ERAAPI",
                        title=title,
                    )
                else:
                    sent = await bot.send_audio(
                        console.channel_id,
                        audio=temp_file,
                        duration=convert_to_seconds(duration),
                        performer="@ERAAPI",
                        title=title,
                    )
            link_out = sent.link
            (add_served_video if vid else add_served_audio)(id, link_out)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass  # Silent fail for background task


async def main():
    print("Starting bot...")
    try:
        await bot.start()
        print("Bot started successfully")
    except Exception as e:
        print(f"Failed to start bot: {e}")
        return

    print("Starting API server...")
    config = uvicorn.Config(
        app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_level="info"
    )
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())

    print("Bot and API are running. Press Ctrl+C to stop.")
    try:
        await idle()
    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        print("Stopping bot and server...")
        await server.shutdown()
        await bot.stop()
        api_task.cancel()
        try:
            await api_task
        except asyncio.CancelledError:
            pass
        print("Shutdown complete")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
