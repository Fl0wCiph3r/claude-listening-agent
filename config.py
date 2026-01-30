"""Configuration for the Reddit Listener Agent."""

# Subreddits to monitor
SUBREDDITS = [
    "Entrepreneur",
    "EntrepreneurRideAlong",
    "SideProject",
    "ChatGPT",
    "PassiveIncome",
    "DigitalMarketing",
    "SaaS",
]

# Keywords to track (case-insensitive)
KEYWORDS = [
    "AI",
    "ChatGPT",
    "Claude",
    "digital product",
    "info product",
    "course",
    "ebook",
    "template",
    "SaaS",
    "automation",
    "side hustle",
    "passive income",
    "make money",
    "GPT",
    "LLM",
    "artificial intelligence",
    "online business",
    "productize",
    "monetize",
]

# Time range in days
LOOKBACK_DAYS = 7

# Minimum score threshold (filters out low-quality posts)
MIN_SCORE = 1

# Maximum posts to fetch per subreddit
MAX_POSTS_PER_SUBREDDIT = 100

# Report output directory
REPORT_DIR = "reports"
