"""
2026-02-19: Anti-parroting detector for comprehension submissions (BS-CMP).

Purpose:
    Detect when a student has copied the lesson text verbatim rather than
    explaining it in their own words. Uses simple noun-overlap heuristic:
    if ≥70% of the lesson's significant nouns appear in the student's text,
    it is flagged as parroting.

Design:
    Pure functions, no DB/LLM dependency. Safe to call synchronously.
"""

import re  # 2026-02-19: Regex for word extraction

# 2026-02-19: Common English stopwords to exclude from noun extraction
STOPWORDS = frozenset([
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have', 'had',
    'will', 'would', 'can', 'could', 'should', 'that', 'this', 'with',
    'for', 'from', 'into', 'onto', 'upon', 'they', 'their', 'them',
    'and', 'but', 'or', 'nor', 'not', 'does', 'did', 'been', 'being',
    'when', 'where', 'what', 'who', 'how', 'why', 'which', 'all',
    'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
    'such', 'than', 'then', 'there', 'these', 'those', 'very',
])


def extract_nouns(text: str) -> set:
    """
    2026-02-19: Extract significant content words (≥4 chars, not stopwords).

    Args:
        text: Input text string.

    Returns:
        set[str]: Lowercase content words of at least 4 characters.
    """
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())  # 2026-02-19: 4+ char words
    return {w for w in words if w not in STOPWORDS}  # 2026-02-19: Remove stopwords


def is_parroting(student_text: str, lesson_text: str, threshold: float = 0.70) -> bool:
    """
    2026-02-19: Detect if student has copied lesson text rather than rephrasing.

    Computes the fraction of lesson's significant nouns that appear in the
    student's text. If the overlap fraction meets or exceeds `threshold`,
    the submission is considered parroting.

    Args:
        student_text: The student's explanation text.
        lesson_text: The lesson's concept/teaching text to compare against.
        threshold: Overlap fraction that triggers parroting flag (default 0.70).

    Returns:
        bool: True if parroting detected, False otherwise.
              Always False if lesson_text has no extractable nouns.
    """
    lesson_nouns = extract_nouns(lesson_text)  # 2026-02-19: Extract lesson nouns
    if not lesson_nouns:  # 2026-02-19: Safe default — can't parrot empty lesson
        return False

    student_nouns = extract_nouns(student_text)  # 2026-02-19: Extract student nouns
    overlap = len(student_nouns & lesson_nouns) / len(lesson_nouns)  # 2026-02-19: Fraction
    return overlap >= threshold  # 2026-02-19: Parroting if meets threshold
