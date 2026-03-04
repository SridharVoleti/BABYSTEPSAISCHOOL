"""
2026-03-03: Mental Maths Drill service (AMT-APE-005).

Purpose:
    Generates timed drill sessions for multiplication tables, squares, and cubes.
    All computation is purely algorithmic — no LLM, no JSON content files.
    Server is the source of truth for questions and correct answers.
"""

import random  # 2026-03-03: Random question sampling
from datetime import datetime, timezone  # 2026-03-03: Timestamps

from services.teaching_engine.adaptive import AdaptiveEngine  # 2026-03-03: Star thresholds

from .models import MathDrillAttempt, MathDrillSession  # 2026-03-03: Drill models

# 2026-03-03: Valid drill types
DRILL_TYPES = ('tables', 'squares', 'cubes')

# 2026-03-03: Valid time limits in seconds
VALID_TIME_LIMITS = (30, 60, 120)


class MathDrillService:
    """
    2026-03-03: Service for Mental Maths Drill sessions (AMT-APE-005).

    Generates timed drill sessions algorithmically. All questions are
    created at session start and stored in the database so the server
    is always the canonical source of correct answers.
    """

    # ── Question generation ────────────────────────────────────────────────

    @staticmethod
    def _generate_questions(drill_type, min_n, max_n, count):
        """
        2026-03-03: Generate a list of unique drill questions.

        Args:
            drill_type: 'tables', 'squares', or 'cubes'.
            min_n: Minimum number in range (inclusive).
            max_n: Maximum number in range (inclusive).
            count: Number of questions to generate.

        Returns:
            list: [{id, question, correct_answer}, ...] with `count` items.

        Raises:
            ValueError: If drill_type is invalid or range has too few unique questions.
        """
        if drill_type == 'tables':  # 2026-03-03: a × b questions
            pool = []  # 2026-03-03: All possible (a, b) pairs
            for a in range(min_n, max_n + 1):
                for b in range(min_n, max_n + 1):
                    pool.append((a, b))  # 2026-03-03: Each pair is unique
            if len(pool) < count:  # 2026-03-03: Guard against insufficient pool
                count = len(pool)  # 2026-03-03: Clamp to pool size
            sampled = random.sample(pool, count)  # 2026-03-03: Sample without replacement
            questions = []
            for idx, (a, b) in enumerate(sampled):
                questions.append({
                    'id': f'q{idx}',
                    'question': f'{a} × {b} = ?',
                    'correct_answer': a * b,
                })
            return questions

        elif drill_type == 'squares':  # 2026-03-03: n² questions
            pool = list(range(min_n, max_n + 1))  # 2026-03-03: All n values
            if len(pool) < count:  # 2026-03-03: Clamp if range too small
                count = len(pool)
            sampled = random.sample(pool, count)  # 2026-03-03: Sample without replacement
            questions = []
            for idx, n in enumerate(sampled):
                questions.append({
                    'id': f'q{idx}',
                    'question': f'{n}² = ?',
                    'correct_answer': n * n,
                })
            return questions

        elif drill_type == 'cubes':  # 2026-03-03: n³ questions
            pool = list(range(min_n, max_n + 1))  # 2026-03-03: All n values
            if len(pool) < count:  # 2026-03-03: Clamp if range too small
                count = len(pool)
            sampled = random.sample(pool, count)  # 2026-03-03: Sample without replacement
            questions = []
            for idx, n in enumerate(sampled):
                questions.append({
                    'id': f'q{idx}',
                    'question': f'{n}³ = ?',
                    'correct_answer': n * n * n,
                })
            return questions

        else:
            raise ValueError(f'Unknown drill_type: {drill_type}')  # 2026-03-03: Guard

    # ── Session management ─────────────────────────────────────────────────

    @staticmethod
    def start_drill(student, drill_type, min_n=1, max_n=12,
                    time_limit=60, total_questions=10):
        """
        2026-03-03: Create a new MathDrillSession for the given student.

        Args:
            student: Student model instance.
            drill_type: 'tables', 'squares', or 'cubes'.
            min_n: Lower bound of number range (1-20).
            max_n: Upper bound of number range (1-20).
            time_limit: Session duration in seconds (30, 60, or 120).
            total_questions: Number of questions (5-20, default 10).

        Returns:
            dict: {success, session_id, drill_type, questions (no correct_answer),
                   time_limit_seconds, total_questions} on success.
                  {success: False, error} on failure.
        """
        # 2026-03-03: Validate drill type
        if drill_type not in DRILL_TYPES:
            return {
                'success': False,
                'error': f"Invalid drill_type '{drill_type}'. Must be one of: {DRILL_TYPES}.",
            }

        # 2026-03-03: Validate time limit
        if time_limit not in VALID_TIME_LIMITS:
            return {
                'success': False,
                'error': f"Invalid time_limit '{time_limit}'. Must be one of: {VALID_TIME_LIMITS}.",
            }

        # 2026-03-03: Validate number range
        if min_n < 1 or max_n > 20 or min_n > max_n:
            return {
                'success': False,
                'error': 'number_range_min must be ≥ 1, number_range_max ≤ 20, and min ≤ max.',
            }

        # 2026-03-03: Validate question count (service allows 1+; API serializer enforces 5-20)
        if total_questions < 1:
            return {
                'success': False,
                'error': 'total_questions must be at least 1.',
            }

        # 2026-03-03: Generate questions algorithmically
        questions = MathDrillService._generate_questions(
            drill_type, min_n, max_n, total_questions
        )
        actual_count = len(questions)  # 2026-03-03: May be clamped if pool is small

        # 2026-03-03: Create session with full questions (including correct_answer)
        session = MathDrillSession.objects.create(
            student=student,
            drill_type=drill_type,
            number_range_min=min_n,
            number_range_max=max_n,
            time_limit_seconds=time_limit,
            total_questions=actual_count,
            questions=questions,
            status='active',
        )

        # 2026-03-03: Return questions without correct_answer (client-safe)
        public_questions = [
            {'id': q['id'], 'question': q['question']}
            for q in questions
        ]

        return {
            'success': True,
            'session_id': str(session.id),
            'drill_type': drill_type,
            'questions': public_questions,
            'time_limit_seconds': time_limit,
            'total_questions': actual_count,
        }

    @staticmethod
    def submit_answer(session_id, question_index, answer, response_time_ms=None):
        """
        2026-03-03: Submit a student answer for a drill question.

        Args:
            session_id: UUID string of the MathDrillSession.
            question_index: 0-based index of the question being answered.
            answer: Student's answer string.
            response_time_ms: Optional time taken in milliseconds.

        Returns:
            dict: {success, is_correct, correct_answer, drill_complete, score, star_rating}.
                  {success: False, error} on validation failure.
        """
        # 2026-03-03: Look up session
        try:
            session = MathDrillSession.objects.get(id=session_id)
        except MathDrillSession.DoesNotExist:
            return {'success': False, 'error': 'Drill session not found.'}

        # 2026-03-03: Guard — session must be active
        if session.status != 'active':
            return {
                'success': False,
                'error': f"Session is '{session.status}', not active.",
            }

        # 2026-03-03: Guard — question index must be valid
        if question_index < 0 or question_index >= len(session.questions):
            return {
                'success': False,
                'error': f"Invalid question_index {question_index}. "
                         f"Session has {len(session.questions)} questions (0-{len(session.questions) - 1}).",
            }

        # 2026-03-03: Guard — cannot answer same question twice
        already_answered = MathDrillAttempt.objects.filter(
            session=session, question_index=question_index
        ).exists()
        if already_answered:
            return {
                'success': False,
                'error': f'Question index {question_index} has already been answered.',
            }

        # 2026-03-03: Evaluate the answer (pure arithmetic comparison)
        correct_answer = session.questions[question_index]['correct_answer']
        is_correct = str(answer).strip() == str(correct_answer)

        # 2026-03-03: Record the attempt
        MathDrillAttempt.objects.create(
            session=session,
            question_index=question_index,
            student_answer=str(answer).strip(),
            is_correct=is_correct,
            response_time_ms=response_time_ms,
        )

        # 2026-03-03: Recompute score
        correct_count = MathDrillAttempt.objects.filter(
            session=session, is_correct=True
        ).count()
        session.score = correct_count
        session.save(update_fields=['score'])

        # 2026-03-03: Check if all questions have been answered
        answered_count = MathDrillAttempt.objects.filter(session=session).count()
        drill_complete = answered_count >= session.total_questions

        if drill_complete:  # 2026-03-03: Finalise on last question
            MathDrillService._finalise(session, final_status='completed')
            session.refresh_from_db()  # 2026-03-03: Pick up star_rating

        return {
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'drill_complete': drill_complete,
            'score': session.score,
            'star_rating': session.star_rating,
        }

    @staticmethod
    def _finalise(session, final_status='completed'):
        """
        2026-03-03: Finalise a drill session — compute star rating and mark done.

        Args:
            session: MathDrillSession instance (already has updated score).
            final_status: 'completed' (normal) or 'expired' (timer ran out).
        """
        # 2026-03-03: Map score to stars using AdaptiveEngine thresholds
        star_rating = AdaptiveEngine.calculate_star_rating(
            session.score, session.total_questions
        )

        # 2026-03-03: Update session
        session.status = final_status
        session.star_rating = star_rating
        session.completed_at = datetime.now(tz=timezone.utc)
        session.save(update_fields=['status', 'star_rating', 'completed_at'])

    @staticmethod
    def complete_drill(session_id):
        """
        2026-03-03: Force-complete a drill session (called on timer expiry).

        Idempotent — if already completed/expired, returns current state.

        Args:
            session_id: UUID string of the MathDrillSession.

        Returns:
            dict: {success, score, star_rating, total_questions, status}.
        """
        try:
            session = MathDrillSession.objects.get(id=session_id)
        except MathDrillSession.DoesNotExist:
            return {'success': False, 'error': 'Drill session not found.'}

        # 2026-03-03: Idempotent — already finished
        if session.status in ('completed', 'expired'):
            return {
                'success': True,
                'score': session.score,
                'star_rating': session.star_rating,
                'total_questions': session.total_questions,
                'status': session.status,
            }

        # 2026-03-03: Recompute score in case some answers came in just before expiry
        correct_count = MathDrillAttempt.objects.filter(
            session=session, is_correct=True
        ).count()
        session.score = correct_count
        session.save(update_fields=['score'])

        MathDrillService._finalise(session, final_status='expired')
        session.refresh_from_db()  # 2026-03-03: Pick up star_rating

        return {
            'success': True,
            'score': session.score,
            'star_rating': session.star_rating,
            'total_questions': session.total_questions,
            'status': session.status,
        }

    @staticmethod
    def get_drill_status(session_id):
        """
        2026-03-03: Return full session state for mid-session resume or results.

        Args:
            session_id: UUID string of the MathDrillSession.

        Returns:
            dict: Full session state including answered questions.
        """
        try:
            session = MathDrillSession.objects.get(id=session_id)
        except MathDrillSession.DoesNotExist:
            return {'success': False, 'error': 'Drill session not found.'}

        # 2026-03-03: Build questions-with-answers list (include correct_answer when finalised)
        attempts_by_index = {
            a.question_index: a
            for a in session.attempts.all()
        }

        questions_with_answers = []
        for idx, q in enumerate(session.questions):
            entry = {
                'id': q['id'],
                'question': q['question'],
                'index': idx,
                'answered': idx in attempts_by_index,
            }
            if idx in attempts_by_index:
                attempt = attempts_by_index[idx]
                entry['student_answer'] = attempt.student_answer
                entry['is_correct'] = attempt.is_correct
                entry['correct_answer'] = q['correct_answer']  # 2026-03-03: Reveal after answer
            questions_with_answers.append(entry)

        return {
            'success': True,
            'session_id': str(session.id),
            'drill_type': session.drill_type,
            'status': session.status,
            'score': session.score,
            'star_rating': session.star_rating,
            'total_questions': session.total_questions,
            'answered_count': len(attempts_by_index),
            'time_limit_seconds': session.time_limit_seconds,
            'started_at': session.started_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'questions_with_answers': questions_with_answers,
        }

    @staticmethod
    def get_drill_history(student):
        """
        2026-03-03: Return the last 20 completed/expired drill sessions for a student.

        Args:
            student: Student model instance.

        Returns:
            dict: {success, sessions: [{session_id, drill_type, score,
                   total_questions, star_rating, status, started_at}, ...]}.
        """
        sessions = MathDrillSession.objects.filter(
            student=student,
            status__in=('completed', 'expired'),
        ).order_by('-started_at')[:20]  # 2026-03-03: Last 20

        history = []
        for s in sessions:
            history.append({
                'session_id': str(s.id),
                'drill_type': s.drill_type,
                'score': s.score,
                'total_questions': s.total_questions,
                'star_rating': s.star_rating,
                'status': s.status,
                'started_at': s.started_at.isoformat(),
            })

        return {
            'success': True,
            'sessions': history,
        }
