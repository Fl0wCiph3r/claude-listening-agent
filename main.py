#!/usr/bin/env python3
"""
Reddit Listener Agent - Monitor online discussions about AI and digital products.

This version uses web scraping (no Reddit API required).

Usage:
    python main.py              # Run full scan and generate report
    python main.py --no-comments # Skip comment scraping (faster)
    python main.py --quick      # Quick mode: fewer pages, no comments
"""

import argparse
import sys

from listener import RedditMonitor, Categorizer, ReportGenerator
from listener.categorizer import Category


def run_scan(include_comments: bool = True, quick: bool = False):
    """Run the full scan and generate report."""
    print("=" * 60)
    print("  Reddit Listener Agent (Web Scraping)")
    print("=" * 60)
    print()

    if quick:
        print("Quick mode enabled (fewer pages, no comments)")
        print()
        include_comments = False

    # Initialize components
    scraper = RedditMonitor()
    categorizer = Categorizer()
    reporter = ReportGenerator()

    # Fetch posts
    posts = scraper.fetch_all(include_comments=include_comments)
    print()
    print(f"Total relevant posts found: {len(posts)}")
    print()

    if not posts:
        print("No matching posts found. The subreddits may be slow or")
        print("try adjusting keywords in config.py")
        return

    # Categorize
    print("Categorizing posts...")
    categorized = categorizer.categorize_all(posts)

    # Print summary
    print()
    print("=" * 40)
    print("RESULTS SUMMARY")
    print("=" * 40)
    print(f"  Questions (Content Ideas):      {len(categorized[Category.QUESTION])}")
    print(f"  Pain Points (Product Opps):     {len(categorized[Category.PAIN_POINT])}")
    print(f"  Success Stories (Comp Intel):   {len(categorized[Category.SUCCESS_STORY])}")
    print(f"  Uncategorized:                  {len(categorized[Category.UNCATEGORIZED])}")
    print("=" * 40)
    print()

    # Generate report
    print("Generating markdown report...")
    reporter.generate(categorized)

    print()
    print("Done! Open the report to review your findings.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Reddit for AI and digital product discussions (no API required)"
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Skip scraping comments (faster but less context)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: fewer pages per subreddit, no comments",
    )

    args = parser.parse_args()

    # Run the scan
    try:
        run_scan(
            include_comments=not args.no_comments,
            quick=args.quick,
        )
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during scan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
