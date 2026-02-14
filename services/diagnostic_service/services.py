"""
2026-02-12: Diagnostic assessment business logic service.

Purpose:
    Core diagnostic operations: start session, process responses,
    compute adaptive item selection, and generate final results.
    Delegates IRT math to the pure irt.py module.
"""

import logging  # 2026-02-12: Logging

from .models import (  # 2026-02-12: Models
    DiagnosticSession, DiagnosticResponse, DiagnosticResult,
)
from .irt import (  # 2026-02-12: IRT functions
    load_question_bank, select_next_item, estimate_theta,
    theta_to_level, compute_domain_scores, compute_domain_levels,
    DEFAULT_TOTAL_ITEMS,
)

logger = logging.getLogger(__name__)  # 2026-02-12: Module logger


class DiagnosticService:
    """2026-02-12: Core diagnostic assessment service with all business logic."""

    _question_bank = None  # 2026-02-12: Cached question bank

    @classmethod
    def _get_question_bank(cls):
        """
        2026-02-12: Get question bank (lazy-loaded, cached).

        Returns:
            list: List of item dicts with IRT parameters.
        """
        if cls._question_bank is None:  # 2026-02-12: Load once
            cls._question_bank = load_question_bank()
        return cls._question_bank

    @classmethod
    def start_session(cls, student):
        """
        2026-02-12: Start a new diagnostic session for a student.

        Checks if student already has a result (no retakes) or an
        in-progress session (resume instead).

        Args:
            student: Student model instance.

        Returns:
            dict: Result with session data and first item.
        """
        # 2026-02-12: Check if student already has a completed result
        if DiagnosticResult.objects.filter(student=student).exists():
            return {
                'success': False,
                'error': 'Diagnostic assessment already completed.',
                'code': 'ALREADY_COMPLETED',
            }

        # 2026-02-12: Check for in-progress session
        existing = DiagnosticSession.objects.filter(
            student=student, status='in_progress'
        ).first()

        if existing:  # 2026-02-12: Resume existing session
            return cls._session_status_response(existing)

        # 2026-02-12: Create new session
        question_bank = cls._get_question_bank()
        first_item = select_next_item(0.0, question_bank, [])

        if not first_item:  # 2026-02-12: Should not happen with 40 items
            return {
                'success': False,
                'error': 'No items available in question bank.',
                'code': 'NO_ITEMS',
            }

        session = DiagnosticSession.objects.create(  # 2026-02-12: New session
            student=student,
            status='in_progress',
            theta_estimate=0.0,
            items_administered=0,
            total_items=DEFAULT_TOTAL_ITEMS,
            current_item_id=first_item['id'],
            administered_item_ids=[],
        )

        logger.info(  # 2026-02-12: Log
            f"Started diagnostic session {session.id} for student {student.id}"
        )

        return {  # 2026-02-12: Success with first item
            'success': True,
            'session_id': str(session.id),
            'total_items': session.total_items,
            'items_administered': 0,
            'current_item': cls._format_item(first_item),
        }

    @classmethod
    def process_response(cls, student, item_id, selected_option, response_time_ms=0):
        """
        2026-02-12: Process a student's response and return next item or result.

        Args:
            student: Student model instance.
            item_id: The item ID being answered.
            selected_option: Index of selected option (0-based).
            response_time_ms: Time to respond in milliseconds.

        Returns:
            dict: Next item or final result.
        """
        # 2026-02-12: Find active session
        session = DiagnosticSession.objects.filter(
            student=student, status='in_progress'
        ).first()

        if not session:  # 2026-02-12: No active session
            return {
                'success': False,
                'error': 'No active diagnostic session found.',
                'code': 'NO_SESSION',
            }

        # 2026-02-12: Verify item matches expected
        if session.current_item_id != item_id:
            return {
                'success': False,
                'error': 'Unexpected item ID. Use /status/ to get current item.',
                'code': 'ITEM_MISMATCH',
            }

        # 2026-02-12: Find item in question bank
        question_bank = cls._get_question_bank()
        item = cls._find_item(question_bank, item_id)

        if not item:  # 2026-02-12: Item not found
            return {
                'success': False,
                'error': 'Item not found in question bank.',
                'code': 'ITEM_NOT_FOUND',
            }

        # 2026-02-12: Check correctness
        is_correct = selected_option == item['correct_option']

        # 2026-02-12: Update administered list
        administered_ids = list(session.administered_item_ids)
        administered_ids.append(item_id)

        # 2026-02-12: Build response history for theta estimation
        responses_for_theta = cls._build_response_history(
            session, question_bank, item, is_correct
        )

        # 2026-02-12: Estimate new theta
        new_theta = estimate_theta(responses_for_theta, session.theta_estimate)

        # 2026-02-12: Record response
        position = session.items_administered + 1
        DiagnosticResponse.objects.create(
            session=session,
            item_id=item_id,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            theta_after=new_theta,
            position=position,
        )

        # 2026-02-12: Update session
        session.theta_estimate = new_theta
        session.items_administered = position
        session.administered_item_ids = administered_ids

        # 2026-02-12: Check if assessment is complete
        if position >= session.total_items:
            return cls._complete_session(session, question_bank)

        # 2026-02-12: Select next item
        next_item = select_next_item(new_theta, question_bank, administered_ids)

        if not next_item:  # 2026-02-12: No more items (ran out early)
            return cls._complete_session(session, question_bank)

        session.current_item_id = next_item['id']
        session.save()  # 2026-02-12: Persist

        return {  # 2026-02-12: Next item
            'success': True,
            'session_id': str(session.id),
            'items_administered': position,
            'total_items': session.total_items,
            'is_complete': False,
            'current_item': cls._format_item(next_item),
        }

    @classmethod
    def get_status(cls, student):
        """
        2026-02-12: Get current session status (for page refresh recovery).

        Args:
            student: Student model instance.

        Returns:
            dict: Current session state with current item.
        """
        # 2026-02-12: Check for completed result first
        result = DiagnosticResult.objects.filter(student=student).first()
        if result:
            return {
                'success': True,
                'status': 'completed',
                'result': {
                    'overall_level': result.overall_level,
                    'theta_final': result.theta_final,
                    'domain_levels': result.domain_levels,
                },
            }

        # 2026-02-12: Check for in-progress session
        session = DiagnosticSession.objects.filter(
            student=student, status='in_progress'
        ).first()

        if not session:  # 2026-02-12: No session at all
            return {
                'success': True,
                'status': 'not_started',
            }

        return cls._session_status_response(session)

    @classmethod
    def get_result(cls, student):
        """
        2026-02-12: Get completed diagnostic result.

        Args:
            student: Student model instance.

        Returns:
            dict: Result data or error if not completed.
        """
        result = DiagnosticResult.objects.filter(student=student).first()

        if not result:  # 2026-02-12: No result yet
            return {
                'success': False,
                'error': 'No diagnostic result found. Complete the assessment first.',
                'code': 'NO_RESULT',
            }

        return {  # 2026-02-12: Return result
            'success': True,
            'result': {
                'overall_level': result.overall_level,
                'theta_final': result.theta_final,
                'domain_levels': result.domain_levels,
                'created_at': result.created_at.isoformat(),
            },
        }

    @classmethod
    def _complete_session(cls, session, question_bank):
        """
        2026-02-12: Complete a diagnostic session and create final result.

        Args:
            session: DiagnosticSession instance.
            question_bank: List of item dicts.

        Returns:
            dict: Final result data.
        """
        # 2026-02-12: Compute domain scores from all responses
        all_responses = session.responses.all().order_by('position')
        responses_for_domains = []

        for resp in all_responses:
            item = cls._find_item(question_bank, resp.item_id)
            if item:
                responses_for_domains.append((item, resp.is_correct))

        domain_scores = compute_domain_scores(responses_for_domains)
        domain_levels = compute_domain_levels(domain_scores)
        overall_level = theta_to_level(session.theta_estimate)

        # 2026-02-12: Update session
        session.status = 'completed'
        session.result_level = overall_level
        session.domain_scores = domain_scores
        session.current_item_id = ''
        session.save()

        # 2026-02-12: Create result (one per student)
        result = DiagnosticResult.objects.create(
            student=session.student,
            session=session,
            overall_level=overall_level,
            theta_final=session.theta_estimate,
            domain_levels=domain_levels,
        )

        logger.info(  # 2026-02-12: Log
            f"Completed diagnostic for student {session.student.id}: {overall_level}"
        )

        return {  # 2026-02-12: Final result
            'success': True,
            'session_id': str(session.id),
            'items_administered': session.items_administered,
            'total_items': session.total_items,
            'is_complete': True,
            'result': {
                'overall_level': overall_level,
                'theta_final': session.theta_estimate,
                'domain_levels': domain_levels,
                'domain_scores': domain_scores,
            },
        }

    @classmethod
    def _session_status_response(cls, session):
        """
        2026-02-12: Build session status response with current item.

        Args:
            session: DiagnosticSession instance.

        Returns:
            dict: Session state with current item.
        """
        question_bank = cls._get_question_bank()
        current_item = cls._find_item(question_bank, session.current_item_id)

        return {
            'success': True,
            'status': 'in_progress',
            'session_id': str(session.id),
            'items_administered': session.items_administered,
            'total_items': session.total_items,
            'current_item': cls._format_item(current_item) if current_item else None,
        }

    @classmethod
    def _build_response_history(cls, session, question_bank, current_item, is_correct):
        """
        2026-02-12: Build full response history for theta estimation.

        Args:
            session: DiagnosticSession instance.
            question_bank: List of item dicts.
            current_item: Current item dict.
            is_correct: Whether current response is correct.

        Returns:
            list: List of (item_dict, is_correct) tuples.
        """
        history = []  # 2026-02-12: Build from DB responses

        for resp in session.responses.all().order_by('position'):
            item = cls._find_item(question_bank, resp.item_id)
            if item:
                history.append((item, resp.is_correct))

        history.append((current_item, is_correct))  # 2026-02-12: Add current
        return history

    @staticmethod
    def _find_item(question_bank, item_id):
        """
        2026-02-12: Find an item in the question bank by ID.

        Args:
            question_bank: List of item dicts.
            item_id: Item ID to find.

        Returns:
            Optional[dict]: Item dict or None.
        """
        for item in question_bank:  # 2026-02-13: Linear search (100 items)
            if item['id'] == item_id:
                return item
        return None

    @staticmethod
    def _format_item(item):
        """
        2026-02-12: Format an item for API response (hide IRT params and answer).

        Args:
            item: Item dict from question bank.

        Returns:
            dict: Client-safe item data.
        """
        return {  # 2026-02-13: Expose question content and item type
            'id': item['id'],
            'domain': item['domain'],
            'question': item['question'],
            'options': item['options'],
            'item_type': item.get('item_type', 'mcq'),
        }
