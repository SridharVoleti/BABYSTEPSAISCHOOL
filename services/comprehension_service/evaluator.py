"""
2026-02-19: LLM-based comprehension evaluator (BS-CMP).

Purpose:
    Use the configured LLM provider to score a student's verbal explanation
    across 5 dimensions: understanding, accuracy, own_words, depth, clarity.
    Provides a structured JSON response with scores (0-100) and feedback.

Design:
    Wraps the llm_service factory. On any LLM error, falls back to neutral
    scores (all 50) and sets llm_error=True so the flow is never blocked.
"""

import json  # 2026-02-19: JSON parsing
import logging  # 2026-02-19: Logging

from services.llm_service.factory import get_llm_provider  # 2026-02-19: LLM provider (module-level for testability)

logger = logging.getLogger(__name__)  # 2026-02-19: Module logger

# 2026-02-19: Evaluation prompt template
EVAL_PROMPT_TEMPLATE = """\
You are evaluating a primary school student's comprehension of a lesson.
Score each dimension from 0 to 100 (integers only).

Lesson topic: {topic}
Lesson summary: {lesson_summary}
Student explanation: {student_text}

Scoring guide:
- understanding (0-100): Does the student grasp the main idea?
- accuracy (0-100): Are the facts stated correctly?
- own_words (0-100): Did the student rephrase rather than copy?
- depth (0-100): Did the student add detail or examples?
- clarity (0-100): Is the explanation easy to follow?

Respond ONLY as valid JSON with exactly these keys:
{{"understanding": N, "accuracy": N, "own_words": N, "depth": N, "clarity": N, "feedback": "one encouraging sentence"}}"""

# 2026-02-19: Default fallback when LLM is unavailable
FALLBACK_SCORES = {
    'understanding': 50,
    'accuracy': 50,
    'own_words': 50,
    'depth': 50,
    'clarity': 50,
    'feedback': 'Great effort! Keep practising your explanations.',
    'llm_error': True,
}


def evaluate_explanation(student_text: str, lesson_summary: str, topic: str) -> dict:
    """
    2026-02-19: Score a student's explanation using the LLM provider.

    Calls the configured LLM with a structured prompt and parses the JSON
    response into a dict with 5 integer scores (0-100) plus a feedback string.
    On any failure (network, parse, validation), returns FALLBACK_SCORES.

    Args:
        student_text: The student's explanation text.
        lesson_summary: Short summary / concept text from the lesson JSON.
        topic: The lesson topic / title for context.

    Returns:
        dict with keys: understanding, accuracy, own_words, depth, clarity,
                        feedback (str), llm_error (bool).
    """
    prompt = EVAL_PROMPT_TEMPLATE.format(  # 2026-02-19: Build prompt
        topic=topic,
        lesson_summary=lesson_summary[:1000],  # 2026-02-19: Trim to avoid token overflow
        student_text=student_text[:500],  # 2026-02-19: Trim student text
    )

    try:
        llm = get_llm_provider()  # 2026-02-19: Get provider (singleton)
        response = llm.chat(  # 2026-02-19: Call LLM
            message=prompt,
            system_prompt='You are a helpful educational assessment assistant.',
        )
        raw_text = response.text.strip()  # 2026-02-19: Get response text

        # 2026-02-19: Strip markdown fences if present
        if raw_text.startswith('```'):
            lines = raw_text.split('\n')
            raw_text = '\n'.join(
                line for line in lines
                if not line.startswith('```')
            ).strip()

        parsed = json.loads(raw_text)  # 2026-02-19: Parse JSON

        # 2026-02-19: Validate required keys and score range
        required_dims = ('understanding', 'accuracy', 'own_words', 'depth', 'clarity')
        for key in required_dims:  # 2026-02-19: Check each dimension
            if key not in parsed:
                raise ValueError(f"Missing key: {key}")
            val = parsed[key]
            if not isinstance(val, (int, float)):
                raise ValueError(f"Non-numeric score for {key}: {val}")
            parsed[key] = max(0, min(100, int(val)))  # 2026-02-19: Clamp 0-100

        parsed['feedback'] = str(parsed.get('feedback', ''))  # 2026-02-19: Ensure string
        parsed['llm_error'] = False  # 2026-02-19: Success flag

        return parsed  # 2026-02-19: Return validated scores

    except Exception as exc:  # 2026-02-19: Any failure → fallback
        logger.warning(  # 2026-02-19: Log warning
            f"LLM evaluation failed, using fallback scores: {exc}"
        )
        return dict(FALLBACK_SCORES)  # 2026-02-19: Return copy of fallback


# 2026-02-21: Prompt template for marks-based key-point evaluation
KEY_POINT_PROMPT_TEMPLATE = """\
You are evaluating a school student's answer to a comprehension question.

Question ({marks} marks): {question}
Model answer: {model_answer}
Student's answer: {student_text}

For each key point below, decide whether the student's answer addresses it — even if stated in different words.
{key_points_numbered}

Respond ONLY as valid JSON with exactly these keys:
{{"covered": [{covered_placeholders}], "feedback": "one encouraging sentence"}}

"covered" must be a JSON array of true/false values, one per key point."""


def evaluate_key_points(
    student_text: str,
    key_points: list,
    question: str,
    model_answer: str = '',
) -> dict:
    """
    2026-02-21: Evaluate whether a student's answer covers each key point.

    Calls the configured LLM with a structured prompt and parses the JSON
    response into a dict with a boolean 'covered' list and a feedback string.
    On any failure, falls back to all-False with llm_error=True so the flow
    is never blocked.

    Args:
        student_text: The student's typed or transcribed answer.
        key_points: List of key point strings from the question JSON.
        question: The question text (for LLM context).
        model_answer: Optional ideal answer for LLM calibration.

    Returns:
        dict with keys: covered (list[bool]), feedback (str), llm_error (bool).
    """
    n = len(key_points)  # 2026-02-21: Number of key points

    # 2026-02-21: Build numbered key-point list for prompt
    key_points_numbered = '\n'.join(
        f'{i + 1}. {kp}' for i, kp in enumerate(key_points)
    )

    # 2026-02-21: Build the placeholder string for JSON response
    covered_placeholders = ', '.join('true/false' for _ in key_points)

    prompt = KEY_POINT_PROMPT_TEMPLATE.format(
        marks=n,
        question=question[:500],  # 2026-02-21: Trim to avoid token overflow
        model_answer=model_answer[:800],  # 2026-02-21: Trim model answer
        student_text=student_text[:500],  # 2026-02-21: Trim student text
        key_points_numbered=key_points_numbered,
        covered_placeholders=covered_placeholders,
    )

    try:
        llm = get_llm_provider()  # 2026-02-21: Get provider (singleton)
        response = llm.chat(  # 2026-02-21: Call LLM
            message=prompt,
            system_prompt='You are a helpful educational assessment assistant.',
        )
        raw_text = response.text.strip()  # 2026-02-21: Get response text

        # 2026-02-21: Strip markdown fences if present
        if raw_text.startswith('```'):
            lines = raw_text.split('\n')
            raw_text = '\n'.join(
                line for line in lines
                if not line.startswith('```')
            ).strip()

        parsed = json.loads(raw_text)  # 2026-02-21: Parse JSON

        # 2026-02-21: Validate 'covered' array
        covered_raw = parsed.get('covered', [])
        if not isinstance(covered_raw, list) or len(covered_raw) != n:
            raise ValueError(
                f"'covered' must be a list of {n} booleans, got: {covered_raw}"
            )

        covered = [bool(v) for v in covered_raw]  # 2026-02-21: Normalise to bool
        feedback = str(parsed.get('feedback', ''))  # 2026-02-21: Ensure string

        return {  # 2026-02-21: Return validated result
            'covered': covered,
            'feedback': feedback,
            'llm_error': False,
        }

    except Exception as exc:  # 2026-02-21: Any failure → fallback
        logger.warning(  # 2026-02-21: Log warning
            f"Key-point evaluation failed, using fallback: {exc}"
        )
        return {  # 2026-02-21: All-False fallback
            'covered': [False] * n,
            'feedback': 'Great effort! Keep practising your explanations.',
            'llm_error': True,
        }
