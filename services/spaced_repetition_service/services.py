"""
2026-02-27: Business logic for Spaced Repetition Service (BS-SPC).

Implements Leitner box system for spaced review scheduling and
pacing records for the intensive learning phase.
"""

import logging  # 2026-02-27: Structured logging
from datetime import date, timedelta  # 2026-02-27: Date arithmetic

from django.utils import timezone  # 2026-02-27: Timezone-aware now()

from services.auth_service.models import Student  # 2026-02-27: Student model
from services.teaching_engine.models import ConceptMastery, TeachingLesson  # 2026-02-27: Teaching models
from .models import (
    SpacedRepetitionRecord, ReviewSession, ReviewResponse, PacingRecord,
)

logger = logging.getLogger(__name__)

# 2026-02-27: Leitner box intervals in days per star level
# Key = star rating, Value = list of intervals for boxes 1, 2, 3, 4 (box 5 = maintenance)
LEITNER_INTERVALS = {
    5: [14, 30, 60, 120],
    4: [7, 14, 30, 60],
    3: [3, 7, 14, 30],
}
DEFAULT_RESET_DAYS = 3  # 2026-02-27: Days when box resets to 1 on failure

# 2026-02-27: IQ level adjustment multipliers for daily target
IQ_MULTIPLIERS = {
    'foundation': 0.7,
    'standard': 1.0,
    'advanced': 1.3,
}


class SpacedRepetitionService:
    """2026-02-27: Leitner box spaced repetition scheduling service."""

    @classmethod
    def schedule_first_review(cls, student, mastery):
        """
        2026-02-27: Schedule first review when a concept is first mastered.

        Called by teaching_engine after first-time mastery. Creates a
        SpacedRepetitionRecord with box=1 and next_review_date computed
        from the mastery's best_star_rating.

        Args:
            student: Student model instance.
            mastery: ConceptMastery model instance.

        Returns:
            SpacedRepetitionRecord: Newly created (or existing) record.
        """
        # 2026-02-27: Idempotent — skip if record already exists
        existing = SpacedRepetitionRecord.objects.filter(
            student=student, mastery=mastery
        ).first()
        if existing:
            return existing

        stars = mastery.best_star_rating  # 2026-02-27: Use current best rating
        # 2026-02-27: Default to 3-star intervals if star level not in map
        intervals = LEITNER_INTERVALS.get(stars, LEITNER_INTERVALS[3])
        days_until_review = intervals[0]  # 2026-02-27: Box 1 interval
        next_review = date.today() + timedelta(days=days_until_review)

        record = SpacedRepetitionRecord.objects.create(
            student=student,
            mastery=mastery,
            box=1,
            next_review_date=next_review,
        )
        logger.info(
            "SPC: Scheduled first review for student %s mastery %s on %s "
            "(box 1, %d stars)",
            student.id, mastery.id, next_review, stars,
        )
        return record

    @classmethod
    def get_review_queue(cls, student, as_of_date=None):
        """
        2026-02-27: Get today's review queue for a student.

        Returns up to 10 records due for review. Overdue items first,
        then by lowest best_star_rating. Aims for 70% scheduled +
        30% from different subjects for interleaving variety.

        Args:
            student: Student model instance.
            as_of_date: date to check against (defaults to today).

        Returns:
            list[dict]: Review items with mastery and lesson details.
        """
        if as_of_date is None:
            as_of_date = date.today()

        # 2026-02-27: Fetch all due records ordered overdue-first, lowest-stars-first
        due_records = SpacedRepetitionRecord.objects.filter(
            student=student,
            next_review_date__lte=as_of_date,
        ).select_related(
            'mastery', 'mastery__lesson', 'mastery__student'
        ).order_by(
            'next_review_date',  # 2026-02-27: Overdue first
            'mastery__best_star_rating',  # 2026-02-27: Lowest stars first
        )[:10]

        result = []
        for record in due_records:
            mastery = record.mastery
            lesson = mastery.lesson
            result.append({
                'record_id': str(record.id),
                'mastery_id': str(mastery.id),
                'lesson_id': lesson.lesson_id,
                'lesson_subject': lesson.subject,
                'day_number': mastery.day_number,
                'best_star_rating': mastery.best_star_rating,
                'box': record.box,
                'next_review_date': record.next_review_date.isoformat(),
                'review_count': record.review_count,
                'phase': record.phase,
            })

        return result

    @classmethod
    def complete_review(cls, student, mastery_id, stars, explanation_seconds):
        """
        2026-02-27: Complete a review for one concept.

        Validates explanation time, advances or resets Leitner box,
        creates ReviewResponse, and returns outcome.

        Args:
            student: Student model instance.
            mastery_id: UUID of ConceptMastery (may be UUID instance or str).
            stars: int 0-5 star rating for the review.
            explanation_seconds: int seconds spent explaining (must be >= 30).

        Returns:
            dict: {'success': bool, 'outcome': 'advanced'|'reset', ...}
        """
        if explanation_seconds < 30:  # 2026-02-27: Minimum explanation time
            return {
                'success': False,
                'error': 'Explanation must be at least 30 seconds.',
                'code': 'EXPLANATION_TOO_SHORT',
            }

        try:
            mastery = ConceptMastery.objects.get(id=mastery_id, student=student)
        except ConceptMastery.DoesNotExist:
            return {
                'success': False,
                'error': 'Concept mastery record not found.',
                'code': 'MASTERY_NOT_FOUND',
            }

        record = SpacedRepetitionRecord.objects.filter(
            student=student, mastery=mastery
        ).first()

        if not record:
            return {
                'success': False,
                'error': 'No review record found for this concept.',
                'code': 'RECORD_NOT_FOUND',
            }

        # 2026-02-27: Clamp stars to valid range
        stars = max(0, min(5, int(stars)))
        outcome = 'advanced' if stars >= 3 else 'reset'

        if outcome == 'advanced':
            # 2026-02-27: Advance box (capped at 5)
            record.box = min(5, record.box + 1)
            intervals = LEITNER_INTERVALS.get(stars, LEITNER_INTERVALS[3])
            box_index = min(record.box - 1, len(intervals) - 1)
            days_forward = intervals[box_index]

            if stars == 5:
                record.consecutive_5star_reviews += 1  # 2026-02-27: Track 5-star streak
                if record.consecutive_5star_reviews >= 3:
                    record.phase = 'maintenance'  # 2026-02-27: Transition to maintenance
            else:
                record.consecutive_5star_reviews = 0  # 2026-02-27: Reset streak on non-5-star
        else:
            # 2026-02-27: Reset to box 1 on poor performance
            record.box = 1
            days_forward = DEFAULT_RESET_DAYS
            record.consecutive_5star_reviews = 0
            record.phase = 'spaced_repetition'

        record.next_review_date = date.today() + timedelta(days=days_forward)
        record.last_reviewed_at = timezone.now()
        record.review_count += 1
        record.save()

        # 2026-02-27: Reuse today's in-progress session or create a new one
        session = ReviewSession.objects.filter(
            student=student, status='in_progress'
        ).first()
        if not session:
            session = ReviewSession.objects.create(student=student)

        session.concepts_reviewed += 1
        session.save()

        # 2026-02-27: Record the individual response
        ReviewResponse.objects.create(
            session=session,
            mastery=mastery,
            stars_awarded=stars,
            explanation_seconds=explanation_seconds,
            outcome=outcome,
        )

        logger.info(
            "SPC: Review complete for student %s mastery %s — "
            "%s (box %d, next %s)",
            student.id, mastery.id, outcome, record.box,
            record.next_review_date,
        )

        return {
            'success': True,
            'outcome': outcome,
            'new_box': record.box,
            'next_review_date': record.next_review_date.isoformat(),
            'phase': record.phase,
            'review_count': record.review_count,
        }


class PacingService:
    """2026-02-27: Intensive phase pacing analytics service."""

    @classmethod
    def get_or_create_pacing(cls, student):
        """
        2026-02-27: Get or create a pacing record for a student.

        Computes total_concepts from published TeachingLesson count × 4
        for the student's grade. IQ multiplier adjusts daily_target.

        Args:
            student: Student model instance.

        Returns:
            PacingRecord: The student's pacing record.
        """
        record = PacingRecord.objects.filter(student=student).first()
        if record:
            return record

        # 2026-02-27: Compute academic year start (June 1 of current or previous year)
        today = date.today()
        year = today.year if today.month >= 6 else today.year - 1
        academic_year_start = date(year, 6, 1)
        intensive_end_date = academic_year_start + timedelta(days=112)

        # 2026-02-27: Total concepts = published lessons × 4 days for this grade
        # Note: TeachingLesson uses class_number (not grade) to store the grade level
        published_count = TeachingLesson.objects.filter(
            class_number=student.grade, status='published'
        ).count()
        total_concepts = published_count * 4

        # 2026-02-27: IQ-adjusted daily target from diagnostic result
        from services.diagnostic_service.models import DiagnosticResult  # 2026-02-27: Late import
        iq_result = DiagnosticResult.objects.filter(student=student).first()
        iq_level = iq_result.overall_level if iq_result else 'standard'
        iq_factor = IQ_MULTIPLIERS.get(iq_level, 1.0)

        # 2026-02-27: Base daily target: spread total over 112 intensive days
        days_total = 112
        base_target = max(1, round(total_concepts / days_total))
        adjusted_target = max(1, round(base_target * iq_factor))

        record = PacingRecord.objects.create(
            student=student,
            academic_year_start=academic_year_start,
            intensive_end_date=intensive_end_date,
            total_concepts=total_concepts,
            daily_target=adjusted_target,
            iq_adjustment_factor=iq_factor,
        )
        logger.info(
            "SPC: Created pacing record for student %s — "
            "%d concepts, %d/day (IQ factor %.1f)",
            student.id, total_concepts, adjusted_target, iq_factor,
        )
        return record

    @classmethod
    def get_pacing_status(cls, student):
        """
        2026-02-27: Compute current pacing status for a student.

        Returns completed/remaining concept counts, pace status
        (on_track/ahead/behind), weekly velocity, and projected
        completion date.

        Args:
            student: Student model instance.

        Returns:
            dict: Pacing status with all metrics.
        """
        record = cls.get_or_create_pacing(student)
        today = date.today()

        # 2026-02-27: Use denormalized completed_concepts from pacing record
        completed_concepts = record.completed_concepts
        remaining_concepts = max(0, record.total_concepts - completed_concepts)

        # 2026-02-27: Days elapsed since academic year start
        days_elapsed = max(0, (today - record.academic_year_start).days)
        expected_by_now = min(
            record.total_concepts,
            days_elapsed * record.daily_target,
        )

        # 2026-02-27: Pace status — within one day's target is "on_track"
        if completed_concepts >= expected_by_now + record.daily_target:
            pace_status = 'ahead'
        elif completed_concepts >= expected_by_now - record.daily_target:
            pace_status = 'on_track'
        else:
            pace_status = 'behind'

        # 2026-02-27: Weekly velocity (last 7 days, counted from ConceptMastery for real-time data)
        week_ago = today - timedelta(days=7)
        weekly_velocity = ConceptMastery.objects.filter(
            student=student,
            is_mastered=True,
            updated_at__date__gte=week_ago,
        ).count()

        # 2026-02-27: Projected completion date based on current velocity
        effective_daily = (
            weekly_velocity / 7.0 if weekly_velocity > 0 else float(record.daily_target)
        )
        effective_daily = max(effective_daily, 1.0)  # 2026-02-27: Guard against zero
        days_to_complete = int(remaining_concepts / effective_daily)
        projected_date = today + timedelta(days=days_to_complete)

        return {
            'phase': record.phase,
            'academic_year_start': record.academic_year_start.isoformat(),
            'intensive_end_date': record.intensive_end_date.isoformat(),
            'total_concepts': record.total_concepts,
            'completed_concepts': completed_concepts,
            'expected_concepts': expected_by_now,  # 2026-02-27: Expected count to date
            'remaining_concepts': remaining_concepts,
            'daily_target': record.daily_target,
            'iq_adjustment_factor': record.iq_adjustment_factor,
            'pace_status': pace_status,
            'weekly_velocity': weekly_velocity,
            'projected_completion_date': projected_date.isoformat(),
        }
