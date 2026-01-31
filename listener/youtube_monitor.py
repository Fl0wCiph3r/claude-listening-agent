"""YouTube monitoring module using YouTube Data API v3 with web scraping fallback."""

import re
import time
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlencode

import requests
from bs4 import BeautifulSoup

import config
from .models import Finding, Platform, ScanResult

logger = logging.getLogger(__name__)


class YouTubeMonitor:
    """Monitor YouTube for relevant videos and comments."""

    def __init__(self):
        """Initialize YouTube monitor."""
        self.api_key = config.YOUTUBE_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.use_api = bool(self.api_key)

    def _delay(self):
        """Add delay between requests."""
        time.sleep(config.REQUEST_DELAY)

    # =========================================================================
    # YouTube Data API v3 Methods
    # =========================================================================

    def _api_search_videos(self, query: str) -> list[dict]:
        """Search for videos using YouTube Data API."""
        if not self.api_key:
            return []

        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": self.api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": config.YOUTUBE_VIDEOS_PER_SEARCH,
            "order": "relevance",
            "publishedAfter": (
                datetime.now(timezone.utc) - timedelta(days=config.YOUTUBE_LOOKBACK_DAYS)
            ).isoformat(),
        }

        try:
            response = self.session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})
                if video_id:
                    videos.append({
                        "id": video_id,
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    })
            return videos

        except Exception as e:
            logger.error(f"YouTube API search error: {e}")
            return []

    def _api_get_comments(self, video_id: str, video_title: str) -> list[Finding]:
        """Get comments for a video using YouTube Data API."""
        if not self.api_key:
            return []

        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "key": self.api_key,
            "videoId": video_id,
            "part": "snippet",
            "maxResults": config.YOUTUBE_COMMENTS_PER_VIDEO,
            "order": "relevance",
        }

        findings = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=config.YOUTUBE_LOOKBACK_DAYS)

        try:
            response = self.session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})

                # Parse date
                published_str = snippet.get("publishedAt", "")
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    published_at = datetime.now(timezone.utc)

                # Skip old comments
                if published_at < cutoff:
                    continue

                comment_text = snippet.get("textDisplay", "")
                # Strip HTML tags
                comment_text = re.sub(r"<[^>]+>", "", comment_text)

                finding = Finding(
                    id=item.get("id", ""),
                    platform=Platform.YOUTUBE,
                    title=video_title,
                    body=comment_text,
                    author=snippet.get("authorDisplayName", "Unknown"),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    created_at=published_at,
                    score=snippet.get("likeCount", 0),
                    source_name=video_title,
                    parent_url=f"https://www.youtube.com/watch?v={video_id}",
                )
                findings.append(finding)

        except Exception as e:
            logger.error(f"YouTube API comments error for {video_id}: {e}")

        return findings

    # =========================================================================
    # Web Scraping Fallback Methods
    # =========================================================================

    def _scrape_search_videos(self, query: str) -> list[dict]:
        """Search for videos using web scraping (fallback)."""
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"

        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            # YouTube returns JSON data in a script tag
            # Look for video IDs in the HTML
            videos = []
            video_ids = set()

            # Find video IDs using regex
            pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            matches = re.findall(pattern, response.text)

            for video_id in matches[:config.YOUTUBE_VIDEOS_PER_SEARCH]:
                if video_id not in video_ids:
                    video_ids.add(video_id)
                    videos.append({
                        "id": video_id,
                        "title": "",  # Would need additional request
                        "channel": "",
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    })

            return videos

        except Exception as e:
            logger.error(f"YouTube scrape search error: {e}")
            return []

    def _scrape_video_info(self, video_id: str) -> dict:
        """Get video info via scraping."""
        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            # Extract title from HTML
            title_match = re.search(r'<title>([^<]+)</title>', response.text)
            title = title_match.group(1).replace(" - YouTube", "").strip() if title_match else ""

            return {"id": video_id, "title": title, "url": url}

        except Exception as e:
            logger.error(f"YouTube scrape video info error: {e}")
            return {"id": video_id, "title": "", "url": url}

    # =========================================================================
    # Main Public Methods
    # =========================================================================

    def search_and_get_comments(self, query: str, progress_callback=None) -> list[Finding]:
        """Search for videos and extract comments."""
        findings = []

        # Search for videos
        if self.use_api:
            videos = self._api_search_videos(query)
        else:
            videos = self._scrape_search_videos(query)
            self._delay()

        if not videos:
            logger.warning(f"No videos found for query: {query}")
            return findings

        # Get comments for each video
        for i, video in enumerate(videos):
            video_id = video.get("id")
            video_title = video.get("title", "")

            # If we don't have the title (from scraping), fetch it
            if not video_title and not self.use_api:
                info = self._scrape_video_info(video_id)
                video_title = info.get("title", f"Video {video_id}")
                self._delay()

            if progress_callback:
                progress_callback(f"      Fetching comments from: {video_title[:50]}...")

            if self.use_api:
                video_findings = self._api_get_comments(video_id, video_title)
            else:
                # Web scraping for comments is very limited due to JS rendering
                # Just create a finding for the video itself
                video_findings = [
                    Finding(
                        id=video_id,
                        platform=Platform.YOUTUBE,
                        title=video_title,
                        body=f"Video about: {query}",
                        author="",
                        url=video.get("url", f"https://www.youtube.com/watch?v={video_id}"),
                        created_at=datetime.now(timezone.utc),
                        source_name=video_title,
                    )
                ]

            findings.extend(video_findings)
            self._delay()

        return findings

    def fetch_all(self, progress_callback=None) -> ScanResult:
        """Fetch findings from all YouTube searches."""
        start_time = time.time()
        all_findings = []
        errors = []

        if not self.use_api:
            logger.warning("YouTube API key not set - using limited web scraping")
            print("    Note: Set YOUTUBE_API_KEY for better results")

        total_searches = len(config.YOUTUBE_SEARCHES)

        for i, query in enumerate(config.YOUTUBE_SEARCHES, 1):
            if progress_callback:
                progress_callback(f"[{i}/{total_searches}] Searching: '{query}'")
            else:
                print(f"    [{i}/{total_searches}] Searching: '{query}'")

            try:
                findings = self.search_and_get_comments(query, progress_callback)
                all_findings.extend(findings)
                print(f"      Found {len(findings)} comments")
            except Exception as e:
                error_msg = f"Error searching '{query}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)

            self._delay()

        # Remove duplicates based on ID
        seen_ids = set()
        unique_findings = []
        for finding in all_findings:
            if finding.id not in seen_ids:
                seen_ids.add(finding.id)
                unique_findings.append(finding)

        return ScanResult(
            platform=Platform.YOUTUBE,
            findings=unique_findings,
            errors=errors,
            scan_time_seconds=time.time() - start_time,
        )
