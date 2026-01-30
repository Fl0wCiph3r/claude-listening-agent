#!/usr/bin/env python3
"""
Reddit Listener Agent - Monitor online discussions about AI and digital products.

Usage:
    python main.py              # Run full scan and generate report
    python main.py --no-comments # Skip comment scanning (faster)
    python main.py --dry-run    # Test connection without full scan
"""

import argparse
import sys
import os

from listener import RedditMonitor, Categorizer, ReportGenerator
from listener.categorizer import Category


def check_credentials():
    """Verify Reddit API credentials are set."""
    required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    missing = [var for var in required if not os.environ.get(var)]

    if missing:
        print("Error: Missing Reddit API credentials!")
        print()
        print("Please set the following environment variables:")
        for var in missing:
            print(f"  export {var}=your_value")
        print()
        print("To get Reddit API credentials:")
        print("  1. Go to https://www.reddit.com/prefs/apps")
        print("  2. Click 'create another app...'")
        print("  3. Select 'script' as the app type")
        print("  4. Use http://localhost:8080 as the redirect URI")
        print("  5. Copy the client ID (under the app name) and secret")
        print()
        print("Or copy .env.example to .env and fill in your values:")
        print("  cp .env.example .env")
        print("  # Edit .env with your credentials")
        print("  source .env")
        return False

    return True


def dry_run():
    """Test Reddit API connection."""
    print("Testing Reddit API connection...")
    try:
        monitor = RedditMonitor()
        # Try to access Reddit
        subreddit = monitor.reddit.subreddit("test")
        _ = subreddit.display_name
        print("Success! Reddit API connection is working.")
        return True
    except Exception as e:
        print(f"Error connecting to Reddit: {e}")
        return False


def run_scan(include_comments: bool = True):
    """Run the full scan and generate report."""
    print("=" * 60)
    print("Reddit Listener Agent")
    print("=" * 60)
    print()

    # Initialize components
    monitor = RedditMonitor()
    categorizer = Categorizer()
    reporter = ReportGenerator()

    # Fetch posts
    print("Fetching posts from Reddit...")
    print()
    posts = monitor.fetch_all(include_comments=include_comments)
    print()
    print(f"Total relevant items found: {len(posts)}")
    print()

    if not posts:
        print("No matching posts found. Try adjusting keywords or time range.")
        return

    # Categorize
    print("Categorizing posts...")
    categorized = categorizer.categorize_all(posts)

    # Print summary
    print()
    print("Results:")
    print(f"  - Questions (Content Ideas): {len(categorized[Category.QUESTION])}")
    print(f"  - Pain Points (Product Opportunities): {len(categorized[Category.PAIN_POINT])}")
    print(f"  - Success Stories (Competitive Intel): {len(categorized[Category.SUCCESS_STORY])}")
    print()

    # Generate report
    print("Generating report...")
    reporter.generate(categorized)

    print()
    print("Done! Open the report to review your findings.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Reddit for AI and digital product discussions"
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Skip scanning comments (faster but less comprehensive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test Reddit API connection without running full scan",
    )

    args = parser.parse_args()

    # Check credentials
    if not check_credentials():
        sys.exit(1)

    if args.dry_run:
        success = dry_run()
        sys.exit(0 if success else 1)

    # Run the scan
    try:
        run_scan(include_comments=not args.no_comments)
    except KeyboardInterrupt:
        print("\nScan interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during scan: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
