"""
2026-02-20: API views for Gamification Engine (BS-GAM).

7 endpoints, all requiring IsAuthenticated + student role:
  GET  /profile/         — coin balance, stars, freezes, recent badges
  GET  /badges/          — earned + available badge catalog
  POST /activity/        — record activity, earn coins/badges/freezes
  GET  /coins/ledger/    — paginated coin transaction history
  POST /coins/spend/     — purchase cosmetic item
  GET  /freezes/         — freeze status + next milestone
  POST /freezes/apply/   — consume one freeze token
"""

from rest_framework import status  # 2026-02-20: HTTP status codes
from rest_framework.exceptions import ValidationError  # 2026-02-20: DRF errors
from rest_framework.permissions import IsAuthenticated  # 2026-02-20: Auth check
from rest_framework.response import Response  # 2026-02-20: API response
from rest_framework.views import APIView  # 2026-02-20: CBV base

from .badge_catalog import COSMETIC_ITEMS  # 2026-02-20: Purchasable items
from .coin_service import spend_coins  # 2026-02-20: Spend logic
from .freeze_service import apply_freeze, check_and_award_freezes, _get_streak, FREEZE_MILESTONES  # 2026-02-20: Freeze logic
from .leaderboard_service import LeaderboardService  # 2026-02-27: Leaderboard logic
from .models import Badge, CoinLedger, StudentBadge, StudentGameProfile  # 2026-02-20: Models
from .services import GamificationService  # 2026-02-20: Facade


def _get_student(request):
    """
    2026-02-20: Extract student from authenticated request.

    Returns:
        tuple: (student, error_response) — one will be None.
    """
    if not hasattr(request.user, 'student_profile'):  # 2026-02-20: Must be student
        return None, Response(
            {'error': 'Only students can access gamification endpoints.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None


def _badge_dict(badge):
    """2026-02-20: Serialise a Badge model instance to dict."""
    return {
        'badge_id': badge.badge_id,
        'name': badge.name,
        'description': badge.description,
        'icon': badge.icon,
        'category': badge.category,
        'rarity': badge.rarity,
    }


def _student_badge_dict(sb):
    """2026-02-20: Serialise a StudentBadge instance to dict."""
    return {
        **_badge_dict(sb.badge),
        'earned_at': sb.earned_at.isoformat(),
    }


class ProfileView(APIView):
    """
    2026-02-20: GET /api/v1/gamification/profile/

    Returns cached gamification totals and 3 most recent badges.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def get(self, request):
        """2026-02-20: Return student game profile."""
        student, error = _get_student(request)
        if error:
            return error

        profile, _ = StudentGameProfile.objects.get_or_create(student=student)
        recent_badges = [
            _student_badge_dict(sb)
            for sb in StudentBadge.objects.filter(student=student).select_related('badge')[:3]
        ]

        return Response({  # 2026-02-20: Profile snapshot
            'coin_balance': profile.coin_balance,
            'total_stars_earned': profile.total_stars_earned,
            'freezes_available': profile.freezes_available,
            'total_badges_earned': profile.total_badges_earned,
            'recent_badges': recent_badges,
        }, status=status.HTTP_200_OK)


class BadgesView(APIView):
    """
    2026-02-20: GET /api/v1/gamification/badges/

    Returns earned badges and unearned catalog badges.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def get(self, request):
        """2026-02-20: Return earned + available badge lists."""
        student, error = _get_student(request)
        if error:
            return error

        earned_badges = StudentBadge.objects.filter(
            student=student
        ).select_related('badge').order_by('-earned_at')

        earned_ids = {sb.badge.badge_id for sb in earned_badges}

        available_badges = Badge.objects.exclude(
            badge_id__in=earned_ids
        ).order_by('category', 'rarity', 'name')

        return Response({  # 2026-02-20: Badge split
            'earned': [_student_badge_dict(sb) for sb in earned_badges],
            'available': [_badge_dict(b) for b in available_badges],
        }, status=status.HTTP_200_OK)


class ActivityView(APIView):
    """
    2026-02-20: POST /api/v1/gamification/activity/

    Records a completed learning activity and returns rewards earned.
    Body: { "stars": 4, "activity_type": "practice_stars", "reference_id": "uuid?" }
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def post(self, request):
        """2026-02-20: Process activity and return gamification rewards."""
        student, error = _get_student(request)
        if error:
            return error

        stars = request.data.get('stars')
        activity_type = request.data.get('activity_type')

        if stars is None or activity_type is None:
            return Response(
                {'error': "'stars' and 'activity_type' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stars_int = int(stars)
        except (ValueError, TypeError):
            return Response(
                {'error': "'stars' must be an integer 0-5."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2026-02-20: Validate activity_type
        valid_types = [choice[0] for choice in CoinLedger._meta.get_field('event_type').choices]
        if activity_type not in valid_types:
            activity_type = 'other'  # 2026-02-20: Graceful fallback

        reference_id = request.data.get('reference_id')

        result = GamificationService.process_activity(
            student=student,
            stars=stars_int,
            activity_type=activity_type,
            reference_id=reference_id,
        )

        return Response({  # 2026-02-20: Reward summary
            'coins_earned': result['coins_earned'],
            'new_coin_balance': result['new_coin_balance'],
            'badges_earned': result['new_badges'],
            'freezes_awarded': result['freezes_awarded'],
        }, status=status.HTTP_200_OK)


class CoinLedgerView(APIView):
    """
    2026-02-20: GET /api/v1/gamification/coins/ledger/

    Returns paginated coin transaction history (newest first, 20 per page).
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def get(self, request):
        """2026-02-20: Return coin ledger entries."""
        student, error = _get_student(request)
        if error:
            return error

        entries = CoinLedger.objects.filter(student=student).order_by('-created_at')[:20]

        return Response({  # 2026-02-20: Ledger slice
            'entries': [
                {
                    'amount': e.amount,
                    'event_type': e.event_type,
                    'description': e.description,
                    'created_at': e.created_at.isoformat(),
                }
                for e in entries
            ]
        }, status=status.HTTP_200_OK)


class SpendCoinsView(APIView):
    """
    2026-02-20: POST /api/v1/gamification/coins/spend/

    Purchase a cosmetic item with coins.
    Body: { "item_id": "avatar_star" }
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def post(self, request):
        """2026-02-20: Deduct coins and return new balance."""
        student, error = _get_student(request)
        if error:
            return error

        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': "'item_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = COSMETIC_ITEMS.get(item_id)
        if not item:
            return Response(
                {'error': f"Unknown item '{item_id}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_balance = spend_coins(
                student=student,
                amount=item['cost'],
                event_type='freeze_spend',  # 2026-02-20: Reuse closest type; cosmetics in future
                description=f"Purchased: {item['name']}",
            )
        except ValidationError as exc:
            return Response(
                {'error': exc.detail[0] if isinstance(exc.detail, list) else str(exc.detail)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({  # 2026-02-20: Purchase result
            'new_coin_balance': new_balance,
            'item_name': item['name'],
        }, status=status.HTTP_200_OK)


class FreezesView(APIView):
    """
    2026-02-20: GET /api/v1/gamification/freezes/

    Returns freeze status: available count, next milestone, current streak.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def get(self, request):
        """2026-02-20: Return freeze status summary."""
        student, error = _get_student(request)
        if error:
            return error

        profile, _ = StudentGameProfile.objects.get_or_create(student=student)
        streak = _get_streak(student)  # 2026-02-20: Cross-service streak lookup

        # 2026-02-20: Determine next unearned milestone
        from .freeze_service import FreezeLedger  # 2026-02-20: Local import
        next_milestone = None
        for threshold, _, reason in FREEZE_MILESTONES:
            if streak < threshold:
                already = FreezeLedger.objects.filter(
                    student=student, event_type='earned', reason=reason
                ).exists()
                if not already:
                    next_milestone = threshold
                    break

        return Response({  # 2026-02-20: Freeze status
            'freezes_available': profile.freezes_available,
            'max_freezes': 5,
            'next_milestone': next_milestone,
            'streak': streak,
        }, status=status.HTTP_200_OK)


class ApplyFreezeView(APIView):
    """
    2026-02-20: POST /api/v1/gamification/freezes/apply/

    Consume one freeze token to protect a missed streak day.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def post(self, request):
        """2026-02-20: Apply one freeze token."""
        student, error = _get_student(request)
        if error:
            return error

        try:
            result = apply_freeze(student)
        except ValidationError as exc:
            return Response(
                {'error': exc.detail[0] if isinstance(exc.detail, list) else str(exc.detail)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class LeaderboardView(APIView):
    """
    2026-02-27: GET /api/v1/gamification/leaderboard/?board=personal|class|regional

    Returns a ranked leaderboard. Board types:
    - personal: Student's own weekly history (always accessible).
    - class: Top 20 from same grade this week (requires parental opt-in).
    - regional: Top 50 all grades this week (requires opt-in + age >= 10).
    """

    permission_classes = [IsAuthenticated]  # 2026-02-27: Auth required

    def get(self, request):
        """2026-02-27: Return leaderboard data for the requested board type."""
        student, error = _get_student(request)
        if error:
            return error

        board_type = request.query_params.get('board', 'personal')
        if board_type not in ('personal', 'class', 'regional'):
            return Response(
                {'error': "board must be 'personal', 'class', or 'regional'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = LeaderboardService.get_leaderboard(board_type, student)

        if not result.get('success', True):
            code = result.get('code', '')
            if code == 'AGE_RESTRICTED':
                return Response({'error': result['error']}, status=status.HTTP_403_FORBIDDEN)
            if code == 'OPT_IN_REQUIRED':
                return Response({'error': result['error']}, status=status.HTTP_403_FORBIDDEN)
            return Response({'error': result.get('error', 'Unknown error.')},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
