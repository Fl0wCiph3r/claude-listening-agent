# Complete Listener Agent

Monitor online discussions about AI products, digital products, and making money online. Automatically categorizes findings into actionable buckets for content creation and product development.

**Monitors 3 platforms:**
- 🔴 **Reddit** - Tech/SaaS discussions (web scraping)
- 🐦 **Twitter/X** - Info product launches (via Nitter - no login required)
- 📺 **YouTube** - Audience questions (API or scraping)

## Features

- **Multi-Platform Monitoring**: Reddit, Twitter, and YouTube in one scan
- **Smart Categorization**: Automatically sorts findings into:
  - **Questions** - Content ideas (what people want to learn)
  - **Pain Points** - Product opportunities (problems to solve)
  - **Success Stories** - Competitive intelligence (what's working)
- **Complete Reports**: Detailed markdown reports with top insights
- **Zero Risk**: Twitter via Nitter (no login/auth required)
- **Graceful Failures**: If one platform fails, others continue

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set Up YouTube API

For better YouTube results, get a free API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable "YouTube Data API v3"
4. Create credentials > API Key
5. Set the environment variable:

```bash
export YOUTUBE_API_KEY=your_api_key_here
```

**Note:** YouTube works without an API key using web scraping, but results are limited.

### 3. Run the Listener

```bash
# Full scan (all platforms) - recommended
python run_complete.py

# Quick mode (faster, less thorough)
python run_complete.py --quick

# Single platform
python run_complete.py --reddit
python run_complete.py --twitter
python run_complete.py --youtube

# Reddit only (original script still works)
python main.py
```

## What It Monitors

### Reddit (7 subreddits)
- r/ChatGPT, r/SideProject, r/PassiveIncome
- r/EntrepreneurRideAlong, r/juststart
- r/nocode, r/microsaas

### Twitter/X (10 search terms)
- "info product launch", "digital product revenue"
- "course sales", "ebook launch"
- "Gumroad revenue", "passive income update"
- "AI course", "ChatGPT prompts", "Notion templates"

### YouTube (5 search terms)
- "make money with AI", "AI side hustle"
- "sell digital products", "create info products"
- "passive income AI"

## How Categorization Works

| Category | Trigger Patterns | Use Case |
|----------|-----------------|----------|
| **Questions** | "how do I", "what's the best", "anyone know", ends with ? | Content ideas |
| **Pain Points** | "struggling", "frustrated", "can't figure out", "doesn't work" | Product opportunities |
| **Success Stories** | "made $X", "launched", "revenue", "MRR", "first sale" | Competitive intelligence |

## Output

Reports are saved to `reports/complete_report_YYYY-MM-DD.md`

### Report Structure

```markdown
# Complete Intelligence Report

## Executive Summary
- Total findings by category
- Breakdown by platform

## Top Insights
- Top 5 content ideas
- Top 5 product opportunities
- Top 5 competitor strategies

## Twitter/X Findings
### Questions | Pain Points | Success Stories

## Reddit Findings
### Questions | Pain Points | Success Stories

## YouTube Comments
### Questions | Pain Points | Success Stories
```

## Configuration

Edit `config.py` to customize:

```python
# Subreddits
SUBREDDITS = ["ChatGPT", "SideProject", ...]

# Twitter searches
TWITTER_SEARCHES = ["info product launch", ...]

# YouTube searches
YOUTUBE_SEARCHES = ["make money with AI", ...]

# Keywords
KEYWORDS = ["AI", "digital product", "SaaS", ...]

# Timing
REQUEST_DELAY = 2.0  # Be nice to servers
LOOKBACK_DAYS = 7    # How far back to search
```

## Project Structure

```
.
├── run_complete.py      # Main entry point (all platforms)
├── main.py              # Reddit-only script
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── listener/
│   ├── models.py            # Unified data models
│   ├── reddit_monitor.py    # Reddit scraper
│   ├── twitter_monitor.py   # Twitter/Nitter scraper
│   ├── youtube_monitor.py   # YouTube API/scraper
│   ├── categorizer.py       # Post categorization
│   ├── report_generator.py  # Reddit-only reports
│   └── complete_report.py   # Multi-platform reports
├── reports/             # Generated reports
└── listener.log         # Debug logs
```

## Safety & Privacy

- **Twitter**: Uses Nitter instances only - no login, no API keys, no account risk
- **Reddit**: Web scraping with rate limiting - no API required
- **YouTube**: API key is free and has generous quotas (10,000/day)

## Troubleshooting

### Twitter not working?
Nitter instances can go offline. The agent tries multiple instances automatically. If all fail, Twitter is skipped.

### YouTube comments limited?
Without an API key, YouTube scraping is limited. Set `YOUTUBE_API_KEY` for better results.

### Too slow?
Use `--quick` mode or scan individual platforms:
```bash
python run_complete.py --quick
python run_complete.py --reddit  # fastest
```

## Runtime

- **Full scan**: ~10-15 minutes
- **Quick mode**: ~5-8 minutes
- **Single platform**: ~2-5 minutes

---

Built for discovering content ideas, product opportunities, and competitive intelligence in the AI/digital products space.
