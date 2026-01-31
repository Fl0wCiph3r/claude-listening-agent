"""Unified data models for all platforms."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Platform(Enum):
    """Source platform for findings."""
    REDDIT = "reddit"
    TWITTER = "twitter"
    YOUTUBE = "youtube"


class Category(Enum):
    """Content categories for analysis."""
    QUESTION = "question"  # Content ideas
    PAIN_POINT = "pain_point"  # Product opportunities
    SUCCESS_STORY = "success"  # Competitive intelligence
    UNCATEGORIZED = "uncategorized"


@dataclass
class Finding:
    """
    Unified data model for findings from any platform.

    This provides a consistent structure across Reddit posts,
    Twitter tweets, and YouTube comments.
    """
    id: str
    platform: Platform
    title: str  # Post title, tweet text preview, or video title
    body: str  # Full text content
    author: str
    url: str
    created_at: datetime

    # Engagement metrics (platform-specific)
    score: int = 0  # Upvotes, likes, etc.
    comments_count: int = 0  # Number of replies/comments
    shares_count: int = 0  # Retweets, shares

    # Platform-specific context
    source_name: str = ""  # Subreddit name, video title, etc.
    parent_url: str = ""  # Link to parent (for comments)

    # Analysis
    matched_keywords: list = field(default_factory=list)
    category: Category = Category.UNCATEGORIZED
    category_confidence: float = 0.0
    category_signals: list = field(default_factory=list)

    # Additional context
    replies: list = field(default_factory=list)  # Top replies/comments

    @property
    def full_text(self) -> str:
        """Return combined title and body for analysis."""
        return f"{self.title} {self.body}".strip()

    @property
    def platform_icon(self) -> str:
        """Return emoji icon for the platform."""
        icons = {
            Platform.REDDIT: "🔴",
            Platform.TWITTER: "🐦",
            Platform.YOUTUBE: "📺",
        }
        return icons.get(self.platform, "📌")

    @property
    def engagement_score(self) -> int:
        """Calculate a unified engagement score."""
        # Weight: likes/upvotes + comments*2 + shares*3
        return self.score + (self.comments_count * 2) + (self.shares_count * 3)


@dataclass
class ScanResult:
    """Results from scanning a single platform."""
    platform: Platform
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scan_time_seconds: float = 0.0

    @property
    def success(self) -> bool:
        """Check if scan was successful (has findings or no errors)."""
        return len(self.findings) > 0 or len(self.errors) == 0

    @property
    def questions(self) -> list[Finding]:
        """Get findings categorized as questions."""
        return [f for f in self.findings if f.category == Category.QUESTION]

    @property
    def pain_points(self) -> list[Finding]:
        """Get findings categorized as pain points."""
        return [f for f in self.findings if f.category == Category.PAIN_POINT]

    @property
    def success_stories(self) -> list[Finding]:
        """Get findings categorized as success stories."""
        return [f for f in self.findings if f.category == Category.SUCCESS_STORY]


@dataclass
class CompleteReport:
    """Complete report from all platforms."""
    reddit: ScanResult = None
    twitter: ScanResult = None
    youtube: ScanResult = None
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

    @property
    def all_findings(self) -> list[Finding]:
        """Get all findings from all platforms."""
        findings = []
        if self.reddit:
            findings.extend(self.reddit.findings)
        if self.twitter:
            findings.extend(self.twitter.findings)
        if self.youtube:
            findings.extend(self.youtube.findings)
        return findings

    @property
    def total_count(self) -> int:
        """Get total number of findings."""
        return len(self.all_findings)

    def get_by_category(self, category: Category) -> list[Finding]:
        """Get all findings for a specific category."""
        return [f for f in self.all_findings if f.category == category]

    @property
    def questions(self) -> list[Finding]:
        return self.get_by_category(Category.QUESTION)

    @property
    def pain_points(self) -> list[Finding]:
        return self.get_by_category(Category.PAIN_POINT)

    @property
    def success_stories(self) -> list[Finding]:
        return self.get_by_category(Category.SUCCESS_STORY)
