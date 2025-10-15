# app/downloader.py
import os, asyncio, yt_dlp
from .. import console
from .poxy import get_proxy

ANDROID_UA = "com.google.android.youtube/19.20.35 (Linux; U; Android 13) gzip"
IOS_UA = "com.google.ios.youtube/19.20.37 (iPhone15,3; U; CPU iOS 17_5 like Mac OS X)"

def _base_opts(proxy: str | None = None):
    os.makedirs(console.download_dir, exist_ok=True)
    opts = {
        "outtmpl": os.path.join(console.download_dir, "%(title).200B.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "retries": 2,
        "fragment_retries": 2,
        "skip_unavailable_fragments": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "no_warnings": True,
        "no_check_certificate": True,
        "cachedir": False,
    }
    if console.cookies_path and os.path.exists(console.cookies_path):
        opts["cookiefile"] = console.cookies_path
    return opts

def _client_opts(client: str):
    if client == "android":
        return {
            "extractor_args": {"youtube": {"player_client": "android"}},
            "http_headers": {"User-Agent": ANDROID_UA, "Accept-Language": "en-US,en;q=0.9"},
        }
    if client == "ios":
        return {
            "extractor_args": {"youtube": {"player_client": "ios"}},
            "http_headers": {"User-Agent": IOS_UA, "Accept-Language": "en-US,en;q=0.9"},
        }
    return {
        "extractor_args": {"youtube": {"player_client": "mweb"}},
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

# 🟩 Fast async audio downloader
async def download_audio(link: str):
    proxy = (await get_proxy()).get("proxy")
    fmt = "bestaudio/best"
    post = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]
    clients = ("android", "ios", "mweb")

    async def _attempt(client: str):
        opts = _base_opts(proxy)
        opts.update(_client_opts(client))
        opts.update({"format": fmt, "postprocessors": post})

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                out = ydl.prepare_filename(info)
                if not out.lower().endswith(".mp3"):
                    out = os.path.splitext(out)[0] + ".mp3"
                return out, info.get("title") or "audio"

        return await asyncio.to_thread(_run)

    for client in clients:
        try:
            return await _attempt(client)
        except Exception:
            continue
    raise Exception("All audio download attempts failed")

# 🟩 Fast async video downloader (up to 720p)
async def download_video(link: str):
    proxy = (await get_proxy()).get("proxy")
    fmt = "bv*[height<=720][vcodec^=avc1]+ba/b[height<=720]"
    clients = ("android", "ios", "mweb")

    async def _attempt(client: str):
        opts = _base_opts(proxy)
        opts.update(_client_opts(client))
        opts.update({"format": fmt})

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=True)
                path = ydl.prepare_filename(info)
                if not path.lower().endswith(".mp4"):
                    new = os.path.splitext(path)[0] + ".mp4"
                    try:
                        os.replace(path, new)
                    except Exception:
                        pass
                    path = new
                return path, info.get("title") or "video"

        return await asyncio.to_thread(_run)

    for client in clients:
        try:
            return await _attempt(client)
        except Exception:
            continue
    raise Exception("All video download attempts failed")
