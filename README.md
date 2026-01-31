# Reddit Listener Agent

Monitor online discussions about AI products, digital products, and making money with AI. Automatically categorizes findings into actionable buckets for content creation and product development.

**No Reddit API required** - uses web scraping to gather data.

## Features

- **Reddit Monitoring**: Scrapes multiple subreddits for relevant discussions
- **Keyword Tracking**: Finds posts mentioning AI, digital products, SaaS, etc.
- **Smart Categorization**: Automatically sorts findings into:
  - **Questions** - Content ideas (what people want to learn)
  - **Pain Points** - Product opportunities (problems to solve)
  - **Success Stories** - Competitive intelligence (what's working)
- **Markdown Reports**: Clean weekly reports saved to `reports/`
- **Top Comments**: Includes top comments for additional context

## Monitored Subreddits

- r/ChatGPT - AI discussions and monetization
- r/SideProject - Product launches
- r/PassiveIncome - Info products and revenue
- r/EntrepreneurRideAlong - Case studies
- r/juststart - Content creators building businesses
- r/nocode - AI tool builders
- r/microsaas - Small digital products

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Listener

```bash
# Full scan with comments (thorough)
python main.py

# Skip comments (faster)
python main.py --no-comments

# Quick mode (fastest - fewer pages, no comments)
python main.py --quick
```

### 3. View Your Report

Reports are saved to `reports/reddit_report_YYYY-MM-DD.md`

## Keywords Tracked

**AI Related:**
- AI, ChatGPT, Claude, GPT, artificial intelligence, LLM

**Digital Products:**
- digital product, info product, course, ebook, template, guide

**Software/Tools:**
- SaaS, software, tool, automation, workflow

**Business/Money:**
- passive income, side hustle, make money, monetize, revenue, MRR, sales

**Platforms:**
- Gumroad, Notion templates, Canva templates

## How Categorization Works

The agent uses pattern matching to categorize posts:

| Category | Trigger Patterns | Use Case |
|----------|-----------------|----------|
| **Questions** | "how do I", "what's the best", "anyone know", ends with ? | Content ideas for blog posts, videos, courses |
| **Pain Points** | "struggling with", "can't figure out", "frustrated", "doesn't work" | Product opportunities, problems to solve |
| **Success Stories** | "made $X", "launched", "revenue", "MRR", "first sale" | Competitive intelligence, market trends |

## Configuration

Edit `config.py` to customize:

```python
SUBREDDITS = [...]      # Which subreddits to monitor
KEYWORDS = [...]        # Keywords to track
LOOKBACK_DAYS = 7       # How far back to search
MIN_SCORE = 1           # Minimum post score
REQUEST_DELAY = 2.0     # Delay between requests (be nice to Reddit)
```

## Project Structure

```
.
├── main.py              # Entry point - run this
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── listener/
│   ├── __init__.py
│   ├── reddit_monitor.py    # Web scraper
│   ├── categorizer.py       # Post categorization
│   └── report_generator.py  # Markdown reports
└── reports/             # Generated reports
```

## Example Output

The report includes sections like:

```markdown
## Questions People Are Asking (Content Ideas)

### 1. How do I validate my SaaS idea before building?

**Subreddit:** r/SideProject | **Score:** 127 | **Comments:** 45
**Keywords:** SaaS, validate
**Link:** https://reddit.com/...

> Looking to build a micro-SaaS but don't want to waste months
> building something nobody wants...

**Top Comments:**
- (89 pts) The best validation is getting someone to pay...
- (45 pts) I always start with a landing page and...
```

## Rate Limiting

The scraper includes a 2-second delay between requests to be respectful to Reddit's servers. You can adjust this in `config.py`:

```python
REQUEST_DELAY = 2.0  # Seconds between requests
```

## Future Enhancements

- [ ] Twitter/X monitoring
- [ ] YouTube comment scanning
- [ ] Email digest option
- [ ] Slack/Discord notifications
- [ ] Trend detection over time
- [ ] Sentiment analysis
