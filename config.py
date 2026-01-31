"""Configuration for the Reddit Listener Agent (Web Scraping Version)."""

# Subreddits to monitor
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

# Time range in days
LOOKBACK_DAYS = 7

# Minimum score threshold (filters out low-quality posts)
MIN_SCORE = 1

# Maximum posts to fetch per subreddit
MAX_POSTS_PER_SUBREDDIT = 50

# Report output directory
REPORT_DIR = "reports"

# Scraping settings
REQUEST_DELAY = 2.0  # Seconds between requests (be respectful)
REQUEST_TIMEOUT = 15  # Seconds before request times out
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
