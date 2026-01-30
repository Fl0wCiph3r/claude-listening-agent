# Reddit Listener Agent

Monitor online discussions about AI products, digital products, and making money with AI. Automatically categorizes findings into actionable buckets for content creation and product development.

## Features

- **Reddit Monitoring**: Scans multiple subreddits for relevant discussions
- **Keyword Tracking**: Finds posts mentioning AI, digital products, courses, SaaS, etc.
- **Smart Categorization**: Automatically sorts findings into:
  - Questions (content ideas)
  - Pain points (product opportunities)
  - Success stories (competitive intelligence)
- **Markdown Reports**: Clean weekly reports you can review and act on

## Monitored Subreddits

- r/Entrepreneur
- r/EntrepreneurRideAlong
- r/SideProject
- r/ChatGPT
- r/PassiveIncome
- r/DigitalMarketing
- r/SaaS

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Select "script" as the app type
4. Use `http://localhost:8080` as the redirect URI
5. Copy the client ID (under the app name) and secret

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Or export directly:

```bash
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
```

## Usage

### Run Full Scan

```bash
python main.py
```

### Skip Comments (Faster)

```bash
python main.py --no-comments
```

### Test API Connection

```bash
python main.py --dry-run
```

## Reports

Reports are saved to the `reports/` directory with the filename format:
```
reddit_report_YYYY-MM-DD.md
```

## Configuration

Edit `config.py` to customize:

- `SUBREDDITS`: List of subreddits to monitor
- `KEYWORDS`: Keywords to track
- `LOOKBACK_DAYS`: How far back to search (default: 7 days)
- `MIN_SCORE`: Minimum post score threshold
- `MAX_POSTS_PER_SUBREDDIT`: Posts to fetch per subreddit

## Project Structure

```
.
├── main.py              # Entry point and CLI
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── listener/
│   ├── __init__.py
│   ├── reddit_monitor.py    # Reddit API integration
│   ├── categorizer.py       # Post categorization logic
│   └── report_generator.py  # Markdown report generation
└── reports/             # Generated reports
```

## Future Enhancements

- [ ] Twitter/X monitoring
- [ ] YouTube comment scanning
- [ ] Email digest option
- [ ] Slack/Discord notifications
- [ ] Sentiment analysis
- [ ] Trend detection over time
