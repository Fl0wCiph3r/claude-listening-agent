"""Generate markdown reports from categorized Reddit data."""

import os
from datetime import datetime, timezone
from pathlib import Path

import config
from .categorizer import Category, CategorizedPost


class ReportGenerator:
    """Generate markdown reports from categorized posts."""

    def __init__(self, output_dir: str | None = None):
        """Initialize report generator."""
        self.output_dir = Path(output_dir or config.REPORT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_post(self, cat_post: CategorizedPost, index: int) -> str:
        """Format a single post for the report."""
        post = cat_post.post
        lines = []

        # Header with index and score
        if post.is_comment:
            lines.append(f"### {index}. Comment on: {post.parent_title[:80]}...")
        else:
            lines.append(f"### {index}. {post.title}")

        lines.append("")

        # Metadata
        lines.append(f"**Subreddit:** r/{post.subreddit} | **Score:** {post.score} | **Author:** u/{post.author}")
        lines.append(f"**Posted:** {post.created_utc.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Keywords:** {', '.join(post.matched_keywords)}")
        lines.append(f"**Link:** [{post.url}]({post.url})")
        lines.append("")

        # Body preview (truncated)
        body = post.body if post.is_comment else post.body or "(No body text)"
        if len(body) > 500:
            body = body[:500] + "..."
        if body.strip():
            lines.append("> " + body.replace("\n", "\n> "))
            lines.append("")

        # Categorization signals
        if cat_post.signals:
            lines.append(f"*Signals: {', '.join(cat_post.signals[:3])}*")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_section(
        self,
        title: str,
        description: str,
        posts: list[CategorizedPost],
        max_items: int = 25,
    ) -> str:
        """Generate a report section."""
        lines = [
            f"## {title}",
            "",
            f"*{description}*",
            "",
            f"**Total found: {len(posts)}** (showing top {min(len(posts), max_items)})",
            "",
        ]

        if not posts:
            lines.append("*No items found in this category.*")
            lines.append("")
        else:
            for i, post in enumerate(posts[:max_items], 1):
                lines.append(self._format_post(post, i))

        return "\n".join(lines)

    def generate(
        self,
        categorized: dict[Category, list[CategorizedPost]],
        save: bool = True,
    ) -> str:
        """Generate the full markdown report."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        lines = [
            "# Reddit Listener Report",
            "",
            f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Period:** Last {config.LOOKBACK_DAYS} days",
            f"**Subreddits:** {', '.join(['r/' + s for s in config.SUBREDDITS])}",
            "",
            "---",
            "",
            "## Summary",
            "",
        ]

        # Summary stats
        total = sum(len(posts) for posts in categorized.values())
        lines.append(f"| Category | Count |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Questions (Content Ideas) | {len(categorized[Category.QUESTION])} |")
        lines.append(f"| Pain Points (Product Opportunities) | {len(categorized[Category.PAIN_POINT])} |")
        lines.append(f"| Success Stories (Competitive Intel) | {len(categorized[Category.SUCCESS_STORY])} |")
        lines.append(f"| Uncategorized | {len(categorized[Category.UNCATEGORIZED])} |")
        lines.append(f"| **Total** | **{total}** |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Questions section
        lines.append(
            self._generate_section(
                "Questions People Are Asking (Content Ideas)",
                "These questions reveal what your audience wants to learn. Great for blog posts, videos, courses, and info products.",
                categorized[Category.QUESTION],
            )
        )

        # Pain points section
        lines.append(
            self._generate_section(
                "Pain Points & Struggles (Product Opportunities)",
                "These frustrations and problems are potential product opportunities. Build something that solves these.",
                categorized[Category.PAIN_POINT],
            )
        )

        # Success stories section
        lines.append(
            self._generate_section(
                "Success Stories & What's Working (Competitive Intelligence)",
                "Learn from what's working for others. Identify trends, strategies, and potential competitors.",
                categorized[Category.SUCCESS_STORY],
            )
        )

        report = "\n".join(lines)

        if save:
            filename = f"reddit_report_{date_str}.md"
            filepath = self.output_dir / filename
            filepath.write_text(report)
            print(f"\nReport saved to: {filepath}")

        return report

    def list_reports(self) -> list[Path]:
        """List all generated reports."""
        return sorted(self.output_dir.glob("reddit_report_*.md"), reverse=True)
