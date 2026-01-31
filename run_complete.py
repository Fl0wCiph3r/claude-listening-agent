#!/usr/bin/env python3
"""
Complete Listener Agent - Monitor Reddit, Twitter, and YouTube.

Scans all platforms for discussions about AI products, digital products,
and making money online. Generates a comprehensive intelligence report.

Usage:
    python run_complete.py              # Full scan (all platforms)
    python run_complete.py --quick      # Quick mode (less thorough)
    python run_complete.py --reddit     # Reddit only
    python run_complete.py --twitter    # Twitter only
    python run_complete.py --youtube    # YouTube only
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone

import config
from listener.models import Platform, Category, Finding, ScanResult, CompleteReport
from listener.reddit_monitor import RedditScraper
from listener.twitter_monitor import TwitterMonitor
from listener.youtube_monitor import YouTubeMonitor
from listener.categorizer import Categorizer
from listener.complete_report import CompleteReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def convert_reddit_to_findings(reddit_posts, categorizer: Categorizer) -> list[Finding]:
    """Convert Reddit posts to unified Finding objects."""
    findings = []

    for post in reddit_posts:
        finding = Finding(
            id=post.id,
            platform=Platform.REDDIT,
            title=post.title,
            body=post.body,
            author=post.author,
            url=post.url,
            created_at=post.created_utc,
            score=post.score,
            comments_count=post.num_comments,
            source_name=post.subreddit,
            matched_keywords=post.matched_keywords,
            replies=post.top_comments,
        )
        findings.append(finding)

    # Categorize all findings
    categorizer.categorize_findings(findings)

    return findings


def scan_reddit(categorizer: Categorizer, include_comments: bool = True) -> ScanResult:
    """Scan Reddit and return results."""
    print("\n" + "=" * 60)
    print("  🔴 REDDIT SCAN")
    print("=" * 60)

    start_time = time.time()
    errors = []

    try:
        scraper = RedditScraper()
        posts = scraper.fetch_all(include_comments=include_comments)

        # Convert to unified findings
        findings = convert_reddit_to_findings(posts, categorizer)

        return ScanResult(
            platform=Platform.REDDIT,
            findings=findings,
            errors=errors,
            scan_time_seconds=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"Reddit scan error: {e}")
        return ScanResult(
            platform=Platform.REDDIT,
            findings=[],
            errors=[str(e)],
            scan_time_seconds=time.time() - start_time,
        )


def scan_twitter(categorizer: Categorizer) -> ScanResult:
    """Scan Twitter via Nitter and return results."""
    print("\n" + "=" * 60)
    print("  🐦 TWITTER/X SCAN (via Nitter)")
    print("=" * 60)
    print("  Note: Using Nitter instances - no login required")

    start_time = time.time()

    try:
        monitor = TwitterMonitor()
        result = monitor.fetch_all()

        # Categorize findings
        categorizer.categorize_findings(result.findings)

        return result

    except Exception as e:
        logger.error(f"Twitter scan error: {e}")
        return ScanResult(
            platform=Platform.TWITTER,
            findings=[],
            errors=[str(e)],
            scan_time_seconds=time.time() - start_time,
        )


def scan_youtube(categorizer: Categorizer) -> ScanResult:
    """Scan YouTube and return results."""
    print("\n" + "=" * 60)
    print("  📺 YOUTUBE SCAN")
    print("=" * 60)

    if not config.YOUTUBE_API_KEY:
        print("  Note: No YOUTUBE_API_KEY set - using limited scraping")
        print("  For better results, set: export YOUTUBE_API_KEY=your_key")

    start_time = time.time()

    try:
        monitor = YouTubeMonitor()
        result = monitor.fetch_all()

        # Categorize findings
        categorizer.categorize_findings(result.findings)

        return result

    except Exception as e:
        logger.error(f"YouTube scan error: {e}")
        return ScanResult(
            platform=Platform.YOUTUBE,
            findings=[],
            errors=[str(e)],
            scan_time_seconds=time.time() - start_time,
        )


def run_complete_scan(
    include_reddit: bool = True,
    include_twitter: bool = True,
    include_youtube: bool = True,
    quick_mode: bool = False,
):
    """Run the complete scan across all platforms."""
    print("\n" + "=" * 70)
    print("  COMPLETE LISTENER AGENT - Intelligence Gathering Tool")
    print("=" * 70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {'Quick' if quick_mode else 'Full'}")
    print()

    platforms = []
    if include_reddit:
        platforms.append("Reddit")
    if include_twitter:
        platforms.append("Twitter")
    if include_youtube:
        platforms.append("YouTube")

    print(f"  Platforms: {', '.join(platforms)}")
    print("=" * 70)

    overall_start = time.time()
    categorizer = Categorizer()

    # Initialize results
    reddit_result = None
    twitter_result = None
    youtube_result = None

    # Scan each platform
    if include_twitter:
        twitter_result = scan_twitter(categorizer)
        print(f"\n  Twitter: {len(twitter_result.findings)} findings")

    if include_reddit:
        reddit_result = scan_reddit(categorizer, include_comments=not quick_mode)
        print(f"\n  Reddit: {len(reddit_result.findings)} findings")

    if include_youtube:
        youtube_result = scan_youtube(categorizer)
        print(f"\n  YouTube: {len(youtube_result.findings)} findings")

    # Create complete report
    report = CompleteReport(
        reddit=reddit_result,
        twitter=twitter_result,
        youtube=youtube_result,
        generated_at=datetime.now(timezone.utc),
    )

    # Generate report
    print("\n" + "=" * 60)
    print("  📊 GENERATING REPORT")
    print("=" * 60)

    reporter = CompleteReportGenerator()
    reporter.generate(report)

    # Summary
    total_time = time.time() - overall_start
    print("\n" + "=" * 70)
    print("  SCAN COMPLETE")
    print("=" * 70)
    print(f"  Total findings: {report.total_count}")
    print(f"    - Questions (Content Ideas): {len(report.questions)}")
    print(f"    - Pain Points (Product Opps): {len(report.pain_points)}")
    print(f"    - Success Stories (Comp Intel): {len(report.success_stories)}")
    print()
    print(f"  Time elapsed: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print("=" * 70)
    print()
    print("  Open the report in reports/ to review your findings!")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Complete Listener Agent - Monitor Reddit, Twitter, and YouTube"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (faster, less thorough)",
    )
    parser.add_argument(
        "--reddit",
        action="store_true",
        help="Scan Reddit only",
    )
    parser.add_argument(
        "--twitter",
        action="store_true",
        help="Scan Twitter only",
    )
    parser.add_argument(
        "--youtube",
        action="store_true",
        help="Scan YouTube only",
    )

    args = parser.parse_args()

    # Determine which platforms to scan
    if args.reddit or args.twitter or args.youtube:
        # Specific platforms selected
        include_reddit = args.reddit
        include_twitter = args.twitter
        include_youtube = args.youtube
    else:
        # Default: all platforms
        include_reddit = True
        include_twitter = True
        include_youtube = True

    try:
        run_complete_scan(
            include_reddit=include_reddit,
            include_twitter=include_twitter,
            include_youtube=include_youtube,
            quick_mode=args.quick,
        )
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
