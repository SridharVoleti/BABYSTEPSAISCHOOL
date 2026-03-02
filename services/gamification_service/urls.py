"""
2026-02-20: URL routing for Gamification Engine (BS-GAM).

All endpoints mounted under /api/v1/gamification/.
"""

from django.urls import path  # 2026-02-20: URL path builder

from .views import (  # 2026-02-20: View imports
    ProfileView,
    BadgesView,
    ActivityView,
    CoinLedgerView,
    SpendCoinsView,
    FreezesView,
    ApplyFreezeView,
    LeaderboardView,  # 2026-02-27: Leaderboard view (BS-GAM-005)
)

app_name = 'gamification_service'  # 2026-02-20: Namespace for URL reversal

urlpatterns = [
    # 2026-02-20: GET /api/v1/gamification/profile/
    path('profile/', ProfileView.as_view(), name='profile'),

    # 2026-02-20: GET /api/v1/gamification/badges/
    path('badges/', BadgesView.as_view(), name='badges'),

    # 2026-02-20: POST /api/v1/gamification/activity/
    path('activity/', ActivityView.as_view(), name='activity'),

    # 2026-02-20: GET /api/v1/gamification/coins/ledger/
    path('coins/ledger/', CoinLedgerView.as_view(), name='coin-ledger'),

    # 2026-02-20: POST /api/v1/gamification/coins/spend/
    path('coins/spend/', SpendCoinsView.as_view(), name='spend-coins'),

    # 2026-02-20: GET /api/v1/gamification/freezes/
    path('freezes/', FreezesView.as_view(), name='freezes'),

    # 2026-02-20: POST /api/v1/gamification/freezes/apply/
    path('freezes/apply/', ApplyFreezeView.as_view(), name='apply-freeze'),

    # 2026-02-27: GET /api/v1/gamification/leaderboard/
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
