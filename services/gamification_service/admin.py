"""
2026-02-20: Django admin registration for Gamification Engine (BS-GAM).
"""

from django.contrib import admin  # 2026-02-20: Admin registration

from .models import (  # 2026-02-20: All models to register
    Badge,
    CoinLedger,
    FreezeLedger,
    StudentBadge,
    StudentGameProfile,
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for Badge catalog."""

    list_display = ['badge_id', 'icon', 'name', 'category', 'rarity']  # 2026-02-20: Columns
    list_filter = ['category', 'rarity']  # 2026-02-20: Sidebar filters
    search_fields = ['badge_id', 'name', 'description']  # 2026-02-20: Search
    ordering = ['category', 'rarity', 'name']  # 2026-02-20: Default order


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for earned student badges."""

    list_display = ['student', 'badge', 'earned_at']  # 2026-02-20: Columns
    list_filter = ['badge__category']  # 2026-02-20: Category filter
    search_fields = ['student__full_name', 'badge__name']  # 2026-02-20: Search
    readonly_fields = ['earned_at']  # 2026-02-20: Immutable timestamp


@admin.register(CoinLedger)
class CoinLedgerAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for coin transaction ledger (read-only)."""

    list_display = ['student', 'amount', 'event_type', 'description', 'created_at']
    list_filter = ['event_type']  # 2026-02-20: Filter by transaction type
    search_fields = ['student__full_name', 'description']  # 2026-02-20: Search
    readonly_fields = ['id', 'student', 'amount', 'event_type', 'description',
                       'reference_id', 'created_at']  # 2026-02-20: All fields immutable

    def has_add_permission(self, request):
        """2026-02-20: Prevent manual insertion — ledger is append-only via code."""
        return False

    def has_change_permission(self, request, obj=None):
        """2026-02-20: Prevent edits — ledger rows are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """2026-02-20: Prevent deletion — preserve audit trail."""
        return False


@admin.register(StudentGameProfile)
class StudentGameProfileAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for student game profiles (read-mostly)."""

    list_display = ['student', 'coin_balance', 'total_stars_earned',
                    'freezes_available', 'total_badges_earned']  # 2026-02-20: Columns
    search_fields = ['student__full_name']  # 2026-02-20: Search by name
    readonly_fields = ['id', 'created_at', 'updated_at']  # 2026-02-20: Immutable fields


@admin.register(FreezeLedger)
class FreezeLedgerAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for freeze audit log (read-only)."""

    list_display = ['student', 'event_type', 'reason', 'created_at']  # 2026-02-20: Columns
    list_filter = ['event_type']  # 2026-02-20: Filter by event type
    search_fields = ['student__full_name', 'reason']  # 2026-02-20: Search
    readonly_fields = ['id', 'student', 'event_type', 'reason', 'created_at']  # 2026-02-20: Immutable
