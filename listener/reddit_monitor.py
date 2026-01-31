"""Reddit monitoring module using web scraping (no API required)."""

import re
import time
import json
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config


@dataclass
class RedditPost:
    """Represents a Reddit post or comment."""

    id: str
    subreddit: str
    title: str
    body: str
    author: str
    score: int
    url: str
    created_utc: datetime
    num_comments: int = 0
    is_comment: bool = False
    parent_title: str = ""
    matched_keywords: list = field(default_factory=list)
    top_comments: list = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Return combined title and body for analysis."""
        return f"{self.title} {self.body}".strip()


class RedditScraper:
    """Scrape Reddit for relevant discussions without using the API."""

    BASE_URL = "https://old.reddit.com"

    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        self.keywords = [kw.lower() for kw in config.KEYWORDS]
        self.keyword_patterns = [
            re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for kw in config.KEYWORDS
        ]
        self.cutoff_time = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)

    def _delay(self):
        """Add delay between requests to be respectful."""
        time.sleep(config.REQUEST_DELAY)

    def _matches_keywords(self, text: str) -> list[str]:
        """Check if text contains any tracked keywords."""
        matched = []
        for kw, pattern in zip(config.KEYWORDS, self.keyword_patterns):
            if pattern.search(text):
                matched.append(kw)
        return matched

    def _parse_time_ago(self, time_str: str) -> datetime | None:
        """Parse Reddit's 'X hours ago' format to datetime."""
        time_str = time_str.lower().strip()
        now = datetime.now(timezone.utc)

        patterns = [
            (r"(\d+)\s*seconds?\s*ago", "seconds"),
            (r"(\d+)\s*minutes?\s*ago", "minutes"),
            (r"(\d+)\s*hours?\s*ago", "hours"),
            (r"(\d+)\s*days?\s*ago", "days"),
            (r"(\d+)\s*weeks?\s*ago", "weeks"),
            (r"(\d+)\s*months?\s*ago", "months"),
            (r"(\d+)\s*years?\s*ago", "years"),
            (r"just now", "now"),
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, time_str)
            if match:
                if unit == "now":
                    return now
                value = int(match.group(1))
                if unit == "seconds":
                    return now - timedelta(seconds=value)
                elif unit == "minutes":
                    return now - timedelta(minutes=value)
                elif unit == "hours":
                    return now - timedelta(hours=value)
                elif unit == "days":
                    return now - timedelta(days=value)
                elif unit == "weeks":
                    return now - timedelta(weeks=value)
                elif unit == "months":
                    return now - timedelta(days=value * 30)
                elif unit == "years":
                    return now - timedelta(days=value * 365)

        return None

    def _parse_score(self, score_str: str) -> int:
        """Parse score string to integer."""
        score_str = score_str.lower().strip()
        if score_str in ("•", "-", "vote", ""):
            return 0

        # Handle 'k' suffix (e.g., "1.2k")
        if "k" in score_str:
            try:
                return int(float(score_str.replace("k", "")) * 1000)
            except ValueError:
                return 0

        try:
            return int(score_str.replace(",", ""))
        except ValueError:
            return 0

    def _fetch_page(self, url: str) -> BeautifulSoup | None:
        """Fetch and parse a page."""
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"    Error fetching {url}: {e}")
            return None

    def _scrape_post_comments(self, post_url: str, limit: int = 5) -> list[dict]:
        """Scrape top comments from a post."""
        comments = []
        self._delay()

        soup = self._fetch_page(post_url)
        if not soup:
            return comments

        # Find comment area
        comment_area = soup.find("div", class_="commentarea")
        if not comment_area:
            return comments

        # Get top-level comments
        comment_divs = comment_area.find_all("div", class_="comment", recursive=False)
        if not comment_divs:
            # Try nested structure
            sitetable = comment_area.find("div", class_="sitetable")
            if sitetable:
                comment_divs = sitetable.find_all("div", class_="thing", recursive=False)

        for comment_div in comment_divs[:limit]:
            try:
                # Skip deleted/removed
                if "deleted" in comment_div.get("class", []):
                    continue

                # Get comment body
                body_div = comment_div.find("div", class_="md")
                if not body_div:
                    continue
                body = body_div.get_text(strip=True)

                # Get score
                score_elem = comment_div.find("span", class_="score")
                score = 0
                if score_elem:
                    score_text = score_elem.get_text(strip=True)
                    score = self._parse_score(score_text.split()[0] if score_text else "0")

                # Get author
                author_elem = comment_div.find("a", class_="author")
                author = author_elem.get_text(strip=True) if author_elem else "[deleted]"

                if body and len(body) > 10:
                    comments.append({
                        "body": body[:500],
                        "score": score,
                        "author": author,
                    })

            except Exception:
                continue

        return comments

    def _scrape_subreddit_page(self, subreddit: str, after: str = None) -> tuple[list[dict], str | None]:
        """Scrape a single page of a subreddit."""
        url = f"{self.BASE_URL}/r/{subreddit}/new/"
        if after:
            url += f"?after={after}"

        soup = self._fetch_page(url)
        if not soup:
            return [], None

        posts = []
        next_page = None

        # Find all post entries
        site_table = soup.find("div", id="siteTable")
        if not site_table:
            return [], None

        things = site_table.find_all("div", class_="thing")

        for thing in things:
            try:
                # Skip promoted/ads
                if "promoted" in thing.get("class", []) or "stickied" in thing.get("class", []):
                    continue

                # Get post ID
                post_id = thing.get("data-fullname", "").replace("t3_", "")
                if not post_id:
                    continue

                # Get title
                title_elem = thing.find("a", class_="title")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                # Get URL
                post_url = thing.get("data-url", "")
                permalink = thing.get("data-permalink", "")
                full_url = f"https://reddit.com{permalink}" if permalink else post_url

                # Get score
                score_elem = thing.find("div", class_="score")
                score = 0
                if score_elem:
                    score_text = score_elem.get("title", "") or score_elem.get_text(strip=True)
                    score = self._parse_score(score_text)

                # Get time
                time_elem = thing.find("time")
                created_utc = None
                if time_elem:
                    # Try datetime attribute first
                    dt_str = time_elem.get("datetime")
                    if dt_str:
                        try:
                            created_utc = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    # Fallback to parsing text
                    if not created_utc:
                        time_text = time_elem.get_text(strip=True)
                        created_utc = self._parse_time_ago(time_text)

                if not created_utc:
                    created_utc = datetime.now(timezone.utc)

                # Check if within time range
                if created_utc < self.cutoff_time:
                    continue

                # Get author
                author_elem = thing.find("a", class_="author")
                author = author_elem.get_text(strip=True) if author_elem else "[deleted]"

                # Get comment count
                comments_elem = thing.find("a", class_="comments")
                num_comments = 0
                if comments_elem:
                    comments_text = comments_elem.get_text(strip=True)
                    match = re.search(r"(\d+)", comments_text)
                    if match:
                        num_comments = int(match.group(1))

                # Get self text (if available in listing)
                body = ""
                expando = thing.find("div", class_="expando")
                if expando:
                    md = expando.find("div", class_="md")
                    if md:
                        body = md.get_text(strip=True)[:1000]

                posts.append({
                    "id": post_id,
                    "title": title,
                    "body": body,
                    "author": author,
                    "score": score,
                    "url": full_url,
                    "permalink": f"{self.BASE_URL}{permalink}",
                    "created_utc": created_utc,
                    "num_comments": num_comments,
                })

            except Exception as e:
                continue

        # Find next page
        next_btn = soup.find("span", class_="next-button")
        if next_btn:
            next_link = next_btn.find("a")
            if next_link:
                href = next_link.get("href", "")
                match = re.search(r"after=([^&]+)", href)
                if match:
                    next_page = match.group(1)

        return posts, next_page

    def fetch_subreddit(self, subreddit: str, include_comments: bool = True) -> list[RedditPost]:
        """Fetch relevant posts from a subreddit."""
        posts = []
        after = None
        pages_fetched = 0
        max_pages = 3  # Limit pages to avoid too many requests

        while pages_fetched < max_pages:
            self._delay()
            page_posts, after = self._scrape_subreddit_page(subreddit, after)

            if not page_posts:
                break

            for post_data in page_posts:
                # Check keywords
                full_text = f"{post_data['title']} {post_data['body']}"
                matched = self._matches_keywords(full_text)

                if not matched:
                    continue

                if post_data["score"] < config.MIN_SCORE:
                    continue

                # Fetch top comments if enabled
                top_comments = []
                if include_comments and post_data["num_comments"] > 0:
                    print(f"      Fetching comments for: {post_data['title'][:50]}...")
                    top_comments = self._scrape_post_comments(post_data["permalink"], limit=3)

                post = RedditPost(
                    id=post_data["id"],
                    subreddit=subreddit,
                    title=post_data["title"],
                    body=post_data["body"],
                    author=post_data["author"],
                    score=post_data["score"],
                    url=post_data["url"],
                    created_utc=post_data["created_utc"],
                    num_comments=post_data["num_comments"],
                    is_comment=False,
                    matched_keywords=matched,
                    top_comments=top_comments,
                )
                posts.append(post)

            pages_fetched += 1

            if not after:
                break

            if len(posts) >= config.MAX_POSTS_PER_SUBREDDIT:
                break

        return posts[:config.MAX_POSTS_PER_SUBREDDIT]

    def fetch_all(self, include_comments: bool = True) -> list[RedditPost]:
        """Fetch relevant posts from all configured subreddits."""
        all_posts = []

        print(f"Scanning {len(config.SUBREDDITS)} subreddits...")
        print(f"Looking for posts from the last {config.LOOKBACK_DAYS} days")
        print()

        for i, subreddit_name in enumerate(config.SUBREDDITS, 1):
            print(f"[{i}/{len(config.SUBREDDITS)}] Scanning r/{subreddit_name}...")
            try:
                posts = self.fetch_subreddit(subreddit_name, include_comments)
                all_posts.extend(posts)
                print(f"    Found {len(posts)} relevant posts")
            except Exception as e:
                print(f"    Error: {e}")

        # Sort by score descending
        all_posts.sort(key=lambda p: p.score, reverse=True)

        return all_posts


# Alias for backwards compatibility
RedditMonitor = RedditScraper
