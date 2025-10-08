import requests, urllib.parse, json, re

# Updated User-Agent for YouTube requests
YOUTUBE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

class FastYoutubeSearch:
    def __init__(self, search_terms: str, max_results=None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self._fast_search()

    def _fast_search(self):
        encoded = urllib.parse.quote_plus(self.search_terms)
        url = f"https://youtube.com/results?search_query={encoded}"
        response = requests.get(url, headers=YOUTUBE_HEADERS).text

        for _ in range(3):
            if "ytInitialData" in response: break
            response = requests.get(url, headers=YOUTUBE_HEADERS).text

        try:
            data = json.loads(re.search(r'ytInitialData\s*=\s*({.+?});', response, re.DOTALL).group(1))
            results = []

            for content in data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]:
                for item in content["itemSectionRenderer"]["contents"]:
                    if "videoRenderer" in item:
                        vid = item["videoRenderer"]
                        video_id = vid.get("videoId")
                        if video_id:
                            video_url = f"https://www.youtube.com{vid['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url']}"
                            results.append({"id": video_id, "url": video_url})
                            if self.max_results and len(results) >= self.max_results: return results
        except: pass

        return results

    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos})
        if clear_cache: self.videos = []
        return result


class YoutubeSearch:
    def __init__(self, search_terms: str, max_results=None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self._search()

    def _search(self):
        encoded = urllib.parse.quote_plus(self.search_terms)
        url = f"https://youtube.com/results?search_query={encoded}"
        response = requests.get(url, headers=YOUTUBE_HEADERS).text
        while "ytInitialData" not in response:
            response = requests.get(url, headers=YOUTUBE_HEADERS).text
        data = json.loads(re.search(r'ytInitialData\s*=\s*({.+?});', response, re.DOTALL).group(1))
        
        results = []
        try:
            for content in data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]:
                for item in content["itemSectionRenderer"]["contents"]:
                    if "videoRenderer" in item:
                        vid = item["videoRenderer"]
                        video_id = vid.get("videoId")
                        if not video_id:
                            continue
                        
                        # Watch link
                        watch_suffix = vid['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url']
                        watch_url = f"https://www.youtube.com{watch_suffix}"
                        
                        # Fetch video page for direct URLs
                        video_page_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_response = requests.get(video_page_url, headers=YOUTUBE_HEADERS).text
                        player_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', video_response, re.DOTALL)
                        video_direct = watch_url  # Fallback to watch
                        audio_direct = watch_url  # Fallback to watch
                        if player_match:
                            player_data = json.loads(player_match.group(1))
                            if 'streamingData' in player_data and 'adaptiveFormats' in player_data['streamingData']:
                                formats = player_data['streamingData']['adaptiveFormats']
                                # Best video MP4
                                mp4_formats = [f for f in formats if f.get('mimeType', '').startswith('video/mp4')]
                                if mp4_formats:
                                    best_video = max(mp4_formats, key=lambda x: int(x.get('bitrate', 0)))
                                    video_direct = best_video['url']
                                # Best audio
                                audio_formats = [f for f in formats if f.get('mimeType', '').startswith('audio/')]
                                if audio_formats:
                                    best_audio = max(audio_formats, key=lambda x: int(x.get('bitrate', 0)))
                                    audio_direct = best_audio['url']
                        
                        res = {
                            "id": video_id,
                            "thumbnails": [thumb["url"] for thumb in vid["thumbnail"]["thumbnails"]],
                            "title": vid["title"]["runs"][0]["text"],
                            "long_desc": vid["descriptionSnippet"]["runs"][0]["text"] if vid.get("descriptionSnippet") else None,
                            "channel": vid["longBylineText"]["runs"][0]["text"],
                            "duration": vid.get("lengthText", {}).get("simpleText", 0),
                            "views": vid.get("viewCountText", {}).get("simpleText", 0),
                            "url_suffix": watch_url,  # Watch link back!
                            "video_url": video_direct,  # Direct video MP4
                            "audio_url": audio_direct  # Direct audio extract!
                        }
                        results.append(res)
                if results and (self.max_results is None or len(results) >= self.max_results):
                    break
        except (KeyError, IndexError, json.JSONDecodeError):
            pass  # YouTube badle toh chill
        return results[:self.max_results] if self.max_results else results

    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos})
        if clear_cache: self.videos = []
        return result
