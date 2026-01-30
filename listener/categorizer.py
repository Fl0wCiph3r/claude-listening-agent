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

    # Question indicators
    QUESTION_PATTERNS = [
        r"\?",  # Contains question mark
        r"^(how|what|why|when|where|which|who|can|could|should|would|is|are|does|do|has|have)\b",
        r"\b(anyone|anybody|someone|somebody)\b.*\b(know|tried|used|recommend)",
        r"\b(looking for|searching for|need help|need advice)\b",
        r"\b(advice|suggestions?|recommendations?|tips?)\b.*\b(on|for|about)\b",
        r"\b(eli5|explain|help me understand)\b",
        r"\bquestion\b",
    ]

    # Pain point / struggle indicators
    PAIN_PATTERNS = [
        r"\b(struggling|frustrated|annoyed|difficult|hard|impossible|can't|cannot)\b",
        r"\b(problem|issue|bug|error|broken|doesn't work|not working)\b",
        r"\b(hate|sucks|terrible|awful|worst|disappointed)\b",
        r"\b(waste of time|waste of money|scam|overpriced)\b",
        r"\b(failed|failing|failure|gave up|giving up)\b",
        r"\b(stuck|confused|lost|overwhelmed)\b",
        r"\b(wish there was|if only|why isn't there)\b",
        r"\b(pain point|bottleneck|blocker)\b",
        r"\b(rant|vent|complaint)\b",
    ]

    # Success story indicators
    SUCCESS_PATTERNS = [
        r"\b(made|earned|generated|hit|reached)\b.*\$\d+",
        r"\b(success|successful|succeeded|working|works great)\b",
        r"\b(finally|achieved|accomplished|milestone)\b",
        r"\b(case study|results|roi|revenue)\b",
        r"\b(grew|growth|increase|doubled|tripled)\b.*\b(revenue|income|sales|users|customers)\b",
        r"\b(launched|shipped|released)\b.*\b(product|app|saas|course|ebook)\b",
        r"\b(quit my job|full[- ]time|went viral)\b",
        r"\b(testimonial|review|feedback)\b.*\b(positive|great|amazing)\b",
        r"\b(strategy|approach|method)\b.*\b(that works|working)\b",
        r"\b(here's how|this is how|what worked)\b",
        r"\b(breakdown|behind the scenes|how i)\b",
        r"\bMRR\b",
        r"\bARR\b",
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
        score = min(1.0, len(matches) * 0.3)
        return score, matches

    def categorize(self, post: RedditPost) -> CategorizedPost:
        """Categorize a single post."""
        text = post.full_text

        # Score each category
        question_score, question_signals = self._score_patterns(
            text, self.question_patterns
        )
        pain_score, pain_signals = self._score_patterns(text, self.pain_patterns)
        success_score, success_signals = self._score_patterns(
            text, self.success_patterns
        )

        # Boost question score if title ends with ?
        if post.title.strip().endswith("?"):
            question_score = min(1.0, question_score + 0.3)
            if "?" not in question_signals:
                question_signals.append("title ends with ?")

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
        if best_score < 0.2:
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
