"""
2026-03-02: Phase 2 Weighted Star Formula service (BS-CMP-003).

Purpose:
    Aggregate four daily-learning signals into a single 1–5 star rating
    stored in DayProgress.phase2_star_rating and ConceptMastery.best_star_rating.

Formula (all components 0–100):
    weighted = 0.40 × comprehension_score
             + 0.20 × (read_along_score × 100)
             + 0.20 × practice_pct
             + 0.20 × self_explanation_score

    phase2_star_rating = clamp(ceil(weighted / 20), 1, 5)  [or 0 if weighted == 0]

Phase 1 compatibility:
    If read_along_score == 0 AND self_explanation_score == 0, the formula
    falls back to mastery_star_rating (preserves existing behaviour for
    lessons where Phase 2 components have not been recorded yet).
"""

import logging  # 2026-03-02: Module logger
import math  # 2026-03-02: ceil()

logger = logging.getLogger(__name__)  # 2026-03-02: Logger


class WeightedStarService:
    """
    2026-03-02: Computes and persists Phase 2 weighted star ratings.

    Call sequence:
        1. record_read_along()  — when ReadAlongSession completes
        2. record_self_explanation()  — when ComprehensionEvaluation saves
        3. compute_and_save()  — when mastery practice finalises (to update everything)
    """

    # 2026-03-02: Component weights (must sum to 1.0)
    WEIGHT_COMPREHENSION = 0.40
    WEIGHT_READ_ALONG = 0.20
    WEIGHT_PRACTICE = 0.20
    WEIGHT_SELF_EXPLANATION = 0.20

    @classmethod
    def record_read_along(cls, day_progress, overall_score: float) -> None:
        """
        2026-03-02: Store best read-along score on DayProgress.

        Keeps the highest overall_score seen for this lesson+day.
        Does NOT recompute phase2_star_rating (that happens in compute_and_save).

        Args:
            day_progress: DayProgress model instance.
            overall_score: Float 0.0–1.0 from ReadAlongSession.overall_score.
        """
        score = float(overall_score)  # 2026-03-02: Ensure float
        if score > day_progress.read_along_score:  # 2026-03-02: Keep best
            day_progress.read_along_score = score
            day_progress.save(update_fields=['read_along_score', 'updated_at'])
            logger.debug(
                "DayProgress %s read_along_score updated to %.4f",
                day_progress.id, score,
            )

    @classmethod
    def record_self_explanation(cls, day_progress, explanation_score: float) -> None:
        """
        2026-03-02: Store best self-explanation score on DayProgress.

        Keeps the highest comprehension_score seen for this lesson+day.
        Does NOT recompute phase2_star_rating.

        Args:
            day_progress: DayProgress model instance.
            explanation_score: Float 0–100 from ComprehensionEvaluation.comprehension_score.
        """
        score = float(explanation_score)  # 2026-03-02: Ensure float
        if score > day_progress.self_explanation_score:  # 2026-03-02: Keep best
            day_progress.self_explanation_score = score
            day_progress.save(update_fields=['self_explanation_score', 'updated_at'])
            logger.debug(
                "DayProgress %s self_explanation_score updated to %.2f",
                day_progress.id, score,
            )

    @classmethod
    def compute_and_save(cls, day_progress) -> int:
        """
        2026-03-02: Compute Phase 2 weighted star rating and persist.

        Reads all four components from day_progress + linked PracticeSession,
        applies the weighted formula, updates DayProgress.phase2_star_rating
        and ConceptMastery.best_star_rating.

        Falls back to mastery_star_rating when Phase 2 data is absent.

        Args:
            day_progress: DayProgress model instance.

        Returns:
            int: Computed phase2_star_rating (0–5).
        """
        # 2026-03-02: Fetch practice_pct from best completed PracticeSession for this day
        practice_pct = cls._get_practice_pct(day_progress)

        # 2026-03-02: Check whether Phase 2 components are present
        has_read_along = day_progress.read_along_score > 0.0
        has_self_exp = day_progress.self_explanation_score > 0.0
        phase2_active = has_read_along or has_self_exp

        if not phase2_active:
            # 2026-03-02: Phase 1 fallback — use mastery practice stars directly
            star_rating = day_progress.mastery_star_rating
            logger.debug(
                "DayProgress %s: Phase 1 fallback — using mastery_star_rating=%d",
                day_progress.id, star_rating,
            )
        else:
            # 2026-03-02: Normalise read_along_score (0–1) → (0–100) for uniform weighting
            read_along_100 = day_progress.read_along_score * 100.0

            weighted = (
                cls.WEIGHT_COMPREHENSION * day_progress.comprehension_score
                + cls.WEIGHT_READ_ALONG * read_along_100
                + cls.WEIGHT_PRACTICE * practice_pct
                + cls.WEIGHT_SELF_EXPLANATION * day_progress.self_explanation_score
            )  # 2026-03-02: Composite score 0–100

            if weighted <= 0:
                star_rating = 0
            else:
                star_rating = min(5, math.ceil(weighted / 20.0))  # 2026-03-02: 1–5

            logger.debug(
                "DayProgress %s: weighted=%.2f → stars=%d "
                "(comp=%.1f ra=%.4f prac=%.1f self_exp=%.1f)",
                day_progress.id, weighted, star_rating,
                day_progress.comprehension_score,
                day_progress.read_along_score,
                practice_pct,
                day_progress.self_explanation_score,
            )

        # 2026-03-02: Persist phase2_star_rating
        day_progress.phase2_star_rating = star_rating
        day_progress.save(update_fields=['phase2_star_rating', 'updated_at'])

        # 2026-03-02: Update ConceptMastery.best_star_rating if improved
        cls._update_concept_mastery(day_progress, star_rating)

        return star_rating

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_practice_pct(day_progress) -> float:
        """
        2026-03-02: Return best percentage_correct from PracticeSession for this day.

        Returns 0.0 if no completed PracticeSession found.

        Args:
            day_progress: DayProgress model instance.

        Returns:
            float: 0.0–100.0
        """
        from .models import PracticeSession  # 2026-03-02: Lazy import to avoid circulars

        best = (
            PracticeSession.objects
            .filter(
                lesson_progress=day_progress.lesson_progress,
                day_number=day_progress.day_number,
                status='completed',
            )
            .order_by('-percentage_correct')
            .values_list('percentage_correct', flat=True)
            .first()
        )
        return float(best) if best is not None else 0.0  # 2026-03-02: Default

    @staticmethod
    def _update_concept_mastery(day_progress, new_star_rating: int) -> None:
        """
        2026-03-02: Update ConceptMastery.best_star_rating if new_star_rating is better.

        Args:
            day_progress: DayProgress model instance.
            new_star_rating: int 0–5.
        """
        from .models import ConceptMastery  # 2026-03-02: Lazy import

        lesson_progress = day_progress.lesson_progress
        try:
            mastery = ConceptMastery.objects.filter(
                student=lesson_progress.student,
                lesson=lesson_progress.lesson,
                day_number=day_progress.day_number,
            ).first()
            if mastery and new_star_rating > mastery.best_star_rating:
                mastery.best_star_rating = new_star_rating
                mastery.is_mastered = mastery.is_mastered or (new_star_rating >= 3)
                mastery.save(update_fields=['best_star_rating', 'is_mastered', 'updated_at'])
                logger.debug(
                    "ConceptMastery for student=%s lesson=%s day=%d updated to %d stars",
                    lesson_progress.student.id,
                    lesson_progress.lesson.lesson_id,
                    day_progress.day_number,
                    new_star_rating,
                )
        except Exception as exc:  # 2026-03-02: Non-fatal — don't break mastery flow
            logger.warning("Failed to update ConceptMastery: %s", exc)
