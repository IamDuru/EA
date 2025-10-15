import asyncio, time, httpx, aiohttp, json, cloudscraper
from urllib.parse import quote
from typing import Dict, Optional



# --- Headers ---
BASE_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Referer": "https://v3.mp3juices.click/"}

FLVTO_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Content-Type": "application/json", "Referer": "https://flvto.site/"}

FLVTO_ALT_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5", "Referer": "https://www-mp3juices.com/"}

FLVTO_CF_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Content-Type": "application/json", "Origin": "https://ht.flvto.online"}

YT_MP3_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Referer": "https://ytmp3.as/"}

YT_MP3_ALT_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5", "Referer": "https://ytmp3.as/", "Origin": "https://ytmp3.as"}

MP3JUICE_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5", "Content-Type": "application/x-www-form-urlencoded", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "cross-site", "Sec-GPC": "1", "Priority": "u=0", "Referer": "https://mp3juice.lt/"}


def _ts() -> int:
    return int(time.time())


# --- Provider 1: FLVTO (Original) ---
async def youtube_to_mp3_flvto(id: str) -> Dict[str, Optional[str]]:
    try:
        async with httpx.AsyncClient(timeout=20, headers=FLVTO_HEADERS) as client:
            r = await client.post("https://es.flvto.top/converter",
                                  json={"id": id, "fileType": "mp3"})
            r.raise_for_status()
            data = r.json()
            return {"dowmp3": data.get("link") if data.get("status") == "ok" else None}
    except Exception as e:
        return {"dowmp3": None, "error": f"flvto: {e}"}


# --- Provider 1B: FLVTO Alternate (Using aiohttp + different subdomains) ---
async def youtube_to_mp3_flvto_alt(id: str) -> Dict[str, Optional[str]]:
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Search (flow maintain karne ke liye)
            search_url = f"https://test.flvto.online/search/?q=https://www.youtube.com/watch?v={id}"
            async with session.get(search_url, headers=FLVTO_ALT_HEADERS) as resp:
                await resp.text()  # Just trigger the search flow
            
            # Step 2: Convert
            convert_url = "https://ht.flvto.online/converter"
            payload = {"id": id, "fileType": "mp3"}
            headers = {**FLVTO_ALT_HEADERS, "Content-Type": "application/json"}
            
            async with session.post(convert_url, headers=headers, json=payload) as resp:
                text = await resp.text()
                try:
                    convert_data = await resp.json()
                except:
                    convert_data = json.loads(text)
                return {"dowmp3": convert_data.get("link")}
    except Exception as e:
        return {"dowmp3": None, "error": f"flvto_alt: {e}"}


# --- Provider 1C: FLVTO CloudScraper (Cloudflare Bypass) ---
def _flvto_cloudscraper_sync(id: str) -> Dict[str, Optional[str]]:
    """Sync version using cloudscraper for Cloudflare bypass"""
    try:
        scraper = cloudscraper.create_scraper(browser={
            'browser': 'firefox',
            'platform': 'windows',
            'mobile': False
        })
        
        url = "https://ht.flvto.online/converter"
        headers = {
            **FLVTO_CF_HEADERS,
            "Referer": f"https://ht.flvto.online/widget?url=https://www.youtube.com/watch?v={id}&el=267",
        }
        payload = {"id": id, "fileType": "MP3"}
        
        r = scraper.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        res = r.json()
        
        return {"dowmp3": res.get("link")}
    except Exception as e:
        return {"dowmp3": None, "error": f"flvto_cf: {e}"}


async def youtube_to_mp3_flvto_cloudscraper(id: str) -> Dict[str, Optional[str]]:
    """Async wrapper for cloudscraper method"""
    try:
        # Run sync cloudscraper in thread pool to make it async-compatible
        result = await asyncio.to_thread(_flvto_cloudscraper_sync, id)
        return result
    except Exception as e:
        return {"dowmp3": None, "error": f"flvto_cf_async: {e}"}


# --- Provider 2: YTMP3 (Original Method) ---
async def youtube_to_mp3_ytmp3(id: str) -> Dict[str, Optional[str]]:
    try:
        async with httpx.AsyncClient(timeout=20, headers=YT_MP3_HEADERS) as client:
            init_url = (
                "https://www1.ummn.nu/api/v1/init"
                "?u=UHV6TmJoOHJXZ1NIdGVNclZrMjJLMWNzeXhTZmhVMFNyS2pWc1B3cXlFMmZJVGFxSlpTT3Qyb2xqMF9RQTR4SW5rRzY4RW4xMktrZTZ1S040ODNmNHUy"
                f"&_={_ts()}"
            )
            r = await client.get(init_url)
            init_data = r.json()
            if init_data.get("error") != "0":
                return {"dowmp3": None, "error": f"ytmp3 init failed: {init_data.get('error')}"}

            convert_url = f"{init_data['convertURL']}&v={id}&f=mp3&_={_ts()}"
            r = await client.get(convert_url)
            convert_data = r.json()

            if convert_data.get("redirect") and convert_data.get("redirectURL"):
                r = await client.get(f"{convert_data['redirectURL']}&_={_ts()}")
                convert_data = r.json()

            return {"dowmp3": convert_data.get("downloadURL")}
    except Exception as e:
        return {"dowmp3": None, "error": f"ytmp3: {e}"}


# --- Provider 2B: YTMP3 Alternate Method (Using aiohttp) ---
async def youtube_to_mp3_ytmp3_alt(id: str) -> Dict[str, Optional[str]]:
    try:
        async with aiohttp.ClientSession() as session:
            ts = _ts()
            
            # Step 1: Init
            init_url = f"https://www1.ummn.nu/api/v1/init?y=ZmZ5blFtMGtKYUVrUW41ckpqUjZDV1dZREU2UWpvY2JWYUQ4OW1nNlJfTnFGMTIzMGxlbDVzMlE1bzJCNHg0UjAxZmIxbDE%3D&t={ts}"
            async with session.get(init_url, headers=YT_MP3_ALT_HEADERS) as resp:
                await resp.json()  # Just to trigger the init
            
            # Step 2: Direct final call
            final_url = f"https://www0.ummn.nu/?id={id}&t={ts+5}"
            async with session.get(final_url, headers=YT_MP3_ALT_HEADERS) as resp:
                final_data = await resp.json()
                return {"dowmp3": final_data.get("link")}
    except Exception as e:
        return {"dowmp3": None, "error": f"ytmp3_alt: {e}"}


# --- Provider 3: Insvid (search/convert) ---
async def youtube_to_mp3_insvid(id: str) -> Dict[str, Optional[str]]:
    try:
        async with httpx.AsyncClient(timeout=20, headers=BASE_HEADERS) as client:
            button_url = f"https://ac.insvid.com/button?url=https://www.youtube.com/watch?v={id}&fileType=mp3&el=232"
            await client.get(button_url)

            r = await client.post(
                "https://ac.insvid.com/converter",
                headers={**BASE_HEADERS,
                         "Content-Type": "application/json",
                         "Origin": "https://ac.insvid.com",
                         "Referer": button_url},
                json={"id": id, "fileType": "mp3"}
            )
            r.raise_for_status()
            d = r.json()
            return {"dowmp3": d.get("link") if d.get("status") == "ok" else None}
    except Exception as e:
        return {"dowmp3": None, "error": f"insvid: {e}"}


# --- Provider 4: MP3Juice ---
async def youtube_to_mp3_mp3juice(id: str) -> Dict[str, Optional[str]]:
    try:
        async with httpx.AsyncClient(timeout=20, headers=MP3JUICE_HEADERS) as client:
            # First fetch title from search API
            youtube_url = f"https://www.youtube.com/watch?v={id}"
            resp = await client.post(
                "https://cdn.mp3j.cc/search",
                data={"q": youtube_url, "_ym_uid": "undefined"},
                headers=MP3JUICE_HEADERS,
            )
            resp.raise_for_status()
            title = (resp.json().get("YoutubeVideo") or {}).get("title") or "Unknown"
            
            # Build direct MP3 download URL
            mp3_url = f"https://cdn.mp3j.cc/dl-yt?file={id}.mp3&title={quote(f'{title}(mp3j.cc)')}"
            return {"dowmp3": mp3_url}
    except Exception as e:
        return {"dowmp3": None, "error": f"mp3juice: {e}"}


# --- Orchestrator ---
async def get_dowmp3(id: str) -> Dict[str, Optional[str]]:
    """
    Try all providers in parallel using a YouTube video ID.
    Returns the first successful dowmp3 link.
    """
    tasks = [
        youtube_to_mp3_flvto(id),
        youtube_to_mp3_flvto_alt(id),
        youtube_to_mp3_flvto_cloudscraper(id),  # NEW CLOUDFLARE BYPASS
        youtube_to_mp3_ytmp3(id),
        youtube_to_mp3_ytmp3_alt(id),
        youtube_to_mp3_insvid(id),
        youtube_to_mp3_mp3juice(id),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, dict) and res.get("dowmp3"):
            return res

    return {"dowmp3": None, "error": "All providers failed"}


# --- Example Usage ---
'''
id = "sUf2PtEZris"  # Example YouTube ID
result = await mp3_best_from_videoid(id)
print(result)
'''
