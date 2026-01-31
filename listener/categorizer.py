"""Categorize Reddit posts into actionable buckets."""

import re
from dataclasses import dataclass, field
from enum import Enum

from .reddit_monitor import RedditPost


class Category(Enum):
    """Content categories for analysis."""

    QUESTION = "question"  # Content ideas
    PAIN_POINT = "pain_point"  # Product opportunities
    SUCCESS_STORY = "success"  # Competitive intelligence
    UNCATEGORIZED = "uncategorized"


@dataclass
class CategorizedPost:
    """A post with its assigned category and reasoning."""

    post: RedditPost
    category: Category
    confidence: float  # 0-1 score
    signals: list = field(default_factory=list)  # Why this category


class Categorizer:
    """Categorize posts into questions, pain points, and success stories."""

    # Question indicators - "how do I", "what's the best", "anyone know"
    QUESTION_PATTERNS = [
        r"\?$",  # Ends with question mark
        r"\?[\"'\s]*$",  # Ends with question mark (with quotes)
        r"^(how|what|why|when|where|which|who|can|could|should|would|is|are|does|do|has|have)\s",
        r"\b(how do i|how can i|how to|what is the best|what's the best|whats the best)\b",
        r"\b(anyone|anybody|someone|somebody)\s+(know|tried|used|recommend|have|had)\b",
        r"\b(looking for|searching for|need help|need advice|seeking)\b",
        r"\b(advice|suggestions?|recommendations?|tips?|thoughts?)\s+(on|for|about|regarding)\b",
        r"\b(eli5|explain|help me understand|confused about)\b",
        r"\b(is it worth|worth it to|should i)\b",
        r"\b(best way to|easiest way to|fastest way to)\b",
        r"\bquestion\b",
        r"\b(any experience with|experience using|tried using)\b",
    ]

    # Pain point / struggle indicators - "struggling with", "can't figure out", "frustrated"
    PAIN_PATTERNS = [
        r"\b(struggling|frustrated|annoyed|irritated|difficult|hard|impossible|can't|cannot|couldn't)\b",
        r"\b(problem|issue|bug|error|broken|doesn't work|not working|stopped working)\b",
        r"\b(hate|sucks|terrible|awful|worst|disappointed|disappointing)\b",
        r"\b(waste of time|waste of money|scam|overpriced|rip.?off)\b",
        r"\b(failed|failing|failure|gave up|giving up|quit|quitting)\b",
        r"\b(stuck|confused|lost|overwhelmed|burned out|burnout)\b",
        r"\b(wish there was|if only|why isn't there|why can't)\b",
        r"\b(pain point|bottleneck|blocker|roadblock)\b",
        r"\b(rant|vent|complaint|complaining)\b",
        r"\b(no luck|bad luck|unlucky)\b",
        r"\b(help!|please help|desperate|at my wits end)\b",
        r"\b(nightmare|disaster|mess|chaos)\b",
        r"\b(can't figure out|don't understand|makes no sense)\b",
    ]

    # Success story indicators - "made $X", "launched", "revenue", "MRR"
    SUCCESS_PATTERNS = [
        r"\b(made|earned|generated|hit|reached|crossed)\b.*\$[\d,]+",
        r"\$[\d,]+[kK]?\s*(MRR|ARR|revenue|sales|profit)",
        r"\b(success|successful|succeeded|working|works great|loving it)\b",
        r"\b(finally|achieved|accomplished|milestone|breakthrough)\b",
        r"\b(case study|results|roi|revenue breakdown)\b",
        r"\b(grew|growth|increase|doubled|tripled|10x)\b.*\b(revenue|income|sales|users|customers|subscribers)\b",
        r"\b(launched|shipped|released|went live)\b.*\b(product|app|saas|course|ebook|template)\b",
        r"\b(quit my job|full[- ]time|went viral|blew up)\b",
        r"\b(testimonial|review|feedback)\b.*\b(positive|great|amazing|awesome)\b",
        r"\b(strategy|approach|method|system)\b.*\b(that works|working|paid off)\b",
        r"\b(here's how|this is how|what worked|my results)\b",
        r"\b(breakdown|behind the scenes|how i built|how i made)\b",
        r"\bMRR\b",
        r"\bARR\b",
        r"\b(first sale|first customer|first paying|100 users|1000 users|10k users)\b",
        r"\b(profitable|profit margin|net profit)\b",
        r"\b(sold|selling|sales of)\s+\d+",
    ]

    def __init__(self):
        """Compile regex patterns."""
        self.question_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.QUESTION_PATTERNS
        ]
        self.pain_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PAIN_PATTERNS
        ]
        self.success_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.SUCCESS_PATTERNS
        ]

    def _score_patterns(
        self, text: str, patterns: list[re.Pattern]
    ) -> tuple[float, list[str]]:
        """Score text against patterns, return score and matched signals."""
        matches = []
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                matches.append(match.group())

        if not matches:
            return 0.0, []

        # Score based on number of matches (diminishing returns)
        score = min(1.0, len(matches) * 0.25)
        return score, matches

    def categorize(self, post: RedditPost) -> CategorizedPost:
        """Categorize a single post."""
        text = post.full_text

        # Also consider top comments in categorization
        comments_text = " ".join(c.get("body", "") for c in post.top_comments)
        full_analysis_text = f"{text} {comments_text}"

        # Score each category
        question_score, question_signals = self._score_patterns(
            text, self.question_patterns
        )
        pain_score, pain_signals = self._score_patterns(
            full_analysis_text, self.pain_patterns
        )
        success_score, success_signals = self._score_patterns(
            full_analysis_text, self.success_patterns
        )

        # Boost question score if title ends with ?
        if post.title.strip().endswith("?"):
            question_score = min(1.0, question_score + 0.4)
            if "?" not in question_signals:
                question_signals.insert(0, "title ends with ?")

        # Boost success score for money mentions
        money_pattern = re.compile(r"\$[\d,]+[kK]?")
        if money_pattern.search(text):
            success_score = min(1.0, success_score + 0.2)

        # Determine winner
        scores = [
            (Category.QUESTION, question_score, question_signals),
            (Category.PAIN_POINT, pain_score, pain_signals),
            (Category.SUCCESS_STORY, success_score, success_signals),
        ]

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        best_category, best_score, best_signals = scores[0]

        # Minimum threshold
        if best_score < 0.15:
            return CategorizedPost(
                post=post,
                category=Category.UNCATEGORIZED,
                confidence=0.0,
                signals=[],
            )

        return CategorizedPost(
            post=post,
            category=best_category,
            confidence=best_score,
            signals=best_signals[:5],  # Top 5 signals
        )

    def categorize_all(
        self, posts: list[RedditPost]
    ) -> dict[Category, list[CategorizedPost]]:
        """Categorize all posts and group by category."""
        results = {
            Category.QUESTION: [],
            Category.PAIN_POINT: [],
            Category.SUCCESS_STORY: [],
            Category.UNCATEGORIZED: [],
        }

        for post in posts:
            categorized = self.categorize(post)
            results[categorized.category].append(categorized)

        # Sort each category by confidence then score
        for category in results:
            results[category].sort(
                key=lambda x: (x.confidence, x.post.score), reverse=True
            )

        return results
