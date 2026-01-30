"""Reddit monitoring module using PRAW."""

import os
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

import praw
from praw.models import Submission, Comment

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

    @property
    def full_text(self) -> str:
        """Return combined title and body for analysis."""
        return f"{self.title} {self.body}".strip()


class RedditMonitor:
    """Monitor Reddit subreddits for relevant discussions."""

    def __init__(self):
        """Initialize Reddit API connection."""
        self.reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT", "ListenerAgent/1.0"),
        )
        self.keywords = [kw.lower() for kw in config.KEYWORDS]
        self.keyword_patterns = [
            re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
            for kw in config.KEYWORDS
        ]

    def _matches_keywords(self, text: str) -> list[str]:
        """Check if text contains any tracked keywords."""
        matched = []
        for kw, pattern in zip(config.KEYWORDS, self.keyword_patterns):
            if pattern.search(text):
                matched.append(kw)
        return matched

    def _is_within_timeframe(self, created_utc: float) -> bool:
        """Check if post is within the lookback period."""
        post_time = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
        return post_time >= cutoff

    def _submission_to_post(self, submission: Submission) -> RedditPost | None:
        """Convert PRAW submission to RedditPost."""
        if not self._is_within_timeframe(submission.created_utc):
            return None

        if submission.score < config.MIN_SCORE:
            return None

        body = submission.selftext if hasattr(submission, "selftext") else ""
        full_text = f"{submission.title} {body}"

        matched = self._matches_keywords(full_text)
        if not matched:
            return None

        return RedditPost(
            id=submission.id,
            subreddit=str(submission.subreddit),
            title=submission.title,
            body=body,
            author=str(submission.author) if submission.author else "[deleted]",
            score=submission.score,
            url=f"https://reddit.com{submission.permalink}",
            created_utc=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            num_comments=submission.num_comments,
            is_comment=False,
            matched_keywords=matched,
        )

    def _comment_to_post(
        self, comment: Comment, parent_title: str, subreddit: str
    ) -> RedditPost | None:
        """Convert PRAW comment to RedditPost."""
        if not self._is_within_timeframe(comment.created_utc):
            return None

        if comment.score < config.MIN_SCORE:
            return None

        matched = self._matches_keywords(comment.body)
        if not matched:
            return None

        return RedditPost(
            id=comment.id,
            subreddit=subreddit,
            title="",
            body=comment.body,
            author=str(comment.author) if comment.author else "[deleted]",
            score=comment.score,
            url=f"https://reddit.com{comment.permalink}",
            created_utc=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
            is_comment=True,
            parent_title=parent_title,
            matched_keywords=matched,
        )

    def fetch_subreddit(
        self, subreddit_name: str, include_comments: bool = True
    ) -> list[RedditPost]:
        """Fetch relevant posts from a subreddit."""
        posts = []
        subreddit = self.reddit.subreddit(subreddit_name)

        # Fetch new and hot posts
        submissions = []
        try:
            submissions.extend(list(subreddit.new(limit=config.MAX_POSTS_PER_SUBREDDIT)))
            submissions.extend(list(subreddit.hot(limit=config.MAX_POSTS_PER_SUBREDDIT // 2)))
        except Exception as e:
            print(f"Error fetching r/{subreddit_name}: {e}")
            return posts

        # Deduplicate submissions
        seen_ids = set()
        unique_submissions = []
        for sub in submissions:
            if sub.id not in seen_ids:
                seen_ids.add(sub.id)
                unique_submissions.append(sub)

        for submission in unique_submissions:
            post = self._submission_to_post(submission)
            if post:
                posts.append(post)

            # Also check top-level comments
            if include_comments:
                try:
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:20]:  # Top 20 comments
                        comment_post = self._comment_to_post(
                            comment, submission.title, subreddit_name
                        )
                        if comment_post:
                            posts.append(comment_post)
                except Exception:
                    pass  # Skip comment errors

        return posts

    def fetch_all(self, include_comments: bool = True) -> list[RedditPost]:
        """Fetch relevant posts from all configured subreddits."""
        all_posts = []

        for subreddit_name in config.SUBREDDITS:
            print(f"Scanning r/{subreddit_name}...")
            posts = self.fetch_subreddit(subreddit_name, include_comments)
            all_posts.extend(posts)
            print(f"  Found {len(posts)} relevant items")

        # Sort by score descending
        all_posts.sort(key=lambda p: p.score, reverse=True)

        return all_posts
