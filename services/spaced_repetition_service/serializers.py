"""
2026-02-27: Serializers for Spaced Repetition Service (BS-SPC).
"""
from rest_framework import serializers  # 2026-02-27: DRF serializers


class ReviewCompleteSerializer(serializers.Serializer):
    """2026-02-27: Input for completing a concept review."""

    mastery_id = serializers.UUIDField()  # 2026-02-27: ConceptMastery UUID
    stars = serializers.IntegerField(min_value=0, max_value=5)  # 2026-02-27: Review rating
    explanation_seconds = serializers.IntegerField(min_value=0)  # 2026-02-27: Time spent
