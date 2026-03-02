"""
2026-02-20: Vocabulary Acquisition System business logic (BS-LNG).

Purpose:
    VocabularyService: Provides get_today_session, record_pronunciation,
    record_mcq, complete_session, and get_progress. Delegates LLM content
    generation to content_generator and language validation to the
    read_along_service language_registry.
"""

import logging  # 2026-02-20: Module logger
from datetime import date  # 2026-02-20: Session date (today)
from statistics import mean  # 2026-02-20: Mean score computation

from django.utils import timezone  # 2026-02-20: Timezone-aware timestamps
from rest_framework.exceptions import (  # 2026-02-20: DRF exceptions
    NotFound, ValidationError, PermissionDenied
)

from services.read_along_service.language_registry import (  # 2026-02-20: DB helpers
    get_language, is_valid_language, get_student_languages
)
from services.read_along_service.models import STAR_THRESHOLDS  # 2026-02-20: Reuse thresholds

from .models import (  # 2026-02-20: Vocabulary models
    VocabularyWord, StudentWordProgress, VocabularySession, SessionWord
)
from .content_generator import get_word_content  # 2026-02-20: LLM content

logger = logging.getLogger(__name__)  # 2026-02-20: Module logger


class VocabularyService:
    """2026-02-20: Core Vocabulary Acquisition System service (BS-LNG)."""

    @staticmethod
    def _score_to_stars(score: float) -> int:
        """
        2026-02-20: Map a 0.0-1.0 fluency score to 0-5 stars.

        Reuses STAR_THRESHOLDS from read_along_service.
        Thresholds: 0=<0.40, 1=<0.55, 2=<0.70, 3=<0.82, 4=<0.92, 5=≥0.92.

        Args:
            score: Float between 0.0 and 1.0.

        Returns:
            int: Star rating 0-5.
        """
        for stars, threshold in enumerate(STAR_THRESHOLDS):  # 2026-02-20: Walk thresholds
            if score < threshold:
                return stars  # 2026-02-20: First threshold exceeded
        return 5  # 2026-02-20: score >= 0.92 → 5 stars

    @staticmethod
    def get_today_session(student, language_name: str) -> dict:
        """
        2026-02-20: Get or create today's vocabulary session for a student.

        Idempotent: calling twice on the same day returns the same session.
        Selects 10 next unmastered words for the student's grade/language,
        fills the LLM content cache, and returns full session data.

        Args:
            student: Student model instance.
            language_name: Language name e.g. 'Hindi'.

        Returns:
            dict: session_id, language, bcp47_tag, grade, session_date,
                  status, student_languages, words[].

        Raises:
            ValidationError: If language_name is not active in DB.
        """
        # 2026-02-20: Validate language
        if not is_valid_language(language_name):
            raise ValidationError({'language': f"'{language_name}' is not an active language."})

        language = get_language(language_name)  # 2026-02-20: Fetch Language object
        today = date.today()  # 2026-02-20: Calendar date for idempotency

        # 2026-02-20: Check for existing session today
        existing = VocabularySession.objects.filter(
            student=student,
            language=language,
            session_date=today,
        ).first()

        if existing:
            # 2026-02-20: Return existing session — idempotent
            return VocabularyService._serialize_session(existing, student)

        # 2026-02-20: Select 10 next unmastered words for student's grade
        mastered_word_ids = StudentWordProgress.objects.filter(
            student=student,
            word__language=language,
            word__grade=student.grade,
            status='mastered',
        ).values_list('word_id', flat=True)

        words = (
            VocabularyWord.objects
            .filter(language=language, grade=student.grade)
            .exclude(id__in=mastered_word_ids)
            .order_by('frequency_rank')[:10]
        )
        words = list(words)  # 2026-02-20: Evaluate queryset

        if not words:
            # 2026-02-20: All words mastered or none seeded — return empty session
            words = []

        # 2026-02-20: Determine mother tongue for LLM content
        try:
            mother_tongue = get_language(student.language_1)  # 2026-02-20: Student's native language
        except Exception:
            try:
                mother_tongue = get_language('English')  # 2026-02-20: Fallback to English
            except Exception:
                mother_tongue = language  # 2026-02-20: Last resort: same language

        # 2026-02-20: Pre-populate LLM content cache for each word
        word_contents = {}
        for word in words:
            try:
                content = get_word_content(word, mother_tongue)
                word_contents[str(word.id)] = content
            except Exception as exc:  # 2026-02-20: Never block session on LLM error
                logger.warning("get_word_content failed for %s: %s", word.word, exc)
                word_contents[str(word.id)] = {
                    'definition': f"(Definition for '{word.word}')",
                    'example_sentence': word.word,
                    'example_translation': word.word,
                    'mnemonic': '',
                    'llm_error': True,
                }

        # 2026-02-20: Create session and session words
        session = VocabularySession.objects.create(
            student=student,
            language=language,
            grade=student.grade,
            session_date=today,
            status='in_progress',
        )

        for idx, word in enumerate(words, start=1):
            SessionWord.objects.create(
                session=session,
                word=word,
                word_order=idx,
            )

        # 2026-02-20: Get student's active languages list
        student_languages = get_student_languages(student)

        logger.info(  # 2026-02-20: Audit log
            "VocabularySession created: student=%s language=%s grade=%d words=%d",
            student.id, language_name, student.grade, len(words),
        )

        return VocabularyService._serialize_session(session, student, word_contents)

    @staticmethod
    def _serialize_session(session: VocabularySession, student, word_contents: dict = None) -> dict:
        """
        2026-02-20: Serialize a VocabularySession to API response format.

        Args:
            session: VocabularySession instance.
            student: Student instance.
            word_contents: Optional pre-computed content dict keyed by word_id str.

        Returns:
            dict: Full session payload.
        """
        student_languages = get_student_languages(student)  # 2026-02-20: Active languages

        # 2026-02-20: Fetch session words in order
        session_words = session.session_words.select_related(
            'word', 'word__language'
        ).order_by('word_order')

        # 2026-02-20: Determine mother tongue for content lookup
        try:
            mother_tongue = get_language(student.language_1)
        except Exception:
            try:
                mother_tongue = get_language('English')
            except Exception:
                mother_tongue = session.language

        words_data = []
        for sw in session_words:
            word = sw.word

            # 2026-02-20: Get content from pre-computed dict or load from cache
            if word_contents and str(word.id) in word_contents:
                content = word_contents[str(word.id)]
            else:
                try:
                    content = get_word_content(word, mother_tongue)
                except Exception:
                    content = {
                        'definition': f"(Definition for '{word.word}')",
                        'example_sentence': word.word,
                        'example_translation': word.word,
                        'mnemonic': '',
                        'llm_error': True,
                    }

            words_data.append({
                'word_id': str(word.id),
                'word': word.word,
                'romanization': word.romanization,
                'word_type': word.word_type,
                'bcp47_tag': session.language.bcp47_tag,
                'definition': content['definition'],
                'example_sentence': content['example_sentence'],
                'example_translation': content['example_translation'],
                'mnemonic': content['mnemonic'],
                'image_keyword': word.image_keyword,
                'word_order': sw.word_order,
            })

        return {
            'session_id': str(session.id),
            'language': session.language.name,
            'bcp47_tag': session.language.bcp47_tag,
            'grade': session.grade,
            'session_date': str(session.session_date),
            'status': session.status,
            'student_languages': student_languages,
            'words': words_data,
        }

    @staticmethod
    def record_pronunciation(session_id: str, word_id: str, score: float, student) -> dict:
        """
        2026-02-20: Record a pronunciation score for a word in a session.

        Updates SessionWord.pronunciation_score and StudentWordProgress.

        Args:
            session_id: UUID string of VocabularySession.
            word_id: UUID string of VocabularyWord.
            score: Float 0.0-1.0 from Levenshtein similarity or self-rating.
            student: Student model instance.

        Returns:
            dict: word_id, pronunciation_score, progress_status.

        Raises:
            NotFound: If session or word not found.
            PermissionDenied: If session belongs to a different student.
            ValidationError: If session not in_progress or score out of range.
        """
        # 2026-02-20: Fetch and validate session ownership
        try:
            session = VocabularySession.objects.get(id=session_id)
        except VocabularySession.DoesNotExist:
            raise NotFound(f"Session '{session_id}' not found.")

        if session.student_id != student.id:
            raise PermissionDenied("You may only update your own sessions.")

        if session.status != 'in_progress':
            raise ValidationError({'session': 'Session is not in progress.'})

        # 2026-02-20: Validate score range
        if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
            raise ValidationError({'score': 'Score must be a float between 0.0 and 1.0.'})

        score = float(score)  # 2026-02-20: Normalize to float

        # 2026-02-20: Find the session word
        try:
            session_word = SessionWord.objects.get(session=session, word_id=word_id)
        except SessionWord.DoesNotExist:
            raise NotFound(f"Word '{word_id}' not found in session '{session_id}'.")

        # 2026-02-20: Update session word
        session_word.pronunciation_score = score
        session_word.save(update_fields=['pronunciation_score', 'updated_at'])

        # 2026-02-20: Update StudentWordProgress
        progress, _ = StudentWordProgress.objects.get_or_create(
            student=student,
            word=session_word.word,
            defaults={'status': 'unseen'},
        )
        progress.exposure_count += 1  # 2026-02-20: Increment exposure
        progress.last_seen_at = timezone.now()

        # 2026-02-20: Update best score
        if score > progress.best_pronunciation_score:
            progress.best_pronunciation_score = score

        # 2026-02-20: Advance status: unseen → introduced (on first pronunciation)
        if progress.status == 'unseen':
            progress.status = 'introduced'

        progress.save(update_fields=[
            'exposure_count', 'last_seen_at', 'best_pronunciation_score',
            'status', 'updated_at',
        ])

        return {
            'word_id': str(session_word.word_id),
            'pronunciation_score': score,
            'progress_status': progress.status,
        }

    @staticmethod
    def record_mcq(session_id: str, word_id: str, correct: bool, student) -> dict:
        """
        2026-02-20: Record a MCQ answer for a word in a session.

        Updates SessionWord.mcq_answered/mcq_correct and StudentWordProgress.

        Args:
            session_id: UUID string of VocabularySession.
            word_id: UUID string of VocabularyWord.
            correct: Whether the MCQ answer was correct.
            student: Student model instance.

        Returns:
            dict: word_id, mcq_correct, progress_status.

        Raises:
            NotFound: If session or word not found.
            PermissionDenied: If session belongs to a different student.
            ValidationError: If session not in_progress.
        """
        # 2026-02-20: Fetch and validate session
        try:
            session = VocabularySession.objects.get(id=session_id)
        except VocabularySession.DoesNotExist:
            raise NotFound(f"Session '{session_id}' not found.")

        if session.student_id != student.id:
            raise PermissionDenied("You may only update your own sessions.")

        if session.status != 'in_progress':
            raise ValidationError({'session': 'Session is not in progress.'})

        # 2026-02-20: Find the session word
        try:
            session_word = SessionWord.objects.get(session=session, word_id=word_id)
        except SessionWord.DoesNotExist:
            raise NotFound(f"Word '{word_id}' not found in session '{session_id}'.")

        # 2026-02-20: Update MCQ flags
        session_word.mcq_answered = True
        session_word.mcq_correct = bool(correct)
        session_word.save(update_fields=['mcq_answered', 'mcq_correct', 'updated_at'])

        # 2026-02-20: Update StudentWordProgress MCQ count
        progress, _ = StudentWordProgress.objects.get_or_create(
            student=student,
            word=session_word.word,
            defaults={'status': 'unseen'},
        )
        if correct:
            progress.mcq_correct_count += 1
        progress.last_seen_at = timezone.now()
        progress.save(update_fields=['mcq_correct_count', 'last_seen_at', 'updated_at'])

        return {
            'word_id': str(session_word.word_id),
            'mcq_correct': bool(correct),
            'progress_status': progress.status,
        }

    @staticmethod
    def complete_session(session_id: str, student) -> dict:
        """
        2026-02-20: Mark a vocabulary session as completed and compute stars.

        Calculates fluency score from pronunciation + MCQ performance,
        maps to 0-5 stars, updates word mastery levels.

        Fluency formula:
            avg_pronunciation = mean(non-null pronunciation_scores) or 0.0
            mcq_pct = correct_count / max(1, answered_count)
            fluency_score = (avg_pronunciation × 0.60) + (mcq_pct × 0.40)

        Mastery rules (in priority order):
            - mcq_correct AND best_pronunciation_score >= 0.70 → mastered
            - mcq_answered OR pronunciation scored → practicing (if not mastered)
            - exposure_count > 0 → introduced (if was unseen)
            - Never regress from mastered

        Args:
            session_id: UUID string of VocabularySession.
            student: Student model instance.

        Returns:
            dict: session_id, fluency_star_rating, fluency_score,
                  avg_pronunciation, mcq_pct, words_introduced, words_mastered.

        Raises:
            NotFound: If session not found.
            PermissionDenied: If session belongs to a different student.
            ValidationError: If session already completed.
        """
        # 2026-02-20: Fetch and validate session
        try:
            session = VocabularySession.objects.get(id=session_id)
        except VocabularySession.DoesNotExist:
            raise NotFound(f"Session '{session_id}' not found.")

        if session.student_id != student.id:
            raise PermissionDenied("You may only complete your own sessions.")

        if session.status != 'in_progress':
            raise ValidationError({'session': 'Session is already completed.'})

        # 2026-02-20: Fetch all session words
        session_words = list(session.session_words.select_related('word').all())

        # 2026-02-20: Compute avg_pronunciation (non-null scores only)
        pron_scores = [sw.pronunciation_score for sw in session_words if sw.pronunciation_score is not None]
        avg_pronunciation = mean(pron_scores) if pron_scores else 0.0

        # 2026-02-20: Compute MCQ percentage
        answered_count = sum(1 for sw in session_words if sw.mcq_answered)
        correct_count = sum(1 for sw in session_words if sw.mcq_correct)
        mcq_pct = correct_count / max(1, answered_count) if answered_count > 0 else 0.0

        # 2026-02-20: Compute fluency score and star rating
        fluency_score = (avg_pronunciation * 0.60) + (mcq_pct * 0.40)
        star_rating = VocabularyService._score_to_stars(fluency_score)

        # 2026-02-20: Update word mastery per session word
        words_introduced = 0
        words_mastered = 0

        for sw in session_words:
            progress, created = StudentWordProgress.objects.get_or_create(
                student=student,
                word=sw.word,
                defaults={'status': 'unseen'},
            )

            old_status = progress.status  # 2026-02-20: Remember old status

            # 2026-02-20: Update pronunciation best score if scored
            if sw.pronunciation_score is not None:
                if sw.pronunciation_score > progress.best_pronunciation_score:
                    progress.best_pronunciation_score = sw.pronunciation_score

            # 2026-02-20: Apply mastery rules (highest priority first, never regress)
            if old_status != 'mastered':
                if sw.mcq_correct and progress.best_pronunciation_score >= 0.70:
                    progress.status = 'mastered'
                elif sw.mcq_answered or sw.pronunciation_score is not None:
                    progress.status = 'practicing'
                elif progress.exposure_count > 0 and old_status == 'unseen':
                    progress.status = 'introduced'

            # 2026-02-20: Increment exposure count
            progress.exposure_count += 1
            progress.last_seen_at = timezone.now()

            progress.save(update_fields=[
                'status', 'best_pronunciation_score', 'exposure_count',
                'last_seen_at', 'updated_at',
            ])

            # 2026-02-20: Count transitions
            if progress.status == 'mastered' and old_status != 'mastered':
                words_mastered += 1
            elif progress.status in ('introduced', 'practicing') and old_status == 'unseen':
                words_introduced += 1

        # 2026-02-20: Mark session completed
        session.status = 'completed'
        session.fluency_star_rating = star_rating
        session.completed_at = timezone.now()
        session.save(update_fields=[
            'status', 'fluency_star_rating', 'completed_at', 'updated_at'
        ])

        logger.info(  # 2026-02-20: Audit log
            "VocabularySession completed: student=%s session=%s stars=%d fluency=%.3f",
            student.id, session_id, star_rating, fluency_score,
        )

        return {
            'session_id': str(session.id),
            'fluency_star_rating': star_rating,
            'fluency_score': round(fluency_score, 4),
            'avg_pronunciation': round(avg_pronunciation, 4),
            'mcq_pct': round(mcq_pct, 4),
            'words_introduced': words_introduced,
            'words_mastered': words_mastered,
        }

    @staticmethod
    def get_progress(student, language_name: str) -> dict:
        """
        2026-02-20: Get overall vocabulary progress for a student in a language.

        Counts words by status, computes current daily streak, and flags
        whether today's session is already completed.

        Args:
            student: Student model instance.
            language_name: Language name e.g. 'Hindi'.

        Returns:
            dict: introduced_count, mastered_count, current_streak,
                  today_completed, grade_breakdown.

        Raises:
            ValidationError: If language_name is not active in DB.
        """
        # 2026-02-20: Validate language
        if not is_valid_language(language_name):
            raise ValidationError({'language': f"'{language_name}' is not an active language."})

        language = get_language(language_name)

        # 2026-02-20: Count words by status for this student + language
        all_progress = StudentWordProgress.objects.filter(
            student=student,
            word__language=language,
        ).values_list('status', flat=True)

        status_counts = {'unseen': 0, 'introduced': 0, 'practicing': 0, 'mastered': 0}
        for status in all_progress:
            status_counts[status] = status_counts.get(status, 0) + 1

        # 2026-02-20: Compute daily streak (consecutive completed days)
        completed_dates = set(
            VocabularySession.objects.filter(
                student=student,
                language=language,
                status='completed',
            ).values_list('session_date', flat=True)
        )

        streak = 0
        check_date = date.today()
        while check_date in completed_dates:
            streak += 1
            from datetime import timedelta  # 2026-02-20: Local import
            check_date = check_date - timedelta(days=1)

        # 2026-02-20: Check if today's session is completed
        today_session = VocabularySession.objects.filter(
            student=student,
            language=language,
            session_date=date.today(),
            status='completed',
        ).exists()

        return {
            'language': language_name,
            'introduced_count': status_counts['introduced'] + status_counts['practicing'],
            'mastered_count': status_counts['mastered'],
            'current_streak': streak,
            'today_completed': today_session,
            'grade_breakdown': {
                'grade': student.grade,
                'introduced': status_counts['introduced'],
                'practicing': status_counts['practicing'],
                'mastered': status_counts['mastered'],
            },
        }
