import asyncio
import aiohttp
import random
from typing import Optional, Dict


async def _fetch_github_speedx(session) -> Optional[str]:
    """GitHub TheSpeedX - 30 min updates"""
    try:
        url = 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                text = await resp.text()
                proxies = [p.strip() for p in text.split('\n') if p.strip()]
                if proxies:
                    proxy = random.choice(proxies[:30])
                    if await _test_proxy(session, proxy):
                        return proxy
    except:
        pass
    return None


async def _fetch_github_skillter(session) -> Optional[str]:
    """GitHub Skillter - validated proxies"""
    try:
        url = 'https://raw.githubusercontent.com/Skillter/ProxyGather/refs/heads/master/proxies/working-proxies-http.txt'
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                text = await resp.text()
                proxies = [p.strip() for p in text.split('\n') if p.strip()]
                if proxies:
                    proxy = random.choice(proxies[:30])
                    if await _test_proxy(session, proxy):
                        return proxy
    except:
        pass
    return None


async def _fetch_github_jetkai(session) -> Optional[str]:
    """GitHub jetkai - hourly updates"""
    try:
        url = 'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt'
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                text = await resp.text()
                proxies = [p.strip() for p in text.split('\n') if p.strip()]
                if proxies:
                    proxy = random.choice(proxies[:30])
                    if await _test_proxy(session, proxy):
                        return proxy
    except:
        pass
    return None


async def _fetch_proxyscrape(session) -> Optional[str]:
    """ProxyScrape API - 5 min updates, fastest"""
    try:
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=1000&country=all&ssl=yes&anonymity=elite"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                text = await resp.text()
                proxies = [p.strip() for p in text.split('\r\n') if p.strip()]
                if proxies:
                    proxy = random.choice(proxies[:20])
                    if await _test_proxy(session, proxy):
                        return proxy
    except:
        pass
    return None


async def _fetch_geonode(session) -> Optional[str]:
    """Geonode API - JSON format"""
    try:
        url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get('data'):
                    item = random.choice(data['data'][:15])
                    proxy = f"{item['ip']}:{item['port']}"
                    if await _test_proxy(session, proxy):
                        return proxy
    except:
        pass
    return None


async def _test_proxy(session, proxy: str) -> bool:
    """Check if a proxy is working by making a quick request."""
    test_url = "http://httpbin.org/ip"
    try:
        async with session.get(
            test_url,
            proxy=f"http://{proxy}",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


async def get_proxy() -> Dict[str, Optional[str]]:
    async with aiohttp.ClientSession() as session:
        tasks = [
            _fetch_proxyscrape(session),
            _fetch_github_speedx(session),
            _fetch_github_skillter(session),
            _fetch_github_jetkai(session),
            _fetch_geonode(session),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, str) and res:
                # Auto add http:// if missing
                if not res.startswith(("http://", "https://", "socks5://")):
                    res = f"http://{res}"
                return {"proxy": res, "error": None}
            
        return {"proxy": None, "error": "All providers failed"}


        # proxy = (await get_proxy()).get("proxy")