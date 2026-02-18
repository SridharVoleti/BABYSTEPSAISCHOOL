"""
2026-02-17: Adaptive mastery practice engine (BS-STR).

Purpose:
    Manages adaptive difficulty selection, star rating calculation,
    and question selection for mastery practice sessions. Controls
    the difficulty curve based on consecutive correct/incorrect answers.
"""

import random  # 2026-02-17: Random question selection


# 2026-02-17: Question count ranges per IQ level
QUESTION_COUNTS = {
    'foundation': (12, 15),
    'standard': (8, 10),
    'advanced': (5, 7),
}

# 2026-02-17: Starting difficulty per IQ level
STARTING_DIFFICULTY = {
    'foundation': 'easy',
    'standard': 'medium',
    'advanced': 'medium',
}

# 2026-02-17: Difficulty ordering for adaptation
DIFFICULTY_ORDER = ['easy', 'medium', 'hard']

# 2026-02-17: Star rating thresholds (percentage correct)
STAR_THRESHOLDS = [
    (81, 5),  # 2026-02-17: 81-100% → 5 stars
    (61, 4),  # 2026-02-17: 61-80% → 4 stars
    (41, 3),  # 2026-02-17: 41-60% → 3 stars
    (21, 2),  # 2026-02-17: 21-40% → 2 stars
    (0, 1),   # 2026-02-17: 0-20% → 1 star
]

# 2026-02-17: Mastery gate threshold (minimum stars to unlock next day)
MASTERY_GATE_STARS = 3

# 2026-02-17: Consecutive answers to trigger difficulty change
ADAPT_THRESHOLD = 2

# 2026-02-17: Max consecutive questions at same difficulty
MAX_SAME_DIFFICULTY = 3


class AdaptiveEngine:
    """
    2026-02-17: Adaptive difficulty engine for mastery practice.

    Controls question count, starting difficulty, difficulty adaptation,
    question selection, and star rating calculation.
    """

    @staticmethod
    def get_total_questions(iq_level):
        """
        2026-02-17: Get total question count for an IQ level.

        Picks a random count within the range for the given IQ level.

        Args:
            iq_level: One of 'foundation', 'standard', 'advanced'.

        Returns:
            int: Number of questions for the practice session.
        """
        min_q, max_q = QUESTION_COUNTS.get(iq_level, (8, 10))  # 2026-02-17: Default to standard
        return random.randint(min_q, max_q)  # 2026-02-17: Random in range

    @staticmethod
    def get_starting_difficulty(iq_level):
        """
        2026-02-17: Get starting difficulty for an IQ level.

        Args:
            iq_level: One of 'foundation', 'standard', 'advanced'.

        Returns:
            str: Starting difficulty ('easy', 'medium', or 'hard').
        """
        return STARTING_DIFFICULTY.get(iq_level, 'medium')  # 2026-02-17: Default to medium

    @staticmethod
    def adapt_difficulty(current_difficulty, consecutive_correct,
                         consecutive_incorrect, same_difficulty_streak):
        """
        2026-02-17: Compute next difficulty based on adaptive rules.

        Rules:
        - 2 consecutive correct → increase difficulty (if possible)
        - 2 consecutive incorrect → decrease difficulty (if possible)
        - Never more than 3 consecutive same-difficulty questions

        Args:
            current_difficulty: Current difficulty level.
            consecutive_correct: Consecutive correct answers.
            consecutive_incorrect: Consecutive incorrect answers.
            same_difficulty_streak: Same-difficulty question count.

        Returns:
            str: Next difficulty level.
        """
        current_idx = DIFFICULTY_ORDER.index(current_difficulty)  # 2026-02-17: Current position

        # 2026-02-17: Force change if at max same-difficulty streak
        if same_difficulty_streak >= MAX_SAME_DIFFICULTY:
            if current_idx < len(DIFFICULTY_ORDER) - 1:  # 2026-02-17: Can go up
                return DIFFICULTY_ORDER[current_idx + 1]
            elif current_idx > 0:  # 2026-02-17: Can go down
                return DIFFICULTY_ORDER[current_idx - 1]

        # 2026-02-17: Adapt based on consecutive streaks
        if consecutive_correct >= ADAPT_THRESHOLD:
            if current_idx < len(DIFFICULTY_ORDER) - 1:  # 2026-02-17: Increase
                return DIFFICULTY_ORDER[current_idx + 1]
        elif consecutive_incorrect >= ADAPT_THRESHOLD:
            if current_idx > 0:  # 2026-02-17: Decrease
                return DIFFICULTY_ORDER[current_idx - 1]

        return current_difficulty  # 2026-02-17: No change

    @staticmethod
    def calculate_star_rating(questions_correct, total_questions):
        """
        2026-02-17: Calculate star rating from score percentage.

        Args:
            questions_correct: Number of correct answers.
            total_questions: Total questions answered.

        Returns:
            int: Star rating (1-5). Minimum 1 star for attempting.
        """
        if total_questions == 0:  # 2026-02-17: No questions
            return 0

        percentage = (questions_correct * 100) / total_questions  # 2026-02-17: Calculate %

        for threshold, stars in STAR_THRESHOLDS:  # 2026-02-17: Check thresholds
            if percentage >= threshold:  # 2026-02-17: First match wins
                return stars

        return 1  # 2026-02-17: Minimum 1 star

    @staticmethod
    def is_mastery_passed(star_rating):
        """
        2026-02-17: Check if star rating passes the mastery gate.

        Args:
            star_rating: Star rating (0-5).

        Returns:
            bool: True if rating >= MASTERY_GATE_STARS (3).
        """
        return star_rating >= MASTERY_GATE_STARS  # 2026-02-17: Check gate

    @staticmethod
    def select_question(practice_bank, difficulty, administered_ids):
        """
        2026-02-17: Select next question from the practice bank.

        Picks a random unadministered question at the given difficulty.
        Falls back to adjacent difficulties if none available.

        Args:
            practice_bank: dict with 'easy', 'medium', 'hard' question lists.
            difficulty: Target difficulty level.
            administered_ids: Set of already-used question IDs.

        Returns:
            tuple: (question_dict, actual_difficulty) or (None, None) if exhausted.
        """
        # 2026-02-17: Try target difficulty first, then adjacent
        difficulty_order = [difficulty]  # 2026-02-17: Start with target
        current_idx = DIFFICULTY_ORDER.index(difficulty)  # 2026-02-17: Position

        # 2026-02-17: Add adjacent difficulties as fallbacks
        if current_idx > 0:
            difficulty_order.append(DIFFICULTY_ORDER[current_idx - 1])
        if current_idx < len(DIFFICULTY_ORDER) - 1:
            difficulty_order.append(DIFFICULTY_ORDER[current_idx + 1])

        for diff in difficulty_order:  # 2026-02-17: Try each difficulty
            questions = practice_bank.get(diff, [])  # 2026-02-17: Get pool
            available = [  # 2026-02-17: Filter out administered
                q for q in questions
                if q.get('id') not in administered_ids
            ]
            if available:  # 2026-02-17: Found available questions
                question = random.choice(available)  # 2026-02-17: Random pick
                return question, diff  # 2026-02-17: Return with actual difficulty

        return None, None  # 2026-02-17: All questions exhausted

    @staticmethod
    def check_answer(question, student_answer):
        """
        2026-02-17: Check if student's answer is correct for any question type.

        Args:
            question: Question dict from practice bank.
            student_answer: Student's answer (type varies by question type).

        Returns:
            tuple: (is_correct, correct_answer, explanation).
        """
        q_type = question.get('type', 'mcq')  # 2026-02-17: Question type
        correct = question.get('correct_answer')  # 2026-02-17: Correct answer
        explanation = question.get('explanation', '')  # 2026-02-17: Feedback text

        if q_type == 'drag_order':  # 2026-02-17: Compare order arrays
            correct_order = question.get('correct_order', [])  # 2026-02-17: Expected order
            is_correct = student_answer == correct_order  # 2026-02-17: Exact match
            return is_correct, correct_order, explanation

        # 2026-02-17: MCQ, true_false, numeric_fill — direct comparison
        is_correct = student_answer == correct  # 2026-02-17: Compare
        return is_correct, correct, explanation
