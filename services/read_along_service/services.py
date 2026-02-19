"""
2026-02-19: Read-Along & Mimic Engine business logic (BS-RAM).

Purpose:
    ReadAlongService: Provides get_content, submit_session, get_history
    and the pure _score_to_stars helper. Delegates content loading to
    TeachingContentLoader and language validation to language_registry.
"""

import logging  # 2026-02-19: Module logger
from statistics import mean  # 2026-02-19: Mean for overall_score calculation

from django.utils import timezone  # 2026-02-19: Timezone-aware timestamps
from rest_framework.exceptions import (  # 2026-02-19: DRF exceptions
    NotFound, ValidationError
)

from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-02-19: Content
from services.teaching_engine.models import TeachingLesson  # 2026-02-19: Lesson model
from .language_registry import (  # 2026-02-19: DB helpers
    get_language, is_valid_language, get_student_languages
)
from .models import ReadAlongSession, STAR_THRESHOLDS  # 2026-02-19: Models

logger = logging.getLogger(__name__)  # 2026-02-19: Module logger


class ReadAlongService:
    """2026-02-19: Core Read-Along & Mimic Engine service."""

    @staticmethod
    def _score_to_stars(score: float) -> int:
        """
        2026-02-19: Map a 0.0-1.0 overall score to 0-5 stars.

        Thresholds: 0=<0.40, 1=<0.55, 2=<0.70, 3=<0.82, 4=<0.92, 5=≥0.92.

        Args:
            score: Float between 0.0 and 1.0.

        Returns:
            int: Star rating 0-5.
        """
        for stars, threshold in enumerate(STAR_THRESHOLDS):  # 2026-02-19: Check thresholds
            if score < threshold:
                return stars  # 2026-02-19: Return stars at first threshold exceeded
        return 5  # 2026-02-19: score >= 0.92 → 5 stars

    @staticmethod
    def get_content(student, lesson_id: str, day_number: int, language: str) -> dict:
        """
        2026-02-19: Get read-along content for a student, lesson day, and language.

        Loads the teaching JSON via TeachingContentLoader, extracts the
        read_along block for the requested language, and returns sentences,
        transliterations, TTS config, and the student's previous best result.

        Args:
            student: Student model instance.
            lesson_id: UUID string of the TeachingLesson.
            day_number: Day within the lesson (1-4).
            language: Language name, e.g. 'Telugu'.

        Returns:
            dict: sentences, transliterations, bcp47_tag, tts_rate,
                  student_languages, previous_best.

        Raises:
            NotFound: If lesson or day not found in content JSON.
            ValidationError: If language is not active in DB.
        """
        # 2026-02-19: Validate language against DB
        if not is_valid_language(language):
            raise ValidationError({'language': f"'{language}' is not an active language."})

        # 2026-02-19: Load lesson from DB
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)
        except TeachingLesson.DoesNotExist:
            raise NotFound(f"Lesson '{lesson_id}' not found.")

        # 2026-02-19: Load content JSON
        try:
            lesson_data = TeachingContentLoader.load_lesson(lesson.content_json_path)
        except FileNotFoundError:
            raise NotFound("Lesson content file not found.")

        # 2026-02-19: Find the day block
        day_block = None
        for day in lesson_data.get('micro_lessons', []):
            if day.get('day') == day_number:
                day_block = day
                break

        if day_block is None:
            raise NotFound(f"Day {day_number} not found in lesson content.")

        # 2026-02-19: Extract read_along section
        read_along = day_block.get('read_along', {})
        lang_content = read_along.get(language, {})

        if not lang_content:
            raise ValidationError(
                {'language': f"No read-along content for '{language}' on day {day_number}."}
            )

        # 2026-02-19: Get language metadata from DB
        lang_obj = get_language(language)

        # 2026-02-19: Get student's assigned languages
        student_languages = get_student_languages(student)

        # 2026-02-19: Get previous best session for this combo
        previous_best = None
        best_session = (
            ReadAlongSession.objects
            .filter(
                student=student,
                lesson=lesson,
                day_number=day_number,
                language=language,
                status='completed',
            )
            .order_by('-star_rating', '-overall_score')
            .first()
        )
        if best_session:
            previous_best = {
                'star_rating': best_session.star_rating,
                'overall_score': best_session.overall_score,
            }

        return {
            'sentences': lang_content.get('sentences', []),
            'transliterations': lang_content.get('transliterations', []),
            'bcp47_tag': lang_obj.bcp47_tag,
            'tts_rate': lang_obj.tts_rate,
            'student_languages': student_languages,
            'previous_best': previous_best,
        }

    @staticmethod
    def submit_session(
        student,
        lesson_id: str,
        day_number: int,
        language: str,
        sentence_scores: list,
        time_spent_seconds: int,
    ) -> dict:
        """
        2026-02-19: Record a completed read-along session.

        Computes overall_score = mean(sentence_scores), maps to star_rating,
        determines attempt_number, saves ReadAlongSession, and returns result.

        Args:
            student: Student model instance.
            lesson_id: UUID string of the TeachingLesson.
            day_number: Day within the lesson (1-4).
            language: Language name, e.g. 'Telugu'.
            sentence_scores: List of floats 0.0-1.0 (one per sentence).
            time_spent_seconds: Total time in seconds.

        Returns:
            dict: overall_score, star_rating, is_new_best, attempt_number.

        Raises:
            ValidationError: If language invalid or sentence_scores malformed.
            NotFound: If lesson not found.
        """
        # 2026-02-19: Validate language
        if not is_valid_language(language):
            raise ValidationError({'language': f"'{language}' is not an active language."})

        # 2026-02-19: Validate sentence_scores
        if not isinstance(sentence_scores, list) or len(sentence_scores) == 0:
            raise ValidationError({'sentence_scores': 'Must be a non-empty list of floats.'})
        for s in sentence_scores:
            if not isinstance(s, (int, float)) or not (0.0 <= float(s) <= 1.0):
                raise ValidationError(
                    {'sentence_scores': 'Each score must be a float between 0.0 and 1.0.'}
                )

        # 2026-02-19: Load lesson
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)
        except TeachingLesson.DoesNotExist:
            raise NotFound(f"Lesson '{lesson_id}' not found.")

        # 2026-02-19: Get language metadata
        lang_obj = get_language(language)

        # 2026-02-19: Compute overall score and star rating
        overall_score = mean(float(s) for s in sentence_scores)
        star_rating = ReadAlongService._score_to_stars(overall_score)

        # 2026-02-19: Determine attempt number (max existing + 1)
        last_attempt = (
            ReadAlongSession.objects
            .filter(student=student, lesson=lesson, day_number=day_number, language=language)
            .order_by('-attempt_number')
            .values_list('attempt_number', flat=True)
            .first()
        )
        attempt_number = (last_attempt or 0) + 1  # 2026-02-19: Increment

        # 2026-02-19: Determine is_new_best
        best_so_far = (
            ReadAlongSession.objects
            .filter(
                student=student,
                lesson=lesson,
                day_number=day_number,
                language=language,
                status='completed',
            )
            .order_by('-star_rating')
            .values_list('star_rating', flat=True)
            .first()
        )
        is_new_best = (best_so_far is None) or (star_rating > best_so_far)

        # 2026-02-19: Create session record
        session = ReadAlongSession.objects.create(
            student=student,
            lesson=lesson,
            day_number=day_number,
            language=language,
            bcp47_tag=lang_obj.bcp47_tag,
            sentence_scores=sentence_scores,
            overall_score=round(overall_score, 4),
            star_rating=star_rating,
            sentences_attempted=len(sentence_scores),
            sentences_total=len(sentence_scores),
            attempt_number=attempt_number,
            status='completed',
            time_spent_seconds=time_spent_seconds,
            completed_at=timezone.now(),
        )

        logger.info(  # 2026-02-19: Audit log
            "ReadAlongSession created: student=%s lesson=%s day=%d lang=%s stars=%d",
            student.id, lesson_id, day_number, language, star_rating,
        )

        return {
            'overall_score': round(overall_score, 4),
            'star_rating': star_rating,
            'is_new_best': is_new_best,
            'attempt_number': attempt_number,
        }

    @staticmethod
    def get_history(student, lesson_id: str, day_number: int, language: str) -> dict:
        """
        2026-02-19: Get last 5 completed sessions for a student/lesson/day/language.

        Args:
            student: Student model instance.
            lesson_id: UUID string of the TeachingLesson.
            day_number: Day within the lesson (1-4).
            language: Language name.

        Returns:
            dict: sessions list (last 5, newest first).

        Raises:
            NotFound: If lesson not found.
        """
        # 2026-02-19: Load lesson
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)
        except TeachingLesson.DoesNotExist:
            raise NotFound(f"Lesson '{lesson_id}' not found.")

        sessions = (
            ReadAlongSession.objects
            .filter(
                student=student,
                lesson=lesson,
                day_number=day_number,
                language=language,
            )
            .order_by('-created_at')[:5]  # 2026-02-19: Last 5
        )

        return {
            'sessions': [
                {
                    'id': str(s.id),
                    'attempt_number': s.attempt_number,
                    'overall_score': s.overall_score,
                    'star_rating': s.star_rating,
                    'sentences_attempted': s.sentences_attempted,
                    'sentences_total': s.sentences_total,
                    'time_spent_seconds': s.time_spent_seconds,
                    'status': s.status,
                    'created_at': s.created_at.isoformat(),
                }
                for s in sessions
            ]
        }
