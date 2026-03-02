"""
2026-02-27: Management command to reset weekly star counters (BS-GAM-005).

Run every Monday 00:00 to zero StudentGameProfile.weekly_stars for all students.
Snapshots in WeeklyLeaderboardSnapshot are preserved for history.

Usage:
    python manage.py reset_weekly_stars
"""

from django.core.management.base import BaseCommand

from services.gamification_service.leaderboard_service import LeaderboardService


class Command(BaseCommand):
    """2026-02-27: Reset weekly_stars field on all StudentGameProfile rows."""

    help = 'Reset weekly star counters for all students (run every Monday)'

    def handle(self, *args, **options):
        """
        2026-02-27: Execute the weekly star reset.

        Calls LeaderboardService.reset_weekly_stars() and reports
        the number of profiles updated.
        """
        count = LeaderboardService.reset_weekly_stars()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully reset weekly_stars for {count} student profile(s).'
            )
        )
