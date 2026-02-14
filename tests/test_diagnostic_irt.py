"""
2026-02-12: Unit tests for IRT 3PL algorithm module.

Purpose:
    Test the pure Python IRT functions in isolation (no Django deps).
    Covers probability, Fisher information, item selection, theta estimation,
    and level classification.
"""

import math  # 2026-02-12: Math for assertions
import pytest  # 2026-02-12: Pytest framework

from services.diagnostic_service.irt import (  # 2026-02-12: Functions under test
    probability_correct,
    fisher_information,
    select_next_item,
    estimate_theta,
    theta_to_level,
    compute_domain_scores,
    compute_domain_levels,
    load_question_bank,
    THETA_MIN,
    THETA_MAX,
)


# 2026-02-12: Sample items for testing
SAMPLE_ITEMS = [
    {'id': 'T1', 'domain': 'math', 'a': 1.0, 'b': -1.0, 'c': 0.2},
    {'id': 'T2', 'domain': 'math', 'a': 1.5, 'b': 0.0, 'c': 0.2},
    {'id': 'T3', 'domain': 'language', 'a': 1.2, 'b': 0.5, 'c': 0.15},
    {'id': 'T4', 'domain': 'language', 'a': 2.0, 'b': 1.5, 'c': 0.1},
    {'id': 'T5', 'domain': 'science', 'a': 1.0, 'b': -0.5, 'c': 0.25},
]


@pytest.mark.unit
class TestProbabilityCorrect:
    """2026-02-12: Tests for the 3PL probability function."""

    def test_at_difficulty_level(self):
        """2026-02-12: P at theta=b should be (1+c)/2."""
        a, b, c = 1.5, 0.5, 0.2  # 2026-02-12: Parameters
        p = probability_correct(b, a, b, c)  # 2026-02-12: theta = b
        expected = (1 + c) / 2  # 2026-02-12: Midpoint
        assert abs(p - expected) < 0.01

    def test_high_ability(self):
        """2026-02-12: High theta should give P close to 1."""
        p = probability_correct(3.0, 1.0, 0.0, 0.2)  # 2026-02-12: theta >> b
        assert p > 0.95

    def test_low_ability(self):
        """2026-02-12: Low theta should give P close to c (guessing)."""
        p = probability_correct(-3.0, 1.0, 0.0, 0.2)  # 2026-02-12: theta << b
        assert abs(p - 0.2) < 0.05  # 2026-02-12: Close to guessing param

    def test_guessing_floor(self):
        """2026-02-12: P should never go below c."""
        p = probability_correct(-10.0, 2.0, 0.0, 0.25)  # 2026-02-12: Very low theta
        assert p >= 0.25

    def test_probability_range(self):
        """2026-02-12: P should always be in [c, 1]."""
        for theta in [-3, -1, 0, 1, 3]:  # 2026-02-12: Range of thetas
            p = probability_correct(theta, 1.0, 0.0, 0.2)
            assert 0.2 <= p <= 1.0


@pytest.mark.unit
class TestFisherInformation:
    """2026-02-12: Tests for Fisher information computation."""

    def test_positive_information(self):
        """2026-02-12: Fisher info should be non-negative."""
        info = fisher_information(0.0, 1.5, 0.0, 0.2)  # 2026-02-12: At difficulty
        assert info >= 0

    def test_max_near_difficulty(self):
        """2026-02-12: Fisher info should peak near item difficulty."""
        info_at_b = fisher_information(0.0, 1.5, 0.0, 0.2)  # 2026-02-12: At b
        info_far = fisher_information(3.0, 1.5, 0.0, 0.2)  # 2026-02-12: Far from b
        assert info_at_b > info_far

    def test_higher_discrimination_more_info(self):
        """2026-02-12: Higher discrimination should give more information."""
        info_low = fisher_information(0.0, 0.5, 0.0, 0.2)  # 2026-02-12: Low a
        info_high = fisher_information(0.0, 2.0, 0.0, 0.2)  # 2026-02-12: High a
        assert info_high > info_low


@pytest.mark.unit
class TestSelectNextItem:
    """2026-02-12: Tests for adaptive item selection."""

    def test_selects_most_informative(self):
        """2026-02-12: Should select item with max Fisher info at current theta."""
        selected = select_next_item(0.0, SAMPLE_ITEMS, [])  # 2026-02-12: Select
        assert selected is not None
        assert selected['id'] in [item['id'] for item in SAMPLE_ITEMS]

    def test_excludes_administered(self):
        """2026-02-12: Should not select already-administered items."""
        administered = ['T1', 'T2', 'T3']  # 2026-02-12: Already used
        selected = select_next_item(0.0, SAMPLE_ITEMS, administered)
        assert selected is not None
        assert selected['id'] not in administered

    def test_returns_none_when_exhausted(self):
        """2026-02-12: Should return None when all items administered."""
        all_ids = [item['id'] for item in SAMPLE_ITEMS]  # 2026-02-12: All used
        selected = select_next_item(0.0, SAMPLE_ITEMS, all_ids)
        assert selected is None

    def test_empty_pool(self):
        """2026-02-12: Should return None for empty pool."""
        selected = select_next_item(0.0, [], [])  # 2026-02-12: No items
        assert selected is None


@pytest.mark.unit
class TestEstimateTheta:
    """2026-02-12: Tests for Newton-Raphson MLE theta estimation."""

    def test_all_correct_raises_theta(self):
        """2026-02-12: All correct responses should raise theta above 0."""
        responses = [  # 2026-02-12: All correct
            (SAMPLE_ITEMS[0], True),
            (SAMPLE_ITEMS[1], True),
            (SAMPLE_ITEMS[2], True),
        ]
        theta = estimate_theta(responses, 0.0)  # 2026-02-12: From prior 0
        assert theta > 0.0

    def test_all_incorrect_lowers_theta(self):
        """2026-02-12: All incorrect responses should lower theta below 0."""
        responses = [  # 2026-02-12: All incorrect
            (SAMPLE_ITEMS[0], False),
            (SAMPLE_ITEMS[1], False),
            (SAMPLE_ITEMS[2], False),
        ]
        theta = estimate_theta(responses, 0.0)  # 2026-02-12: From prior 0
        assert theta < 0.0

    def test_clamped_to_range(self):
        """2026-02-12: Theta should be clamped to [THETA_MIN, THETA_MAX]."""
        # 2026-02-12: Many correct on easy items should push theta up
        responses = [(SAMPLE_ITEMS[0], True)] * 20
        theta = estimate_theta(responses, 0.0)
        assert THETA_MIN <= theta <= THETA_MAX

    def test_empty_responses_returns_prior(self):
        """2026-02-12: No responses should return prior theta."""
        theta = estimate_theta([], 1.5)  # 2026-02-12: Prior of 1.5
        assert theta == 1.5

    def test_mixed_responses_moderate_theta(self):
        """2026-02-12: Mixed responses should give moderate theta."""
        responses = [  # 2026-02-12: Mixed correct/incorrect
            (SAMPLE_ITEMS[0], True),
            (SAMPLE_ITEMS[1], False),
            (SAMPLE_ITEMS[2], True),
            (SAMPLE_ITEMS[3], False),
        ]
        theta = estimate_theta(responses, 0.0)
        assert -2.0 < theta < 2.0  # 2026-02-12: Should be moderate


@pytest.mark.unit
class TestThetaToLevel:
    """2026-02-12: Tests for theta to level conversion."""

    def test_foundation(self):
        """2026-02-12: Low theta should map to foundation."""
        assert theta_to_level(-1.0) == 'foundation'
        assert theta_to_level(-3.0) == 'foundation'

    def test_standard(self):
        """2026-02-12: Medium theta should map to standard."""
        assert theta_to_level(0.0) == 'standard'
        assert theta_to_level(-0.4) == 'standard'
        assert theta_to_level(0.4) == 'standard'

    def test_advanced(self):
        """2026-02-12: High theta should map to advanced."""
        assert theta_to_level(0.5) == 'advanced'
        assert theta_to_level(2.0) == 'advanced'

    def test_boundary_foundation_standard(self):
        """2026-02-12: -0.5 boundary should be standard."""
        assert theta_to_level(-0.5) == 'standard'

    def test_boundary_standard_advanced(self):
        """2026-02-12: 0.5 boundary should be advanced."""
        assert theta_to_level(0.5) == 'advanced'


@pytest.mark.unit
class TestDomainScores:
    """2026-02-12: Tests for per-domain scoring."""

    def test_computes_per_domain(self):
        """2026-02-12: Should compute separate theta for each domain."""
        responses = [
            (SAMPLE_ITEMS[0], True),  # 2026-02-12: math
            (SAMPLE_ITEMS[1], True),  # 2026-02-12: math
            (SAMPLE_ITEMS[2], False),  # 2026-02-12: language
            (SAMPLE_ITEMS[3], False),  # 2026-02-12: language
        ]
        scores = compute_domain_scores(responses)
        assert 'math' in scores
        assert 'language' in scores
        assert scores['math'] > scores['language']  # 2026-02-12: Math all correct

    def test_domain_levels(self):
        """2026-02-12: Should convert domain scores to levels."""
        scores = {'math': 1.0, 'language': -1.0, 'science': 0.0}
        levels = compute_domain_levels(scores)
        assert levels['math'] == 'advanced'
        assert levels['language'] == 'foundation'
        assert levels['science'] == 'standard'


@pytest.mark.unit
class TestLoadQuestionBank:
    """2026-02-12: Tests for question bank loading."""

    def test_loads_items(self):
        """2026-02-12: Should load 40 items from JSON file."""
        items = load_question_bank()
        assert len(items) == 40

    def test_item_structure(self):
        """2026-02-12: Each item should have required fields."""
        items = load_question_bank()
        required_fields = ['id', 'domain', 'a', 'b', 'c', 'question', 'options', 'correct_option']
        for item in items:
            for field in required_fields:
                assert field in item, f"Missing field '{field}' in item {item.get('id', '?')}"

    def test_four_domains(self):
        """2026-02-12: Should have items from 4 domains."""
        items = load_question_bank()
        domains = set(item['domain'] for item in items)
        assert domains == {'math', 'language', 'science', 'social_studies'}

    def test_ten_per_domain(self):
        """2026-02-12: Should have 10 items per domain."""
        items = load_question_bank()
        domain_counts = {}
        for item in items:
            domain = item['domain']
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        for domain, count in domain_counts.items():
            assert count == 10, f"Domain '{domain}' has {count} items, expected 10"

    def test_four_options_each(self):
        """2026-02-12: Each item should have exactly 4 options."""
        items = load_question_bank()
        for item in items:
            assert len(item['options']) == 4, f"Item {item['id']} has {len(item['options'])} options"

    def test_correct_option_valid(self):
        """2026-02-12: correct_option should be 0-3."""
        items = load_question_bank()
        for item in items:
            assert 0 <= item['correct_option'] <= 3, f"Item {item['id']} has invalid correct_option"
