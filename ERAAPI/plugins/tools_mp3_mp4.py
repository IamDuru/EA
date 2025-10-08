import asyncio
import requests
import base64
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Accept": "*/*",
    "Referer": "https://mp3juice.co/"
}

def safe_json(resp):
    """Try to parse JSON, else return raw text with error flag."""
    try:
        return resp.json()
    except ValueError:
        return {"error": "not_json", "raw": resp.text[:200]}

async def get_download_url(youtube_url: str, fmt: str = "mp4") -> Optional[str]:
    """
    Async version of get_download_url function
    Args:
        youtube_url: YouTube URL to convert
        fmt: Format to download ('mp3' or 'mp4')
    Returns:
        Direct download URL or None if failed
    """
    try:
        async with requests.Session() as session:
            # Step 1: Encode YouTube URL
            encoded_url = base64.b64encode(youtube_url.encode()).decode()

            # Step 2: Search request
            search_api = (
                "https://mp3juice.co/se.php?"
                "a=UHV6TmJoOHJXZ1NIdGVNclZrMjJLMWNzeXhTZmhVMFNyS2pWc1B3cXlFMmZJVGFxSlpTT3Qyb2xqMF9RQTR4SW5rRzY4RW4xMktrZTZ1S040ODNmNHUy"
                f"&y=y&q={encoded_url}"
            )

            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.get(search_api, headers=HEADERS, timeout=15)
            )
            data = safe_json(response)

            if not data.get("yt"):
                print(f"No YouTube results. Response: {data}")
                return None

            video_id = data["yt"][0]["id"]

            # Step 3: Init request
            init_api = (
                "https://www1.eooc.cc/api/v1/init?"
                "u=UHV6TmJoOHJXZ1NIdGVNclZrMjJLMWNzeXhTZmhVMFNyS2pWc1B3cXlFMmZJVGFxSlpTT3Qyb2xqMF9RQTR4SW5rRzY4RW4xMktrZTZ1S040ODNmNHUy"
            )

            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.get(init_api, headers=HEADERS, timeout=15)
            )
            init_data = safe_json(response)

            if "convertURL" not in init_data:
                print(f"Init failed. Response: {init_data}")
                return None

            convert_url = init_data["convertURL"]

            # Step 4: Convert request
            convert_api = f"{convert_url}&v={video_id}&f={fmt}"
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.get(convert_api, headers=HEADERS, timeout=20)
            )
            conv_data = safe_json(response)

            # Handle redirect if present
            if conv_data.get("redirect") == 1 and conv_data.get("redirectURL"):
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: session.get(conv_data["redirectURL"], headers=HEADERS, timeout=20)
                )
                conv_data = safe_json(response)

            if conv_data.get("error") != 0:
                print(f"Conversion failed. Response: {conv_data}")
                return None

            download_url = conv_data.get("downloadURL")
            return download_url

    except Exception as e:
        print(f"Error in get_download_url: {e}")
        return None


#---------------------------####-------
import requests
from urllib.parse import quote
import json

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
REF, BASE = "https://mp3juice.lt/", "https://cdn.mp3j.cc"

BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}
SEARCH_HEADERS = {
    **BASE_HEADERS,
    "Content-Type": "application/x-www-form-urlencoded",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "Priority": "u=0",
    "Referer": REF,
}
NAV_HEADERS = {
    **BASE_HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Sec-GPC": "1",
    "Priority": "u=0, i",
    "Referer": REF,
}


def _post_search(session: requests.Session, q: str, timeout: float = 15.0) -> dict:
    resp = session.post(
        f"{BASE}/search",
        data={"q": q, "_ym_uid": "undefined"},
        headers=SEARCH_HEADERS,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


async def mp3j_top1_links(query: str, resolution: int = 720, trigger_download: bool = False, timeout: float = 20.0) -> Optional[dict]:
    """
    Async version of mp3j_top1_links function
    Fetch top-1 YouTube result and return MP3/MP4 download links.
    MP4 is forced unmuted via '_true' in title.
    """
    try:
        async with requests.Session() as s:
            # Search request
            resp = await asyncio.get_event_loop().run_in_executor(
                None, lambda: s.post(
                    f"{BASE}/search",
                    data={"q": query, "_ym_uid": "undefined"},
                    headers=SEARCH_HEADERS,
                    timeout=timeout,
                )
            )
            resp.raise_for_status()
            search_data = resp.json()

            yt = search_data.get("YoutubeSearch") or []
            if not yt or "id" not in yt[0]:
                print("No YouTube result found")
                return None

            video_id = yt[0]["id"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

            # Get video details
            resp = await asyncio.get_event_loop().run_in_executor(
                None, lambda: s.post(
                    f"{BASE}/search",
                    data={"q": youtube_url, "_ym_uid": "undefined"},
                    headers=SEARCH_HEADERS,
                    timeout=timeout,
                )
            )
            resp.raise_for_status()
            video_data = resp.json()

            title = (video_data.get("YoutubeVideo") or {}).get("title") or yt[0].get("title", "Unknown")

            mp3_url = f"{BASE}/dl-yt?file={video_id}.mp3&title={quote(f'{title}(mp3j.cc)')}"
            mp4_url = f"{BASE}/dl-yt?file={video_id}_{resolution}.mp4&title={quote(f'{title}_true(mp3j.cc)')}"

            if trigger_download:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: s.get(mp4_url, headers=NAV_HEADERS, timeout=timeout, allow_redirects=True).raise_for_status()
                )

            return {
                "videoId": video_id,
                "downloadUrlMp3": mp3_url,
                "downloadUrlMp4": mp4_url,
            }

    except Exception as e:
        print(f"Error in mp3j_top1_links: {e}")
        return None


# Convenience functions for direct import
async def get_mp3_download_url(youtube_url: str) -> Optional[str]:
    """Get MP3 download URL from YouTube URL"""
    return await get_download_url(youtube_url, "mp3")


async def get_mp4_download_url(youtube_url: str) -> Optional[str]:
    """Get MP4 download URL from YouTube URL"""
    return await get_download_url(youtube_url, "mp4")


async def get_video_download_links(query: str, resolution: int = 720) -> Optional[dict]:
    """Search and get both MP3 and MP4 download links"""
    return await mp3j_top1_links(query, resolution, trigger_download=False)

