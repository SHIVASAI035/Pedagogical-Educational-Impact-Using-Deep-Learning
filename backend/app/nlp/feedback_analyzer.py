"""Lexicon-based sentiment and aspect analysis for student feedback.

Approach and limitations
------------------------
This module uses an explainable lexicon + negation/intensifier rules rather
than a large pre-trained transformer. That choice is deliberate for a BTech
project that must run offline on a laptop:

* every label can be traced to the words that produced it;
* no student text leaves the machine;
* no GPU or multi-hundred-MB download is required.

Known limitations (also reported in ``docs/PROJECT_REPORT.md``):

* sarcasm and implicit criticism ("great, another worksheet") are missed;
* domain slang and Hinglish are only partially covered;
* the lexicon is small, so neutral text with no sentiment words falls back to
  the numeric ratings;
* aspect detection is keyword-based, not a trained sequence labeller.

When numeric ratings are available they are fused with the text score so that a
blank comment still yields a sensible label.
"""
from __future__ import annotations

import math
import re
from typing import Iterable

POSITIVE = {
    "good", "great", "excellent", "amazing", "helpful", "clear", "understand",
    "understandable", "easy", "engaging", "interactive", "interesting", "useful",
    "practical", "patient", "supportive", "encouraging", "well", "best", "love",
    "liked", "like", "enjoy", "enjoyed", "effective", "informative", "organized",
    "friendly", "motivating", "confident", "improved", "improvement", "awesome",
    "wonderful", "perfect", "valuable", "insightful", "recommend", "appreciate",
    "collaborative", "fun", "exciting", "responsive", "thorough", "clarify",
}

NEGATIVE = {
    "bad", "poor", "boring", "confusing", "confused", "unclear", "difficult",
    "hard", "slow", "fast", "rushed", "unhelpful", "useless", "disappointing",
    "disappointed", "weak", "worse", "worst", "hate", "hated", "dislike",
    "disliked", "messy", "disorganized", "ignored", "ignore", "unfair",
    "frustrating", "frustrated", "stressful", "complicated", "lacking",
    "insufficient", "monotonous", "repetitive", "uninteresting", "irrelevant",
    "inaccessible", "unavailable", "late", "biased", "rude", "unprepared",
}

NEGATORS = {
    "not", "no", "never", "none", "nothing", "nobody", "neither", "nor",
    "hardly", "barely", "scarcely", "without", "isn't", "wasn't", "aren't",
    "weren't", "don't", "doesn't", "didn't", "can't", "cannot", "couldn't",
    "won't", "wouldn't", "shouldn't",
}

INTENSIFIERS = {
    "very": 1.6, "really": 1.4, "extremely": 2.0, "so": 1.3, "too": 1.4,
    "highly": 1.6, "super": 1.5, "quite": 1.2, "absolutely": 1.8,
    "incredibly": 1.8, "somewhat": 0.7, "slightly": 0.6, "little": 0.7,
}

ASPECTS = {
    "clarity": {"clear", "clarity", "explain", "explanation", "understand",
                "understandable", "confusing", "confused", "unclear", "simple"},
    "interaction": {"interactive", "interaction", "discussion", "questions",
                    "participate", "participation", "responsive", "engage",
                    "engaging", "attention", "doubt", "doubts"},
    "methodology": {"method", "methodology", "teaching", "approach", "lecture",
                    "activity", "activities", "flipped", "project", "practical",
                    "demonstration", "collaborative", "group"},
    "practical": {"practical", "example", "examples", "real", "application",
                  "demo", "demonstration", "hands-on", "experiment", "lab"},
    "difficulty": {"difficult", "hard", "easy", "fast", "rushed", "slow",
                   "complicated", "stressful", "pace"},
    "materials": {"material", "materials", "notes", "slides", "worksheet",
                  "resource", "resources", "book", "content"},
}

_TOKEN_RE = re.compile(r"[a-z][a-z'\-]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _score_tokens(tokens: list[str]) -> tuple[float, list[str]]:
    total = 0.0
    matched: list[str] = []
    for index, token in enumerate(tokens):
        base = 0.0
        if token in POSITIVE:
            base = 1.0
        elif token in NEGATIVE:
            base = -1.0
        if base == 0.0:
            continue

        # Look back up to two tokens for negation / intensification.
        window = tokens[max(0, index - 2): index]
        for previous in window:
            if previous in NEGATORS:
                base *= -0.85
            if previous in INTENSIFIERS:
                base *= INTENSIFIERS[previous]

        total += base
        matched.append(token)
    return total, matched


def _label(score: float) -> str:
    if score >= 0.15:
        return "positive"
    if score <= -0.15:
        return "negative"
    return "neutral"


def analyze_text(text: str) -> dict:
    """Analyse a free-text comment. Returns a score in [-1, 1] and aspects."""
    text = (text or "").strip()
    if not text:
        return {"score": 0.0, "label": "neutral", "keywords": [], "aspects": {}}

    sentences = [segment for segment in re.split(r"[.!?;]+", text) if segment.strip()]
    scores: list[float] = []
    keywords: list[str] = []
    aspect_scores: dict[str, list[float]] = {}

    for sentence in sentences:
        tokens = _tokens(sentence)
        total, matched = _score_tokens(tokens)
        if matched:
            scores.append(math.tanh(total / max(2.0, len(matched) + 1)))
            keywords.extend(matched)
        for aspect, vocabulary in ASPECTS.items():
            if any(token in vocabulary for token in tokens):
                aspect_scores.setdefault(aspect, []).append(
                    math.tanh(total / max(2.0, len(matched) + 1))
                )

    overall = sum(scores) / len(scores) if scores else 0.0
    aspects = {
        aspect: round(sum(values) / len(values), 3)
        for aspect, values in aspect_scores.items()
    }
    return {
        "score": round(overall, 3),
        "label": _label(overall),
        "keywords": sorted(set(keywords)),
        "aspects": aspects,
    }


def analyze_feedback(comment: str | None, ratings: Iterable[int] | None = None) -> dict:
    """Fuse text sentiment with 1-5 ratings into a single explainable result.

    Text carries 65% of the weight when it contains sentiment words, otherwise
    the ratings carry the full weight.
    """
    text_result = analyze_text(comment or "")
    rating_list = [float(r) for r in (ratings or []) if r is not None]
    rating_score = None
    if rating_list:
        average = sum(rating_list) / len(rating_list)
        rating_score = max(-1.0, min(1.0, (average - 3.0) / 2.0))

    if rating_score is None:
        final = text_result["score"]
    elif not text_result["keywords"]:
        final = rating_score
    else:
        final = 0.65 * text_result["score"] + 0.35 * rating_score

    return {
        "label": _label(final),
        "score": round(final, 3),
        "text_score": text_result["score"],
        "rating_score": None if rating_score is None else round(rating_score, 3),
        "keywords": text_result["keywords"],
        "aspects": text_result["aspects"],
        "method": "lexicon+ratings-fusion-v1",
    }
