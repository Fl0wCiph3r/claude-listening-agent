"""Configuration for the Complete Listener Agent."""

import os

# =============================================================================
# REDDIT SETTINGS
# =============================================================================

SUBREDDITS = [
    "ChatGPT",
    "SideProject",
    "PassiveIncome",
    "EntrepreneurRideAlong",
    "juststart",
    "nocode",
    "microsaas",
]

# Keywords to track (case-insensitive)
KEYWORDS = [
    # AI related
    "AI",
    "ChatGPT",
    "Claude",
    "GPT",
    "artificial intelligence",
    "LLM",
    # Digital products
    "digital product",
    "info product",
    "infoproduct",
    "course",
    "ebook",
    "template",
    "guide",
    # Software/Tools
    "SaaS",
    "software",
    "tool",
    "automation",
    "workflow",
    # Money/Business
    "passive income",
    "side hustle",
    "make money",
    "monetize",
    "revenue",
    "MRR",
    "sales",
    # Platforms
    "Gumroad",
    "Notion template",
    "Canva template",
]

# =============================================================================
# YOUTUBE SETTINGS
# =============================================================================

# YouTube API key (set via environment variable)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# Search queries for YouTube
YOUTUBE_SEARCHES = [
    "make money with AI",
    "AI side hustle",
    "sell digital products",
    "create info products",
    "passive income AI",
]

# YouTube settings
YOUTUBE_VIDEOS_PER_SEARCH = 10  # Top videos per search
YOUTUBE_COMMENTS_PER_VIDEO = 30  # Comments to fetch per video
YOUTUBE_LOOKBACK_DAYS = 30  # Comments from last 30 days

# =============================================================================
# TWITTER/NITTER SETTINGS
# =============================================================================

# Nitter instances to try (in order of preference)
NITTER_INSTANCES = [
    "nitter.poast.org",
    "nitter.privacydev.net",
    "nitter.net",
    "nitter.cz",
]

# Twitter search queries
TWITTER_SEARCHES = [
    "info product launch",
    "digital product revenue",
    "course sales",
    "ebook launch",
    "made selling templates",
    "Gumroad revenue",
    "passive income update",
    "AI course",
    "ChatGPT prompts",
    "Notion templates",
]

# Twitter settings
TWITTER_TWEETS_PER_SEARCH = 30  # Tweets to fetch per search
TWITTER_LOOKBACK_DAYS = 7  # Tweets from last 7 days

# =============================================================================
# GENERAL SETTINGS
# =============================================================================

# Time range in days (for Reddit)
LOOKBACK_DAYS = 7

# Minimum score threshold
MIN_SCORE = 1

# Maximum posts per subreddit
MAX_POSTS_PER_SUBREDDIT = 50

# Report output directory
REPORT_DIR = "reports"

# Log file
LOG_FILE = "listener.log"

# =============================================================================
# SCRAPING SETTINGS
# =============================================================================

REQUEST_DELAY = 2.0  # Seconds between requests
REQUEST_TIMEOUT = 15  # Request timeout in seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
