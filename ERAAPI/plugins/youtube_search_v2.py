import json, re, requests
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus



class YouTubeConfig:
    BASE_SEARCH_URL = "https://youtube.com/results"
    BASE_WATCH_URL = "https://www.youtube.com/watch?v={}"
    BASE_VIDEO_URL = "https://www.youtube.com{}"
    MAX_RETRIES = 3
    YT_INITIAL_DATA_PATTERN = r'ytInitialData\s*=\s*({.+?});'
    YT_PLAYER_RESPONSE_PATTERN = r'ytInitialPlayerResponse\s*=\s*({.+?});'


def _extract_json_from_html(html: str, pattern: str) -> Optional[Dict[str, Any]]:
    match = re.search(pattern, html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def _build_search_url(search_terms: str) -> str:
    encoded_query = quote_plus(search_terms)
    return f"{YouTubeConfig.BASE_SEARCH_URL}?search_query={encoded_query}"


def _get_video_data_path() -> List[str]:
    return [
        "contents",
        "twoColumnSearchResultsRenderer",
        "primaryContents",
        "sectionListRenderer",
        "contents"
    ]


def _extract_video_info(video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    video_id = video_data.get("videoId")
    if not video_id:
        return None

    return {
        "id": video_id,
        "url": YouTubeConfig.BASE_VIDEO_URL.format(
            video_data["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        )
    }


class FastYoutubeSearch:
    def __init__(self, search_terms: str, max_results: Optional[int] = None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self._fast_search()

    def _fast_search(self) -> List[Dict[str, str]]:
        url = _build_search_url(self.search_terms)
        response = requests.get(url).text

        for _ in range(YouTubeConfig.MAX_RETRIES):
            if "ytInitialData" in response:
                break
            response = requests.get(url).text

        data = _extract_json_from_html(response, YouTubeConfig.YT_INITIAL_DATA_PATTERN)
        if not data:
            return []

        results = []
        video_path = _get_video_data_path()

        try:
            contents = data
            for key in video_path:
                contents = contents[key]

            for content in contents:
                for item in content["itemSectionRenderer"]["contents"]:
                    if "videoRenderer" in item:
                        vid = item["videoRenderer"]
                        video_info = _extract_video_info(vid)
                        if video_info:
                            results.append(video_info)
                            if self.max_results and len(results) >= self.max_results:
                                return results
        except (KeyError, TypeError):
            pass

        return results

    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos})
        if clear_cache: self.videos = []
        return result


class YoutubeSearch:
    def __init__(self, search_terms: str, max_results: Optional[int] = None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self._search()

    def _search(self) -> List[Dict[str, Any]]:
        url = _build_search_url(self.search_terms)
        response = requests.get(url).text

        while "ytInitialData" not in response:
            response = requests.get(url).text

        data = _extract_json_from_html(response, YouTubeConfig.YT_INITIAL_DATA_PATTERN)
        if not data:
            return []

        results = []
        video_path = _get_video_data_path()

        try:
            contents = data
            for key in video_path:
                contents = contents[key]

            for content in contents:
                for item in content["itemSectionRenderer"]["contents"]:
                    if "videoRenderer" in item:
                        vid = item["videoRenderer"]
                        video_info = self._extract_detailed_video_info(vid)
                        if video_info:
                            results.append(video_info)
                            if self.max_results and len(results) >= self.max_results:
                                return results[:self.max_results]
        except (KeyError, IndexError, json.JSONDecodeError):
            pass

        return results[:self.max_results] if self.max_results else results

    def _extract_detailed_video_info(self, video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        video_id = video_data.get("videoId")
        if not video_id:
            return None

        watch_suffix = video_data["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        watch_url = YouTubeConfig.BASE_VIDEO_URL.format(watch_suffix)

        video_direct, audio_direct = self._get_direct_urls(video_id, watch_url)

        return {
            "id": video_id,
            "thumbnails": self._extract_thumbnails(video_data),
            "title": self._extract_title(video_data),
            "long_desc": self._extract_description(video_data),
            "channel": self._extract_channel(video_data),
            "duration": self._extract_duration(video_data),
            "views": self._extract_views(video_data),
            "url_suffix": watch_url,
            "video_url": video_direct,
            "audio_url": audio_direct
        }

    def _get_direct_urls(self, video_id: str, fallback_url: str) -> tuple[str, str]:
        video_page_url = YouTubeConfig.BASE_WATCH_URL.format(video_id)
        video_response = requests.get(video_page_url).text

        player_data = _extract_json_from_html(video_response, YouTubeConfig.YT_PLAYER_RESPONSE_PATTERN)
        if not player_data:
            return fallback_url, fallback_url

        streaming_data = player_data.get("streamingData", {})
        if "adaptiveFormats" not in streaming_data:
            return fallback_url, fallback_url

        formats = streaming_data["adaptiveFormats"]
        return (
            self._get_best_format_url(formats, "video/mp4") or fallback_url,
            self._get_best_format_url(formats, "audio/") or fallback_url
        )

    def _get_best_format_url(self, formats: List[Dict[str, Any]], mime_type: str) -> Optional[str]:
        matching_formats = [f for f in formats if f.get("mimeType", "").startswith(mime_type)]
        if not matching_formats:
            return None

        best_format = max(matching_formats, key=lambda x: int(x.get("bitrate", 0)))
        return best_format.get("url")

    def _extract_thumbnails(self, video_data: Dict[str, Any]) -> List[str]:
        return [thumb["url"] for thumb in video_data["thumbnail"]["thumbnails"]]

    def _extract_title(self, video_data: Dict[str, Any]) -> str:
        return video_data["title"]["runs"][0]["text"]

    def _extract_description(self, video_data: Dict[str, Any]) -> Optional[str]:
        desc_snippet = video_data.get("descriptionSnippet")
        if desc_snippet and desc_snippet.get("runs"):
            return desc_snippet["runs"][0]["text"]
        return None

    def _extract_channel(self, video_data: Dict[str, Any]) -> str:
        return video_data["longBylineText"]["runs"][0]["text"]

    def _extract_duration(self, video_data: Dict[str, Any]) -> str:
        length_text = video_data.get("lengthText", {})
        return length_text.get("simpleText", "0")

    def _extract_views(self, video_data: Dict[str, Any]) -> str:
        view_count = video_data.get("viewCountText", {})
        return view_count.get("simpleText", "0")

    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos})
        if clear_cache: self.videos = []
        return result
