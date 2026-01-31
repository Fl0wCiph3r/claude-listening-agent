"""Twitter monitoring via Nitter instances (no API/login required)."""

import re
import time
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

import config
from .models import Finding, Platform, ScanResult

logger = logging.getLogger(__name__)


class TwitterMonitor:
    """
    Monitor Twitter via Nitter instances.

    Nitter is a free and open source alternative Twitter front-end
    that allows scraping without authentication.

    IMPORTANT: No login, no API keys, no account credentials needed.
    Zero risk to your Twitter account.
    """

    def __init__(self):
        """Initialize Twitter monitor."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.working_instance = None
        self.cutoff_time = datetime.now(timezone.utc) - timedelta(days=config.TWITTER_LOOKBACK_DAYS)

    def _delay(self):
        """Add delay between requests."""
        time.sleep(config.REQUEST_DELAY + 1)  # Extra delay for Nitter

    def _find_working_instance(self) -> str | None:
        """Find a working Nitter instance."""
        if self.working_instance:
            return self.working_instance

        for instance in config.NITTER_INSTANCES:
            try:
                url = f"https://{instance}"
                response = self.session.get(
                    url,
                    timeout=config.REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                if response.status_code == 200:
                    self.working_instance = instance
                    logger.info(f"Using Nitter instance: {instance}")
                    return instance
            except Exception as e:
                logger.debug(f"Nitter instance {instance} failed: {e}")
                continue

        logger.error("No working Nitter instances found")
        return None

    def _parse_tweet_time(self, time_str: str) -> datetime | None:
        """Parse Nitter's time format."""
        time_str = time_str.lower().strip()
        now = datetime.now(timezone.utc)

        # Handle relative times
        patterns = [
            (r"(\d+)\s*s(ec)?(ond)?s?\s*ago", "seconds"),
            (r"(\d+)\s*m(in)?(ute)?s?\s*ago", "minutes"),
            (r"(\d+)\s*h(our)?s?\s*ago", "hours"),
            (r"(\d+)\s*d(ay)?s?\s*ago", "days"),
            (r"(\d+)\s*w(eek)?s?\s*ago", "weeks"),
            (r"(\d+)\s*mo(nth)?s?\s*ago", "months"),
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, time_str)
            if match:
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

        # Try parsing absolute dates
        date_formats = [
            "%b %d, %Y",
            "%d %b %Y",
            "%Y-%m-%d",
            "%b %d",
        ]

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(time_str, fmt)
                # Add current year if not present
                if parsed.year == 1900:
                    parsed = parsed.replace(year=now.year)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        return now

    def _parse_count(self, count_str: str) -> int:
        """Parse engagement count (e.g., '1.2K' -> 1200)."""
        if not count_str:
            return 0

        count_str = count_str.strip().upper()

        # Remove commas
        count_str = count_str.replace(",", "")

        # Handle K, M suffixes
        multipliers = {"K": 1000, "M": 1000000}

        for suffix, mult in multipliers.items():
            if suffix in count_str:
                try:
                    return int(float(count_str.replace(suffix, "")) * mult)
                except ValueError:
                    return 0

        try:
            return int(count_str)
        except ValueError:
            return 0

    def _scrape_search(self, query: str, instance: str) -> list[Finding]:
        """Scrape search results from a Nitter instance."""
        findings = []
        encoded_query = quote_plus(query)
        url = f"https://{instance}/search?f=tweets&q={encoded_query}"

        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find tweet containers
            tweets = soup.find_all("div", class_="timeline-item")
            if not tweets:
                # Try alternative selectors
                tweets = soup.find_all("div", class_="tweet-body")

            for tweet in tweets[:config.TWITTER_TWEETS_PER_SEARCH]:
                try:
                    finding = self._parse_tweet(tweet, instance, query)
                    if finding and finding.created_at >= self.cutoff_time:
                        findings.append(finding)
                except Exception as e:
                    logger.debug(f"Error parsing tweet: {e}")
                    continue

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limited on {instance}")
            else:
                logger.error(f"HTTP error on {instance}: {e}")
        except Exception as e:
            logger.error(f"Error scraping {instance}: {e}")

        return findings

    def _parse_tweet(self, tweet_elem, instance: str, query: str) -> Finding | None:
        """Parse a single tweet element."""
        # Get tweet content
        content_elem = tweet_elem.find("div", class_="tweet-content")
        if not content_elem:
            content_elem = tweet_elem.find("div", class_="tweet-body")

        if not content_elem:
            return None

        tweet_text = content_elem.get_text(strip=True)
        if not tweet_text:
            return None

        # Get author
        author_elem = tweet_elem.find("a", class_="username")
        if not author_elem:
            author_elem = tweet_elem.find("a", class_="fullname")
        author = author_elem.get_text(strip=True) if author_elem else "Unknown"
        author = author.lstrip("@")

        # Get tweet link
        link_elem = tweet_elem.find("a", class_="tweet-link")
        if not link_elem:
            link_elem = tweet_elem.find("a", href=re.compile(r"/status/\d+"))

        tweet_path = link_elem.get("href", "") if link_elem else ""
        tweet_id = ""
        if tweet_path:
            match = re.search(r"/status/(\d+)", tweet_path)
            if match:
                tweet_id = match.group(1)

        # Construct real Twitter URL
        twitter_url = f"https://twitter.com/{author}/status/{tweet_id}" if tweet_id else ""

        # Get timestamp
        time_elem = tweet_elem.find("span", class_="tweet-date")
        if not time_elem:
            time_elem = tweet_elem.find("a", class_="tweet-date")

        time_str = ""
        if time_elem:
            time_link = time_elem.find("a")
            if time_link:
                time_str = time_link.get("title", "") or time_link.get_text(strip=True)
            else:
                time_str = time_elem.get_text(strip=True)

        created_at = self._parse_tweet_time(time_str) if time_str else datetime.now(timezone.utc)

        # Get engagement stats
        stats = tweet_elem.find("div", class_="tweet-stats")
        likes = 0
        retweets = 0
        replies = 0

        if stats:
            # Find like count
            like_elem = stats.find("span", class_="icon-heart")
            if like_elem and like_elem.parent:
                likes = self._parse_count(like_elem.parent.get_text(strip=True))

            # Find retweet count
            rt_elem = stats.find("span", class_="icon-retweet")
            if rt_elem and rt_elem.parent:
                retweets = self._parse_count(rt_elem.parent.get_text(strip=True))

            # Find reply count
            reply_elem = stats.find("span", class_="icon-comment")
            if reply_elem and reply_elem.parent:
                replies = self._parse_count(reply_elem.parent.get_text(strip=True))

        return Finding(
            id=tweet_id or f"tweet_{hash(tweet_text)}",
            platform=Platform.TWITTER,
            title=tweet_text[:100] + "..." if len(tweet_text) > 100 else tweet_text,
            body=tweet_text,
            author=author,
            url=twitter_url,
            created_at=created_at,
            score=likes,
            comments_count=replies,
            shares_count=retweets,
            source_name=f"Search: {query}",
            matched_keywords=[query],
        )

    def fetch_all(self, progress_callback=None) -> ScanResult:
        """Fetch findings from all Twitter searches via Nitter."""
        start_time = time.time()
        all_findings = []
        errors = []

        # Find working instance
        instance = self._find_working_instance()
        if not instance:
            return ScanResult(
                platform=Platform.TWITTER,
                findings=[],
                errors=["No working Nitter instances available. Twitter data skipped."],
                scan_time_seconds=time.time() - start_time,
            )

        print(f"    Using Nitter instance: {instance}")

        total_searches = len(config.TWITTER_SEARCHES)

        for i, query in enumerate(config.TWITTER_SEARCHES, 1):
            if progress_callback:
                progress_callback(f"[{i}/{total_searches}] Searching: '{query}'")
            else:
                print(f"    [{i}/{total_searches}] Searching: '{query}'")

            try:
                findings = self._scrape_search(query, instance)
                all_findings.extend(findings)
                print(f"      Found {len(findings)} tweets")
            except Exception as e:
                error_msg = f"Error searching '{query}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)

                # Try next instance if current one fails
                self.working_instance = None
                instance = self._find_working_instance()
                if not instance:
                    errors.append("All Nitter instances failed")
                    break

            self._delay()

        # Remove duplicates
        seen_ids = set()
        unique_findings = []
        for finding in all_findings:
            if finding.id not in seen_ids:
                seen_ids.add(finding.id)
                unique_findings.append(finding)

        # Sort by engagement
        unique_findings.sort(key=lambda f: f.engagement_score, reverse=True)

        return ScanResult(
            platform=Platform.TWITTER,
            findings=unique_findings,
            errors=errors,
            scan_time_seconds=time.time() - start_time,
        )
