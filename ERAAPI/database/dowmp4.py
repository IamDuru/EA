
import requests, time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
    "Accept": "*/*",
    "Referer": "https://mp3juice.co/"
}

def safe_json(resp):
    try:
        return resp.json()
    except ValueError:
        return {"error": "not_json", "raw": resp.text[:200]}

def get_mp4_url(id: str) -> str:
    ts = int(time.time())

    # Step 1: Init API (gives convertURL with sig)
    init_api = f"https://www1.eooc.cc/api/v1/init?e=SEFneE42cUs2MHdobzkzbHMwSWxjXzZsMWc5a2ROMGpPOWEySlVhOFZORzlY&t={ts}"
    r = requests.get(init_api, headers=HEADERS, timeout=15)
    init_data = safe_json(r)

    if "convertURL" not in init_data:
        raise Exception(f"Init failed. Raw: {init_data}")

    convert_url = init_data["convertURL"]

    # Step 2: Convert API (mp4 only)
    convert_api = f"{convert_url}&v={id}&f=mp4&t={ts}"
    r = requests.get(convert_api, headers=HEADERS, timeout=20)
    conv_data = safe_json(r)

    # Step 3: Handle redirect if present
    if conv_data.get("redirect") == 1 and conv_data.get("redirectURL"):
        r = requests.get(conv_data["redirectURL"], headers=HEADERS, timeout=20)
        conv_data = safe_json(r)

    # Step 4: Final download URL
    dowmp4 = conv_data.get("downloadURL")
    if not dowmp4:
        raise Exception(f"No download URL. Raw: {conv_data}")
    return dowmp4


async def get_dowmp4(id: str):
    """Async wrapper for get_mp4_url"""
    import asyncio
    result = await asyncio.to_thread(get_mp4_url, id)
    return {"dowmp4": result}

'''
# 🔥 Example usage
vid = "sUf2PtEZris"   # YouTube id
print(get_mp4_url(vid))
'''