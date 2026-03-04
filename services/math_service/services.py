"""
2026-03-02: Math Service business logic (BS-MTH module).

Purpose:
    Orchestrate math lesson listing, session creation, answer submission,
    hint requests, and progress aggregation. Delegates content loading to
    MathContentLoader and evaluation to MathEvaluator.
"""

import logging  # 2026-03-02: Logging

from django.utils import timezone  # 2026-03-02: Timezone-aware timestamps

from services.diagnostic_service.models import DiagnosticResult  # 2026-03-02: IQ level source
from services.teaching_engine.adaptive import AdaptiveEngine  # 2026-03-02: Star rating util
from .models import MathLesson, MathSession, MathProblemAttempt  # 2026-03-02: Own models
from .content_loader import MathContentLoader  # 2026-03-02: Content loader
from .evaluator import MathEvaluator  # 2026-03-02: Answer evaluator

logger = logging.getLogger(__name__)  # 2026-03-02: Module logger


class MathService:
    """
    2026-03-02: Core business logic for the Math Practice module (BS-MTH).

    All methods return plain dict responses with a 'success' key.
    Views should check success before returning HTTP responses.
    """

    @classmethod
    def get_student_iq_level(cls, student) -> str:
        """
        2026-03-02: Get student's IQ level from diagnostic result.

        Falls back to 'standard' if no diagnostic result exists.

        Args:
            student: Student model instance.

        Returns:
            str: One of 'foundation', 'standard', 'advanced'.
        """
        result = DiagnosticResult.objects.filter(student=student).first()  # 2026-03-02: Lookup
        if not result:  # 2026-03-02: No diagnostic result
            return 'standard'  # 2026-03-02: Default fallback
        return result.overall_level  # 2026-03-02: From diagnostic

    @classmethod
    def list_lessons(cls, class_number: int) -> dict:
        """
        2026-03-02: List published math lessons for a given grade.

        Args:
            class_number: Grade number (1-12).

        Returns:
            dict: {success: True, lessons: [...]}
        """
        queryset = MathLesson.objects.filter(  # 2026-03-02: Published only
            class_number=class_number, status='published'
        )
        lessons = []  # 2026-03-02: Build list
        for lesson in queryset:  # 2026-03-02: Iterate
            lessons.append({  # 2026-03-02: Lesson summary
                'lesson_id': lesson.lesson_id,
                'title': lesson.title,
                'class_number': lesson.class_number,
                'week_number': lesson.week_number,
                'topic': lesson.topic,
            })
        return {'success': True, 'lessons': lessons}  # 2026-03-02: Return

    @classmethod
    def get_lesson_detail(cls, lesson_id: str) -> dict:
        """
        2026-03-02: Get lesson metadata plus day titles from JSON.

        Args:
            lesson_id: MathLesson.lesson_id string.

        Returns:
            dict: {success, lesson_id, title, topic, days: [{day, title}]}
        """
        lesson = MathLesson.objects.filter(  # 2026-03-02: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-03-02: Not found
            return {'success': False, 'error': 'Lesson not found.'}

        try:
            data = MathContentLoader.load_lesson(lesson.content_json_path)  # 2026-03-02: Load JSON
        except FileNotFoundError:  # 2026-03-02: JSON file missing
            return {'success': False, 'error': 'Lesson content file not found.'}

        days = [  # 2026-03-02: Extract day titles
            {'day': d.get('day'), 'title': d.get('title')}
            for d in data.get('days', [])
        ]

        return {  # 2026-03-02: Detail response
            'success': True,
            'lesson_id': lesson.lesson_id,
            'title': lesson.title,
            'topic': lesson.topic,
            'class_number': lesson.class_number,
            'week_number': lesson.week_number,
            'character': data.get('character', ''),
            'learning_objectives': data.get('learning_objectives', []),
            'days': days,
        }

    @classmethod
    def start_session(cls, student, lesson_id: str, day_number: int) -> dict:
        """
        2026-03-02: Start a math practice session for a lesson day.

        Looks up student IQ level, loads day problems from JSON,
        creates a MathSession, and returns the first problem.

        Args:
            student: Student model instance.
            lesson_id: MathLesson.lesson_id string.
            day_number: Day to practice (1-4).

        Returns:
            dict: {success, session_id, iq_level, total_problems, first_problem}
        """
        lesson = MathLesson.objects.filter(  # 2026-03-02: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-03-02: Not found
            return {'success': False, 'error': 'Lesson not found.'}

        if day_number < 1 or day_number > 4:  # 2026-03-02: Validate day
            return {'success': False, 'error': 'day_number must be between 1 and 4.'}

        iq_level = cls.get_student_iq_level(student)  # 2026-03-02: Get IQ level

        try:
            problems = MathContentLoader.get_day_problems(  # 2026-03-02: Load problems
                lesson.content_json_path, day_number, iq_level
            )
        except (FileNotFoundError, ValueError) as exc:  # 2026-03-02: Content errors
            return {'success': False, 'error': str(exc)}

        session = MathSession.objects.create(  # 2026-03-02: Create session
            student=student,
            lesson=lesson,
            day_number=day_number,
            iq_level=iq_level,
            status='active',
            total_problems=len(problems),
        )

        first_problem = cls._sanitise_problem(problems[0]) if problems else None  # 2026-03-02: First

        return {  # 2026-03-02: Start response
            'success': True,
            'session_id': str(session.id),
            'lesson_id': lesson_id,
            'day_number': day_number,
            'iq_level': iq_level,
            'total_problems': len(problems),
            'problems': [cls._sanitise_problem(p) for p in problems],  # 2026-03-02: All problems
            'first_problem': first_problem,
        }

    @classmethod
    def submit_answer(cls, session_id: str, problem_id: str, student_answer: str,
                      time_taken: int = None) -> dict:
        """
        2026-03-02: Submit an answer for a problem in an active session.

        Loads the problem from JSON, evaluates the answer, creates a
        MathProblemAttempt, and computes star_rating if session is complete.

        Args:
            session_id: UUID string of the MathSession.
            problem_id: Problem ID from JSON.
            student_answer: Student's raw answer string.
            time_taken: Optional seconds taken to answer.

        Returns:
            dict: {success, is_correct, feedback, correct_answer, worked_steps,
                   problems_correct, total_problems, session_complete, star_rating}
        """
        try:
            session = MathSession.objects.get(id=session_id)  # 2026-03-02: Get session
        except MathSession.DoesNotExist:  # 2026-03-02: Not found
            return {'success': False, 'error': 'Session not found.'}

        if session.status == 'completed':  # 2026-03-02: Already done
            return {'success': False, 'error': 'Session already completed.'}

        # 2026-03-02: Load problem from JSON
        problem = MathContentLoader.get_problem_by_id(
            session.lesson.content_json_path, problem_id
        )
        if problem is None:  # 2026-03-02: Problem not found
            return {'success': False, 'error': f'Problem {problem_id} not found.'}

        # 2026-03-02: Evaluate the answer
        eval_result = MathEvaluator.evaluate(problem, student_answer)  # 2026-03-02: Evaluate

        # 2026-03-02: Record attempt (update if exists, create if not)
        attempt, created = MathProblemAttempt.objects.get_or_create(  # 2026-03-02: Get or create
            session=session,
            problem_id=problem_id,
            defaults={
                'problem_type': problem.get('type', 'mcq'),
                'student_answer': student_answer,
                'is_correct': eval_result['is_correct'],
                'feedback': eval_result['feedback'],
                'time_taken_seconds': time_taken,
            },
        )

        if not created:  # 2026-03-02: Update existing attempt
            attempt.student_answer = student_answer  # 2026-03-02: Update answer
            attempt.is_correct = eval_result['is_correct']  # 2026-03-02: Update result
            attempt.feedback = eval_result['feedback']  # 2026-03-02: Update feedback
            if time_taken is not None:  # 2026-03-02: Update time if provided
                attempt.time_taken_seconds = time_taken
            attempt.save()  # 2026-03-02: Persist

        # 2026-03-02: Recount correct answers from all attempts in this session
        all_attempts = MathProblemAttempt.objects.filter(session=session)  # 2026-03-02: All attempts
        problems_correct = all_attempts.filter(is_correct=True).count()  # 2026-03-02: Count correct
        total_answered = all_attempts.count()  # 2026-03-02: Total answered

        session.problems_correct = problems_correct  # 2026-03-02: Update session
        session.save(update_fields=['problems_correct'])  # 2026-03-02: Persist

        # 2026-03-02: Check if session is complete (all problems answered)
        session_complete = total_answered >= session.total_problems  # 2026-03-02: Complete check
        star_rating = None  # 2026-03-02: Default

        if session_complete:  # 2026-03-02: Compute stars and close session
            star_rating = AdaptiveEngine.calculate_star_rating(  # 2026-03-02: Reuse adaptive engine
                problems_correct, session.total_problems
            )
            session.status = 'completed'  # 2026-03-02: Mark complete
            session.star_rating = star_rating  # 2026-03-02: Store rating
            session.completed_at = timezone.now()  # 2026-03-02: Record completion time
            session.save(update_fields=['status', 'star_rating', 'completed_at'])  # 2026-03-02: Persist

        return {  # 2026-03-02: Answer submission response
            'success': True,
            'is_correct': eval_result['is_correct'],
            'feedback': eval_result['feedback'],
            'correct_answer': eval_result['correct_answer'],
            'worked_steps': eval_result['worked_steps'],
            'problems_correct': problems_correct,
            'total_problems': session.total_problems,
            'session_complete': session_complete,
            'star_rating': star_rating,
        }

    @classmethod
    def request_hint(cls, session_id: str, problem_id: str) -> dict:
        """
        2026-03-02: Request a progressive hint for a problem in a session.

        Increments hints_used on the attempt record and calls the evaluator.

        Args:
            session_id: UUID string of the MathSession.
            problem_id: Problem ID from JSON.

        Returns:
            dict: {success, hint_text, hint_number}
        """
        try:
            session = MathSession.objects.get(id=session_id)  # 2026-03-02: Get session
        except MathSession.DoesNotExist:  # 2026-03-02: Not found
            return {'success': False, 'error': 'Session not found.'}

        # 2026-03-02: Load problem
        problem = MathContentLoader.get_problem_by_id(
            session.lesson.content_json_path, problem_id
        )
        if problem is None:  # 2026-03-02: Not found
            return {'success': False, 'error': f'Problem {problem_id} not found.'}

        # 2026-03-02: Get or create attempt to track hints_used
        attempt, _ = MathProblemAttempt.objects.get_or_create(  # 2026-03-02: Ensure attempt exists
            session=session,
            problem_id=problem_id,
            defaults={
                'problem_type': problem.get('type', 'mcq'),
                'student_answer': '',
                'is_correct': False,
                'feedback': '',
            },
        )
        attempt.hints_used += 1  # 2026-03-02: Increment hint count
        attempt.save(update_fields=['hints_used'])  # 2026-03-02: Persist

        hint_text = MathEvaluator.generate_hint(problem, attempt.hints_used)  # 2026-03-02: Generate hint

        return {  # 2026-03-02: Hint response
            'success': True,
            'hint_text': hint_text,
            'hint_number': attempt.hints_used,
        }

    @classmethod
    def get_session_status(cls, session_id: str) -> dict:
        """
        2026-03-02: Get current status of a math session.

        Args:
            session_id: UUID string of the MathSession.

        Returns:
            dict: {success, session_id, status, problems_correct, total_problems, star_rating}
        """
        try:
            session = MathSession.objects.get(id=session_id)  # 2026-03-02: Lookup
        except MathSession.DoesNotExist:  # 2026-03-02: Not found
            return {'success': False, 'error': 'Session not found.'}

        return {  # 2026-03-02: Status response
            'success': True,
            'session_id': str(session.id),
            'lesson_id': session.lesson.lesson_id,
            'day_number': session.day_number,
            'iq_level': session.iq_level,
            'status': session.status,
            'problems_correct': session.problems_correct,
            'total_problems': session.total_problems,
            'star_rating': session.star_rating,
            'started_at': session.started_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
        }

    @classmethod
    def get_progress(cls, student) -> dict:
        """
        2026-03-02: Aggregate math progress for a student.

        Returns per-class summary: sessions completed, total stars,
        and topics attempted.

        Args:
            student: Student model instance.

        Returns:
            dict: {success, total_sessions, total_stars, by_class: {...}}
        """
        sessions = MathSession.objects.filter(  # 2026-03-02: All completed sessions
            student=student, status='completed'
        ).select_related('lesson')

        by_class = {}  # 2026-03-02: Per-class summary
        total_stars = 0  # 2026-03-02: Running total
        total_sessions = 0  # 2026-03-02: Running count

        for session in sessions:  # 2026-03-02: Iterate
            grade = session.lesson.class_number  # 2026-03-02: Grade
            if grade not in by_class:  # 2026-03-02: Init entry
                by_class[grade] = {
                    'sessions_completed': 0,
                    'total_stars': 0,
                    'topics': [],
                }
            by_class[grade]['sessions_completed'] += 1  # 2026-03-02: Increment
            stars = session.star_rating or 0  # 2026-03-02: Null-safe
            by_class[grade]['total_stars'] += stars  # 2026-03-02: Add stars
            topic = session.lesson.topic  # 2026-03-02: Topic
            if topic not in by_class[grade]['topics']:  # 2026-03-02: Unique topics
                by_class[grade]['topics'].append(topic)

            total_stars += stars  # 2026-03-02: Running total
            total_sessions += 1  # 2026-03-02: Running count

        return {  # 2026-03-02: Progress response
            'success': True,
            'total_sessions': total_sessions,
            'total_stars': total_stars,
            'by_class': by_class,
        }

    @staticmethod
    def _sanitise_problem(problem: dict) -> dict:
        """
        2026-03-02: Return a safe problem dict for the client (no worked solution).

        Removes worked_solution to prevent answer leaking to the frontend.
        Keeps: id, type, question, options (for MCQ), hint placeholder.

        Args:
            problem: Full problem dict from JSON.

        Returns:
            dict: Client-safe problem dict.
        """
        return {  # 2026-03-02: Safe subset
            'id': problem.get('id'),
            'type': problem.get('type'),
            'question': problem.get('question'),
            'options': problem.get('options'),  # 2026-03-02: None for non-MCQ
        }
