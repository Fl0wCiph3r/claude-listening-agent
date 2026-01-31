"""Generate complete markdown reports from all platforms."""

from datetime import datetime, timezone
from pathlib import Path

import config
from .models import Finding, Platform, Category, CompleteReport, ScanResult


class CompleteReportGenerator:
    """Generate comprehensive markdown reports from all platforms."""

    def __init__(self, output_dir: str | None = None):
        """Initialize report generator."""
        self.output_dir = Path(output_dir or config.REPORT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_finding(self, finding: Finding, index: int) -> str:
        """Format a single finding for the report."""
        lines = []

        # Header
        icon = finding.platform_icon
        lines.append(f"### {index}. {icon} {finding.title[:100]}")
        lines.append("")

        # Metadata based on platform
        if finding.platform == Platform.TWITTER:
            lines.append(f"**Author:** @{finding.author} | **Likes:** {finding.score} | **Retweets:** {finding.shares_count}")
        elif finding.platform == Platform.YOUTUBE:
            lines.append(f"**Video:** {finding.source_name[:60]}... | **Likes:** {finding.score}")
            lines.append(f"**Author:** {finding.author}")
        else:  # Reddit
            lines.append(f"**Subreddit:** r/{finding.source_name} | **Score:** {finding.score} | **Comments:** {finding.comments_count}")
            lines.append(f"**Author:** u/{finding.author}")

        lines.append(f"**Posted:** {finding.created_at.strftime('%Y-%m-%d %H:%M UTC')}")

        if finding.url:
            lines.append(f"**Link:** [{finding.url}]({finding.url})")
        lines.append("")

        # Body
        body = finding.body
        if len(body) > 400:
            body = body[:400] + "..."
        if body.strip():
            lines.append("> " + body.replace("\n", "\n> "))
            lines.append("")

        # Signals
        if finding.category_signals:
            lines.append(f"*Signals: {', '.join(finding.category_signals[:3])}*")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_platform_section(
        self,
        platform_name: str,
        platform_focus: str,
        result: ScanResult | None,
        max_per_category: int = 15,
    ) -> str:
        """Generate a section for a single platform."""
        lines = [
            f"## {platform_name} ({platform_focus})",
            "",
        ]

        if not result or not result.findings:
            if result and result.errors:
                lines.append(f"*Skipped due to errors: {result.errors[0]}*")
            else:
                lines.append("*No findings from this platform.*")
            lines.append("")
            return "\n".join(lines)

        # Stats
        lines.append(f"**Total findings:** {len(result.findings)} | ")
        lines.append(f"Questions: {len(result.questions)} | ")
        lines.append(f"Pain Points: {len(result.pain_points)} | ")
        lines.append(f"Success Stories: {len(result.success_stories)}")
        lines.append("")

        # Questions
        if result.questions:
            lines.append("### Questions (Content Ideas)")
            lines.append("")
            for i, finding in enumerate(result.questions[:max_per_category], 1):
                lines.append(self._format_finding(finding, i))

        # Pain Points
        if result.pain_points:
            lines.append("### Pain Points (Product Opportunities)")
            lines.append("")
            for i, finding in enumerate(result.pain_points[:max_per_category], 1):
                lines.append(self._format_finding(finding, i))

        # Success Stories
        if result.success_stories:
            lines.append("### Success Stories (Competitive Intel)")
            lines.append("")
            for i, finding in enumerate(result.success_stories[:max_per_category], 1):
                lines.append(self._format_finding(finding, i))

        return "\n".join(lines)

    def _generate_top_insights(self, report: CompleteReport) -> str:
        """Generate top insights section."""
        lines = [
            "## Top Insights",
            "",
        ]

        # Top content ideas (questions)
        questions = sorted(
            report.questions,
            key=lambda f: f.engagement_score,
            reverse=True
        )[:5]

        if questions:
            lines.append("### Top 5 Content Ideas (from Questions)")
            lines.append("")
            for i, q in enumerate(questions, 1):
                lines.append(f"{i}. {q.platform_icon} **{q.title[:80]}**")
                lines.append(f"   - Source: {q.source_name} | Engagement: {q.engagement_score}")
                lines.append(f"   - [View]({q.url})")
                lines.append("")

        # Top product opportunities (pain points)
        pain_points = sorted(
            report.pain_points,
            key=lambda f: f.engagement_score,
            reverse=True
        )[:5]

        if pain_points:
            lines.append("### Top 5 Product Opportunities (from Pain Points)")
            lines.append("")
            for i, p in enumerate(pain_points, 1):
                lines.append(f"{i}. {p.platform_icon} **{p.title[:80]}**")
                lines.append(f"   - Source: {p.source_name} | Engagement: {p.engagement_score}")
                lines.append(f"   - [View]({p.url})")
                lines.append("")

        # Top competitor strategies (success stories)
        successes = sorted(
            report.success_stories,
            key=lambda f: f.engagement_score,
            reverse=True
        )[:5]

        if successes:
            lines.append("### Top 5 Competitor Strategies (from Success Stories)")
            lines.append("")
            for i, s in enumerate(successes, 1):
                lines.append(f"{i}. {s.platform_icon} **{s.title[:80]}**")
                lines.append(f"   - Source: {s.source_name} | Engagement: {s.engagement_score}")
                lines.append(f"   - [View]({s.url})")
                lines.append("")

        return "\n".join(lines)

    def generate(self, report: CompleteReport, save: bool = True) -> str:
        """Generate the complete markdown report."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        # Count by platform
        twitter_count = len(report.twitter.findings) if report.twitter else 0
        reddit_count = len(report.reddit.findings) if report.reddit else 0
        youtube_count = len(report.youtube.findings) if report.youtube else 0

        lines = [
            "# Complete Intelligence Report",
            "",
            f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Period:** Last 7-30 days (varies by platform)",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| **Total Findings** | **{report.total_count}** |",
            f"| Questions (Content Ideas) | {len(report.questions)} |",
            f"| Pain Points (Product Opps) | {len(report.pain_points)} |",
            f"| Success Stories (Comp Intel) | {len(report.success_stories)} |",
            "",
            "**By Platform:**",
            f"| Platform | Findings |",
            f"|----------|----------|",
            f"| 🐦 Twitter/X | {twitter_count} |",
            f"| 🔴 Reddit | {reddit_count} |",
            f"| 📺 YouTube | {youtube_count} |",
            "",
            "---",
            "",
        ]

        # Top Insights (most valuable section)
        lines.append(self._generate_top_insights(report))
        lines.append("")
        lines.append("---")
        lines.append("")

        # Platform sections
        lines.append(
            self._generate_platform_section(
                "🐦 Twitter/X Findings",
                "Info Product Focus",
                report.twitter,
            )
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append(
            self._generate_platform_section(
                "🔴 Reddit Findings",
                "Tech/SaaS Focus",
                report.reddit,
            )
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append(
            self._generate_platform_section(
                "📺 YouTube Comments",
                "Audience Questions",
                report.youtube,
            )
        )

        report_content = "\n".join(lines)

        if save:
            filename = f"complete_report_{date_str}.md"
            filepath = self.output_dir / filename
            filepath.write_text(report_content, encoding='utf-8')
            print(f"\nReport saved to: {filepath}")

        return report_content

    def list_reports(self) -> list[Path]:
        """List all generated reports."""
        return sorted(self.output_dir.glob("complete_report_*.md"), reverse=True)
