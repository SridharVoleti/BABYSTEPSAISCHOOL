"""
2026-02-27: Leaderboard service for Gamification Engine (BS-GAM-005).

Implements weekly class and regional leaderboards with parental opt-in
consent enforcement and age gating for regional boards.
"""

import logging
from datetime import date, timedelta

from .models import StudentGameProfile, WeeklyLeaderboardSnapshot

logger = logging.getLogger(__name__)  # 2026-02-27: Module logger


class LeaderboardService:
    """
    2026-02-27: Weekly leaderboard service.

    Supports three board types:
    - personal: Student's own weekly star history (always accessible).
    - class: Top 20 from same grade this week (requires opt-in).
    - regional: Top 50 from all grades this week (requires opt-in + age >= 10).
    """

    @staticmethod
    def _current_week_start():
        """
        2026-02-27: Return the Monday date for the current week.

        Returns:
            date: Monday of the current ISO week.
        """
        today = date.today()
        return today - timedelta(days=today.weekday())  # 2026-02-27: Monday = weekday 0

    @classmethod
    def get_leaderboard(cls, board_type, student):
        """
        2026-02-27: Return a ranked leaderboard for the given board_type.

        Board types:
        - 'personal': last 8 weeks of this student's snapshots (always allowed).
        - 'class': top 20 students in the same grade this week (opt-in required).
        - 'regional': top 50 students all grades this week (opt-in + age >= 10).

        Args:
            board_type: str — 'personal', 'class', or 'regional'.
            student: Student model instance.

        Returns:
            dict: {'board_type': str, 'entries': list[dict], 'rank': int|None}
        """
        week_start = cls._current_week_start()

        if board_type == 'personal':
            return cls._personal_board(student, week_start)

        # 2026-02-27: Check opt-in consent for non-personal boards
        opted_in = cls._check_opt_in(student)
        if not opted_in:
            return {
                'success': False,
                'error': 'Parental opt-in required for leaderboard access.',
                'code': 'OPT_IN_REQUIRED',
            }

        if board_type == 'class':
            return cls._class_board(student, week_start)

        if board_type == 'regional':
            # 2026-02-27: Age gate — must be 10 or older
            student_age = cls._get_student_age(student)
            if student_age < 10:
                return {
                    'success': False,
                    'error': 'Regional leaderboard requires age 10 or above.',
                    'code': 'AGE_RESTRICTED',
                }
            return cls._regional_board(student, week_start)

        return {
            'success': False,
            'error': f"Unknown board type '{board_type}'.",
            'code': 'INVALID_BOARD_TYPE',
        }

    @classmethod
    def _check_opt_in(cls, student):
        """
        2026-02-27: Check if parent has opted student into leaderboards.

        Args:
            student: Student model instance.

        Returns:
            bool: True if leaderboard_opt_in is True, False otherwise.
        """
        from services.parent_dashboard.models import ParentalControls  # 2026-02-27: Lazy import
        controls = ParentalControls.objects.filter(student=student).first()
        if not controls:
            return False  # 2026-02-27: No controls = no opt-in
        return controls.leaderboard_opt_in

    @staticmethod
    def _get_student_age(student):
        """
        2026-02-27: Compute student age in years from dob.

        Args:
            student: Student model instance.

        Returns:
            int: Age in years.
        """
        today = date.today()
        dob = student.dob
        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )
        return age

    @classmethod
    def _personal_board(cls, student, week_start):
        """
        2026-02-27: Return student's own weekly star history (last 8 weeks).

        Args:
            student: Student model instance.
            week_start: date of current week's Monday.

        Returns:
            dict: Board response with entries list.
        """
        eight_weeks_ago = week_start - timedelta(weeks=7)  # 2026-02-27: Inclusive of current week = 8 weeks
        snapshots = WeeklyLeaderboardSnapshot.objects.filter(
            student=student,
            week_start__gte=eight_weeks_ago,
        ).order_by('-week_start')[:8]  # 2026-02-27: Cap at 8 entries

        entries = [
            {
                'week_start': snap.week_start.isoformat(),
                'stars_this_week': snap.stars_this_week,
                'display_name': snap.display_name,
                'grade': snap.grade,
            }
            for snap in snapshots
        ]

        return {
            'success': True,
            'board_type': 'personal',
            'entries': entries,
            'rank': None,  # 2026-02-27: Personal board has no rank
        }

    @classmethod
    def _class_board(cls, student, week_start):
        """
        2026-02-27: Return top 20 students in same grade this week.

        Args:
            student: Student model instance.
            week_start: date of current week's Monday.

        Returns:
            dict: Board response with ranked entries.
        """
        snapshots = WeeklyLeaderboardSnapshot.objects.filter(
            grade=student.grade,
            week_start=week_start,
        ).order_by('-stars_this_week')[:20]

        entries = []
        student_rank = None
        for rank, snap in enumerate(snapshots, start=1):
            entries.append({
                'rank': rank,
                'display_name': snap.display_name,
                'grade': snap.grade,
                'stars_this_week': snap.stars_this_week,
                'is_self': snap.student_id == student.id,
            })
            if snap.student_id == student.id:
                student_rank = rank

        return {
            'success': True,
            'board_type': 'class',
            'entries': entries,
            'rank': student_rank,
        }

    @classmethod
    def _regional_board(cls, student, week_start):
        """
        2026-02-27: Return top 50 students across all grades this week.

        Args:
            student: Student model instance.
            week_start: date of current week's Monday.

        Returns:
            dict: Board response with ranked entries.
        """
        snapshots = WeeklyLeaderboardSnapshot.objects.filter(
            week_start=week_start,
        ).order_by('-stars_this_week')[:50]

        entries = []
        student_rank = None
        for rank, snap in enumerate(snapshots, start=1):
            entries.append({
                'rank': rank,
                'display_name': snap.display_name,
                'grade': snap.grade,
                'stars_this_week': snap.stars_this_week,
                'is_self': snap.student_id == student.id,
            })
            if snap.student_id == student.id:
                student_rank = rank

        return {
            'success': True,
            'board_type': 'regional',
            'entries': entries,
            'rank': student_rank,
        }

    @classmethod
    def record_week_snapshot(cls, student, stars):
        """
        2026-02-27: Upsert a WeeklyLeaderboardSnapshot for the current week.

        Called from GamificationService.process_activity after stars are
        accumulated. Adds to existing snapshot if present, creates new one.

        Args:
            student: Student model instance.
            stars: int stars earned in this activity.
        """
        week_start = cls._current_week_start()
        snapshot, created = WeeklyLeaderboardSnapshot.objects.get_or_create(
            student=student,
            week_start=week_start,
            defaults={
                'grade': student.grade,
                'stars_this_week': stars,
                'display_name': student.full_name,
            },
        )
        if not created:
            # 2026-02-27: Accumulate stars in existing snapshot
            snapshot.stars_this_week += stars
            snapshot.save(update_fields=['stars_this_week'])

    @classmethod
    def reset_weekly_stars(cls):
        """
        2026-02-27: Reset weekly_stars to 0 for all StudentGameProfiles.

        Intended to run every Monday 00:00 via management command.
        Snapshots are preserved for history; only the running counter resets.

        Returns:
            int: Number of profiles reset.
        """
        count = StudentGameProfile.objects.update(weekly_stars=0)
        logger.info(f"Leaderboard: Reset weekly_stars for {count} student profiles.")
        return count
