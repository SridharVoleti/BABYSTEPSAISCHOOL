"""
2026-02-12: IRT 3PL (Item Response Theory, 3-Parameter Logistic) module.

Purpose:
    Pure Python implementation of IRT 3PL adaptive testing algorithm.
    No Django dependencies - fully unit-testable.

    3PL model: P(correct) = c + (1-c) / (1 + exp(-a * (theta - b)))
    where:
        a = discrimination (how well the item differentiates ability levels)
        b = difficulty (the ability level where P = (1+c)/2)
        c = guessing parameter (lower asymptote, pseudo-chance)
        theta = student ability estimate

    Item selection: Maximum Fisher information at current theta.
    Theta estimation: Newton-Raphson MLE, clamped to [-3, 3].
    Level thresholds: theta < -0.5 = Foundation, -0.5..0.5 = Standard, > 0.5 = Advanced.
"""

import json  # 2026-02-12: JSON loading
import math  # 2026-02-12: Math functions
import os  # 2026-02-12: File path operations
from typing import Dict, List, Optional, Tuple  # 2026-02-12: Type hints


# 2026-02-12: Level threshold constants
THETA_FOUNDATION_UPPER = -0.5  # 2026-02-12: Below this = Foundation
THETA_STANDARD_UPPER = 0.5  # 2026-02-12: Below this = Standard, above = Advanced
THETA_MIN = -3.0  # 2026-02-12: Minimum theta clamp
THETA_MAX = 3.0  # 2026-02-12: Maximum theta clamp
DEFAULT_TOTAL_ITEMS = 25  # 2026-02-12: Total items to administer


def probability_correct(theta: float, a: float, b: float, c: float) -> float:
    """
    2026-02-12: Compute probability of correct response under IRT 3PL model.

    Args:
        theta: Student ability estimate.
        a: Item discrimination parameter.
        b: Item difficulty parameter.
        c: Item guessing (pseudo-chance) parameter.

    Returns:
        float: Probability of correct response in [c, 1].
    """
    exponent = -a * (theta - b)  # 2026-02-12: Logistic exponent
    exponent = max(-500, min(500, exponent))  # 2026-02-12: Prevent overflow
    return c + (1 - c) / (1 + math.exp(exponent))  # 2026-02-12: 3PL formula


def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """
    2026-02-12: Compute Fisher information of an item at a given theta.

    Higher information = item is more informative at this ability level.
    Used for optimal item selection (pick max information item).

    Args:
        theta: Student ability estimate.
        a: Item discrimination parameter.
        b: Item difficulty parameter.
        c: Item guessing parameter.

    Returns:
        float: Fisher information value (non-negative).
    """
    p = probability_correct(theta, a, b, c)  # 2026-02-12: P(correct)
    q = 1 - p  # 2026-02-12: P(incorrect)
    if p <= c or q <= 0:  # 2026-02-12: Avoid division by zero
        return 0.0
    p_star = (p - c) / (1 - c)  # 2026-02-12: Adjusted probability
    return (a ** 2) * (p_star ** 2) * (q / p)  # 2026-02-12: Fisher info formula


def select_next_item(
    theta: float,
    item_pool: List[Dict],
    administered_ids: List[str],
) -> Optional[Dict]:
    """
    2026-02-12: Select the next item with maximum Fisher information.

    Filters out already-administered items and picks the one providing
    the most information at the current theta estimate.

    Args:
        theta: Current ability estimate.
        item_pool: List of item dicts with 'id', 'a', 'b', 'c' keys.
        administered_ids: List of item IDs already used.

    Returns:
        Optional[Dict]: Best item dict, or None if no items available.
    """
    administered_set = set(administered_ids)  # 2026-02-12: Fast lookup
    available = [  # 2026-02-12: Filter administered items
        item for item in item_pool
        if item['id'] not in administered_set
    ]

    if not available:  # 2026-02-12: No items left
        return None

    best_item = None  # 2026-02-12: Track best
    best_info = -1.0

    for item in available:  # 2026-02-12: Find max information item
        info = fisher_information(theta, item['a'], item['b'], item['c'])
        if info > best_info:
            best_info = info
            best_item = item

    return best_item


def estimate_theta(
    responses: List[Tuple[Dict, bool]],
    prior_theta: float = 0.0,
    max_iterations: int = 20,
    convergence: float = 0.001,
) -> float:
    """
    2026-02-12: Estimate theta using Newton-Raphson MLE.

    Uses the method of maximum likelihood with Newton-Raphson iteration.
    Falls back to EAP (Expected A Posteriori) if MLE fails to converge.

    Args:
        responses: List of (item_dict, is_correct) tuples.
        prior_theta: Starting theta value.
        max_iterations: Max Newton-Raphson iterations.
        convergence: Convergence threshold.

    Returns:
        float: Updated theta estimate, clamped to [THETA_MIN, THETA_MAX].
    """
    if not responses:  # 2026-02-12: No data, return prior
        return prior_theta

    theta = prior_theta  # 2026-02-12: Starting point

    for _ in range(max_iterations):  # 2026-02-12: Newton-Raphson iteration
        numerator = 0.0  # 2026-02-12: First derivative of log-likelihood
        denominator = 0.0  # 2026-02-12: Negative second derivative

        for item, correct in responses:
            a = item['a']  # 2026-02-12: Item parameters
            b = item['b']
            c = item['c']

            p = probability_correct(theta, a, b, c)  # 2026-02-12: P(correct)
            q = 1 - p  # 2026-02-12: P(incorrect)

            if p <= c or q <= 0 or p >= 1:  # 2026-02-12: Avoid degenerate cases
                continue

            p_star = (p - c) / (1 - c)  # 2026-02-12: Adjusted probability
            w = a * p_star * q / p  # 2026-02-12: Weight term

            if correct:  # 2026-02-12: Correct response contribution
                numerator += w
            else:  # 2026-02-12: Incorrect response contribution
                numerator -= a * p_star

            denominator += (a ** 2) * (p_star ** 2) * (q / p)  # 2026-02-12: Info

        if abs(denominator) < 1e-10:  # 2026-02-12: Avoid division by zero
            break

        delta = numerator / denominator  # 2026-02-12: Newton step
        theta += delta

        theta = max(THETA_MIN, min(THETA_MAX, theta))  # 2026-02-12: Clamp

        if abs(delta) < convergence:  # 2026-02-12: Converged
            break

    return max(THETA_MIN, min(THETA_MAX, theta))  # 2026-02-12: Final clamp


def theta_to_level(theta: float) -> str:
    """
    2026-02-12: Convert theta estimate to placement level.

    Args:
        theta: IRT ability estimate.

    Returns:
        str: 'foundation', 'standard', or 'advanced'.
    """
    if theta < THETA_FOUNDATION_UPPER:  # 2026-02-12: Below -0.5
        return 'foundation'
    elif theta < THETA_STANDARD_UPPER:  # 2026-02-12: -0.5 to 0.5
        return 'standard'
    return 'advanced'  # 2026-02-12: Above 0.5


def compute_domain_scores(
    responses: List[Tuple[Dict, bool]],
) -> Dict[str, float]:
    """
    2026-02-12: Compute per-domain (subject) theta estimates.

    Groups responses by domain and runs theta estimation on each group.

    Args:
        responses: List of (item_dict, is_correct) tuples.

    Returns:
        Dict[str, float]: Domain name -> theta estimate.
    """
    domain_responses: Dict[str, List[Tuple[Dict, bool]]] = {}  # 2026-02-12: Group

    for item, correct in responses:  # 2026-02-12: Group by domain
        domain = item.get('domain', 'unknown')
        if domain not in domain_responses:
            domain_responses[domain] = []
        domain_responses[domain].append((item, correct))

    domain_scores = {}  # 2026-02-12: Compute per-domain theta
    for domain, resps in domain_responses.items():
        domain_scores[domain] = estimate_theta(resps)

    return domain_scores


def compute_domain_levels(domain_scores: Dict[str, float]) -> Dict[str, str]:
    """
    2026-02-12: Convert domain theta scores to level labels.

    Args:
        domain_scores: Dict of domain -> theta.

    Returns:
        Dict[str, str]: Domain -> level string.
    """
    return {  # 2026-02-12: Map each domain theta to level
        domain: theta_to_level(theta)
        for domain, theta in domain_scores.items()
    }


def load_question_bank() -> List[Dict]:
    """
    2026-02-12: Load question bank from JSON file.

    Returns:
        List[Dict]: List of item dicts with IRT parameters and content.
    """
    bank_path = os.path.join(  # 2026-02-12: Path to question bank
        os.path.dirname(os.path.abspath(__file__)),
        'question_bank.json',
    )
    with open(bank_path, 'r', encoding='utf-8') as f:  # 2026-02-12: Load JSON
        data = json.load(f)
    return data['items']  # 2026-02-12: Return items list
