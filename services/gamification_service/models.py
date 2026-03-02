"""
2026-02-20: Gamification Engine models (BS-GAM).

Purpose:
    Badge: Achievement catalog seeded from badge_catalog.py.
    StudentBadge: Earned badge record per student (append-only).
    CoinLedger: Append-only coin transaction log.
    StudentGameProfile: Cached totals (OneToOne → Student).
    FreezeLedger: Streak freeze audit log.
"""

import uuid  # 2026-02-20: UUID primary keys

from django.db import models  # 2026-02-20: Django ORM

from services.auth_service.models import Student  # 2026-02-20: Cross-app FK


class Badge(models.Model):
    """
    2026-02-20: Achievement badge catalog entry.

    Rows are seeded by migrations/0002_seed_badges.py from badge_catalog.py.
    badge_id is a stable slug used in code (e.g. 'week_warrior').
    """

    CATEGORY_CHOICES = [  # 2026-02-20: Badge grouping
        ('streak', 'Streak'),
        ('stars', 'Stars'),
        ('vocabulary', 'Vocabulary'),
        ('reading', 'Reading'),
        ('learning', 'Learning'),
    ]

    RARITY_CHOICES = [  # 2026-02-20: Badge rarity tier
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
    ]

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    badge_id = models.SlugField(  # 2026-02-20: Stable code identifier
        max_length=50, unique=True
    )
    name = models.CharField(max_length=100)  # 2026-02-20: Display name
    description = models.CharField(max_length=255)  # 2026-02-20: Achievement description
    icon = models.CharField(max_length=10)  # 2026-02-20: Emoji icon
    category = models.CharField(  # 2026-02-20: Badge category
        max_length=20, choices=CATEGORY_CHOICES
    )
    rarity = models.CharField(  # 2026-02-20: Rarity tier
        max_length=20, choices=RARITY_CHOICES, default='common'
    )

    class Meta:
        """2026-02-20: Model metadata."""

        ordering = ['category', 'rarity', 'name']  # 2026-02-20: Natural display order

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.icon} {self.name} ({self.badge_id})"


class StudentBadge(models.Model):
    """
    2026-02-20: A badge earned by a student (append-only record).

    Created once when the badge criterion is first met.
    unique_together prevents duplicate awards for the same badge.
    """

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-20: Badge recipient
        Student, on_delete=models.CASCADE, related_name='badges'
    )
    badge = models.ForeignKey(  # 2026-02-20: Which badge
        Badge, on_delete=models.CASCADE, related_name='student_badges'
    )
    earned_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: When earned

    class Meta:
        """2026-02-20: Model metadata."""

        unique_together = [  # 2026-02-20: One award per (student, badge)
            ['student', 'badge']
        ]
        ordering = ['-earned_at']  # 2026-02-20: Newest first

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.student.full_name} earned {self.badge.name}"


class CoinLedger(models.Model):
    """
    2026-02-20: Append-only coin transaction log.

    Every coin earn/spend creates a new row. Rows are never modified.
    Positive amount = earn; negative amount = spend.
    """

    EVENT_TYPE_CHOICES = [  # 2026-02-20: Transaction categories
        ('lesson_complete', 'Lesson Complete'),
        ('practice_stars', 'Practice Stars'),
        ('vocab_session', 'Vocabulary Session'),
        ('read_along', 'Read-Along'),
        ('badge_bonus', 'Badge Bonus'),
        ('freeze_spend', 'Freeze Spend'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-20: Coin owner
        Student, on_delete=models.CASCADE, related_name='coin_ledger'
    )
    amount = models.IntegerField()  # 2026-02-20: Positive=earn, negative=spend
    event_type = models.CharField(  # 2026-02-20: Transaction category
        max_length=30, choices=EVENT_TYPE_CHOICES
    )
    reference_id = models.UUIDField(  # 2026-02-20: FK-free reference to source object
        null=True, blank=True
    )
    description = models.CharField(max_length=200)  # 2026-02-20: Human-readable note
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Transaction time

    class Meta:
        """2026-02-20: Model metadata."""

        ordering = ['-created_at']  # 2026-02-20: Newest first

    def __str__(self):
        """2026-02-20: String representation."""
        sign = '+' if self.amount >= 0 else ''
        return f"{self.student.full_name} | {sign}{self.amount} coins | {self.event_type}"


class StudentGameProfile(models.Model):
    """
    2026-02-20: Cached gamification totals for a student (OneToOne → Student).

    Always access via StudentGameProfile.objects.get_or_create(student=student).
    Never modify coin_balance directly — use coin_service.earn_coins / spend_coins.
    freezes_available is capped at 5.
    """

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.OneToOneField(  # 2026-02-20: One profile per student
        Student, on_delete=models.CASCADE, related_name='game_profile'
    )
    coin_balance = models.IntegerField(default=0)  # 2026-02-20: Current coin balance
    total_stars_earned = models.IntegerField(default=0)  # 2026-02-20: Cumulative stars
    weekly_stars = models.IntegerField(default=0)  # 2026-02-27: Stars this week (reset Mondays)
    freezes_available = models.IntegerField(default=0)  # 2026-02-20: Max 5
    total_badges_earned = models.IntegerField(default=0)  # 2026-02-20: Cached badge count
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Profile created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-20: Last updated

    def __str__(self):
        """2026-02-20: String representation."""
        return (
            f"{self.student.full_name} | "
            f"💰{self.coin_balance} ⭐{self.total_stars_earned} "
            f"🧊{self.freezes_available}"
        )


class WeeklyLeaderboardSnapshot(models.Model):
    """
    2026-02-27: Weekly star snapshot per student for leaderboard ranking.

    One row per (student, week_start). Created/updated by
    LeaderboardService.record_week_snapshot each time stars are earned.
    Rows persist after weekly reset for history purposes.
    """

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-27: Which student
        Student, on_delete=models.CASCADE, related_name='leaderboard_snapshots'
    )
    grade = models.IntegerField()  # 2026-02-27: Denormalized from student.grade for fast filter
    stars_this_week = models.IntegerField(default=0)  # 2026-02-27: Stars earned this week
    week_start = models.DateField()  # 2026-02-27: Monday of this week
    display_name = models.CharField(max_length=150)  # 2026-02-27: Student's full_name snapshot

    class Meta:
        """2026-02-27: Model metadata."""

        unique_together = [['student', 'week_start']]  # 2026-02-27: One per student per week
        indexes = [  # 2026-02-27: Fast class board queries on (grade, week_start)
            models.Index(fields=['grade', 'week_start'], name='lb_grade_week_idx'),
        ]
        ordering = ['-week_start', '-stars_this_week']  # 2026-02-27: Newest week, top stars

    def __str__(self):
        """2026-02-27: String representation."""
        return (
            f"{self.display_name} | Grade {self.grade} | "
            f"⭐{self.stars_this_week} | w/c {self.week_start}"
        )


class FreezeLedger(models.Model):
    """
    2026-02-20: Streak freeze audit log (earned + applied events).

    Idempotency: before awarding a freeze at a milestone, check
    FreezeLedger.objects.filter(student=s, event_type='earned', reason=reason).exists().
    The reason field doubles as the idempotency key.
    """

    EVENT_TYPE_CHOICES = [  # 2026-02-20: Freeze event types
        ('earned', 'Earned'),
        ('applied', 'Applied'),
    ]

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-20: Freeze owner
        Student, on_delete=models.CASCADE, related_name='freeze_ledger'
    )
    event_type = models.CharField(  # 2026-02-20: Earned or applied
        max_length=10, choices=EVENT_TYPE_CHOICES
    )
    reason = models.CharField(max_length=100)  # 2026-02-20: e.g. "streak_7", "applied_2026-02-20"
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Event time

    class Meta:
        """2026-02-20: Model metadata."""

        ordering = ['-created_at']  # 2026-02-20: Newest first

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.student.full_name} | freeze {self.event_type} | {self.reason}"
