"""
2026-02-12: Diagnostic assessment business logic service.

Purpose:
    Core diagnostic operations: start session, process responses,
    compute adaptive item selection, and generate final results.
    Delegates IRT math to the pure irt.py module.

    Also contains IQReassessmentService (BS-DIA-003) for rolling
    20-concept window evaluation and automated level adjustments.
"""

import logging  # 2026-02-12: Logging

from django.utils import timezone  # 2026-02-27: Timezone-aware timestamps

from .models import (  # 2026-02-12: Models
    DiagnosticSession, DiagnosticResponse, DiagnosticResult,
    IQReassessmentWindow, IQReassessmentEvent,  # 2026-02-27: Reassessment models
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


class IQReassessmentService:
    """
    2026-02-27: Rolling 20-concept window IQ level reassessment (BS-DIA-003).

    After every 20 mastered concepts a window is evaluated using three metrics:
      - avg_stars: average best star rating from mastery practice (0-5)
      - avg_reteaching: average attempts per concept (proxy for reteaching load)
      - avg_comprehension: average comprehension score from DayProgress (0-100)

    Upgrade (both consecutive windows must agree):
      avg_stars >= 4.5 AND avg_reteaching <= 1.5 AND avg_comprehension >= 75
    Downgrade (both consecutive windows must agree):
      avg_stars <= 2.0 AND avg_reteaching >= 3.0

    A confirmed upgrade/downgrade updates DiagnosticResult.overall_level and
    creates an IQReassessmentEvent. Parent is mock-notified in dev.
    """

    WINDOW_SIZE = 20  # 2026-02-27: Concepts per evaluation window
    UPGRADE_MIN_STARS = 4.5  # 2026-02-27: Minimum avg stars for upgrade
    UPGRADE_MAX_RETEACH = 1.5  # 2026-02-27: Maximum avg reteaching for upgrade
    UPGRADE_MIN_COMPREHENSION = 75.0  # 2026-02-27: Minimum avg comprehension for upgrade (0-100)
    DOWNGRADE_MAX_STARS = 2.0  # 2026-02-27: Maximum avg stars for downgrade
    DOWNGRADE_MIN_RETEACH = 3.0  # 2026-02-27: Minimum avg reteaching for downgrade
    LEVEL_ORDER = ['foundation', 'standard', 'advanced']  # 2026-02-27: Ordered tiers

    @classmethod
    def check_and_evaluate(cls, student):
        """
        2026-02-27: Check if a new window is due and evaluate it.

        Called each time a ConceptMastery is newly set to is_mastered=True.
        A window is due when total mastered count is a multiple of WINDOW_SIZE.

        Args:
            student: Student model instance.

        Returns:
            dict or None: Evaluation result if a window was evaluated, else None.
        """
        from services.teaching_engine.models import ConceptMastery  # 2026-02-27: Avoid circular

        # 2026-02-27: Count all mastered concepts for this student
        total_mastered = ConceptMastery.objects.filter(
            student=student, is_mastered=True
        ).count()

        if total_mastered == 0 or total_mastered % cls.WINDOW_SIZE != 0:
            return None  # 2026-02-27: No window due yet

        window_number = total_mastered // cls.WINDOW_SIZE  # 2026-02-27: Which window

        # 2026-02-27: Guard against double-evaluation (e.g. concurrent requests)
        if IQReassessmentWindow.objects.filter(
            student=student, window_number=window_number
        ).exists():
            return None  # 2026-02-27: Already evaluated this window

        # 2026-02-27: Require a baseline diagnostic result to compare against
        result = DiagnosticResult.objects.filter(student=student).first()
        if not result:
            return None  # 2026-02-27: No diagnostic baseline — skip

        level_before = result.overall_level  # 2026-02-27: Level at start of window

        # 2026-02-27: Grab the most recently mastered WINDOW_SIZE concepts
        recent_masteries = list(
            ConceptMastery.objects.filter(
                student=student, is_mastered=True
            ).order_by('-updated_at')[:cls.WINDOW_SIZE]
        )

        # 2026-02-27: Compute aggregate metrics for the window
        metrics = cls._compute_window_metrics(student, recent_masteries)

        # 2026-02-27: Determine outcome (upgrade / downgrade / maintain)
        outcome = cls._determine_outcome(
            metrics['avg_stars'],
            metrics['avg_reteaching'],
            metrics['avg_comprehension'],
            level_before,
        )

        # 2026-02-27: Compute what the level would be if this outcome applied
        level_after = cls._apply_outcome_to_level(level_before, outcome)

        # 2026-02-27: Persist the window record
        IQReassessmentWindow.objects.create(
            student=student,
            window_number=window_number,
            avg_stars=metrics['avg_stars'],
            avg_reteaching=metrics['avg_reteaching'],
            avg_comprehension=metrics['avg_comprehension'],
            outcome=outcome,
            level_before=level_before,
            level_after=level_after,
            concepts_in_window=metrics['concept_ids'],
        )

        # 2026-02-27: Check for 2 consecutive same-direction windows → apply change
        if outcome != 'maintain':
            prev_window = IQReassessmentWindow.objects.filter(
                student=student, window_number=window_number - 1
            ).first()
            if prev_window and prev_window.outcome == outcome:
                cls._apply_level_change(
                    student, level_before, level_after, outcome, window_number
                )

        logger.info(  # 2026-02-27: Audit log
            f"IQ reassessment window #{window_number} for {student.full_name}: "
            f"stars={metrics['avg_stars']:.2f} reteach={metrics['avg_reteaching']:.2f} "
            f"comprehension={metrics['avg_comprehension']:.1f} → {outcome} "
            f"({level_before} → {level_after})"
        )

        return {  # 2026-02-27: Return evaluation result
            'window_number': window_number,
            'outcome': outcome,
            'level_before': level_before,
            'level_after': level_after,
            'metrics': metrics,
        }

    @classmethod
    def _compute_window_metrics(cls, student, masteries):
        """
        2026-02-27: Aggregate stars, reteaching, and comprehension for a concept window.

        Args:
            student: Student model instance.
            masteries: List of ConceptMastery instances (most recent WINDOW_SIZE).

        Returns:
            dict: avg_stars, avg_reteaching, avg_comprehension (all floats),
                  concept_ids (list of '<lesson_id>:day<N>' strings).
        """
        from services.teaching_engine.models import DayProgress  # 2026-02-27: Avoid circular

        total_stars = 0.0
        total_reteach = 0.0
        total_comprehension = 0.0
        concept_ids = []

        for mastery in masteries:  # 2026-02-27: Accumulate per-concept metrics
            total_stars += mastery.best_star_rating
            total_reteach += mastery.attempts_count
            concept_ids.append(
                f"{mastery.lesson.lesson_id}:day{mastery.day_number}"
            )

            # 2026-02-27: Pull comprehension score from corresponding DayProgress
            day_prog = DayProgress.objects.filter(
                lesson_progress__student=student,
                lesson_progress__lesson=mastery.lesson,
                day_number=mastery.day_number,
            ).first()
            if day_prog:
                total_comprehension += day_prog.comprehension_score

        count = len(masteries)
        if count == 0:  # 2026-02-27: Guard against empty window
            return {
                'avg_stars': 0.0,
                'avg_reteaching': 0.0,
                'avg_comprehension': 0.0,
                'concept_ids': [],
            }

        return {  # 2026-02-27: Rounded averages
            'avg_stars': round(total_stars / count, 2),
            'avg_reteaching': round(total_reteach / count, 2),
            'avg_comprehension': round(total_comprehension / count, 1),
            'concept_ids': concept_ids,
        }

    @classmethod
    def _determine_outcome(cls, avg_stars, avg_reteaching, avg_comprehension, current_level):
        """
        2026-02-27: Apply threshold rules to decide window outcome.

        Upgrade requires ALL three conditions:
          avg_stars >= UPGRADE_MIN_STARS
          avg_reteaching <= UPGRADE_MAX_RETEACH
          avg_comprehension >= UPGRADE_MIN_COMPREHENSION

        Downgrade requires BOTH:
          avg_stars <= DOWNGRADE_MAX_STARS
          avg_reteaching >= DOWNGRADE_MIN_RETEACH

        Boundary: 'advanced' cannot upgrade; 'foundation' cannot downgrade.

        Args:
            avg_stars: Average best star rating across window (0-5).
            avg_reteaching: Average reteaching attempts across window.
            avg_comprehension: Average comprehension score (0-100).
            current_level: Current IQ level ('foundation'|'standard'|'advanced').

        Returns:
            str: 'upgrade', 'downgrade', or 'maintain'.
        """
        # 2026-02-27: Test upgrade conditions first (exceptional performance)
        if (
            avg_stars >= cls.UPGRADE_MIN_STARS
            and avg_reteaching <= cls.UPGRADE_MAX_RETEACH
            and avg_comprehension >= cls.UPGRADE_MIN_COMPREHENSION
        ):
            if current_level == 'advanced':  # 2026-02-27: Already at ceiling
                return 'maintain'
            return 'upgrade'

        # 2026-02-27: Test downgrade conditions (persistent struggle)
        if (
            avg_stars <= cls.DOWNGRADE_MAX_STARS
            and avg_reteaching >= cls.DOWNGRADE_MIN_RETEACH
        ):
            if current_level == 'foundation':  # 2026-02-27: Already at floor
                return 'maintain'
            return 'downgrade'

        return 'maintain'  # 2026-02-27: Default

    @classmethod
    def _apply_outcome_to_level(cls, current_level, outcome):
        """
        2026-02-27: Compute the projected level after this window outcome.

        Does NOT change DiagnosticResult — that requires 2 consecutive windows.

        Args:
            current_level: Current IQ level string.
            outcome: 'upgrade', 'downgrade', or 'maintain'.

        Returns:
            str: Projected level string.
        """
        idx = cls.LEVEL_ORDER.index(current_level)  # 2026-02-27: Positional index
        if outcome == 'upgrade':
            return cls.LEVEL_ORDER[min(idx + 1, len(cls.LEVEL_ORDER) - 1)]
        if outcome == 'downgrade':
            return cls.LEVEL_ORDER[max(idx - 1, 0)]
        return current_level  # 2026-02-27: 'maintain'

    @classmethod
    def _apply_level_change(cls, student, old_level, new_level, direction, window_number):
        """
        2026-02-27: Apply a confirmed level change to DiagnosticResult and record event.

        Called only when two consecutive windows share the same direction.
        Updates DiagnosticResult.overall_level and creates IQReassessmentEvent.
        Mock-notifies parent (log only in dev).

        Args:
            student: Student model instance.
            old_level: Level before change.
            new_level: Level after change.
            direction: 'upgrade' or 'downgrade'.
            window_number: Window number that triggered the change (second of the pair).
        """
        # 2026-02-27: Update diagnostic result overall level
        result = DiagnosticResult.objects.filter(student=student).first()
        if result:
            result.overall_level = new_level
            result.save()

        # 2026-02-27: Record the level-change event
        IQReassessmentEvent.objects.create(
            student=student,
            old_level=old_level,
            new_level=new_level,
            direction=direction,
            triggering_window=window_number,
            parent_notified=True,  # 2026-02-27: Mock: mark as notified immediately
            parent_notified_at=timezone.now(),
        )

        logger.info(  # 2026-02-27: Audit log
            f"IQ level CHANGED for {student.full_name}: {old_level} → {new_level} "
            f"({direction}, triggered by window #{window_number})"
        )

    @classmethod
    def get_history(cls, student):
        """
        2026-02-27: Retrieve reassessment windows and events for a student.

        Args:
            student: Student model instance.

        Returns:
            dict: Windows list, events list, and total mastered concept count.
        """
        from services.teaching_engine.models import ConceptMastery  # 2026-02-27: Avoid circular

        total_mastered = ConceptMastery.objects.filter(
            student=student, is_mastered=True
        ).count()

        windows_data = [  # 2026-02-27: Serialize each window
            {
                'window_number': w.window_number,
                'avg_stars': w.avg_stars,
                'avg_reteaching': w.avg_reteaching,
                'avg_comprehension': w.avg_comprehension,
                'outcome': w.outcome,
                'level_before': w.level_before,
                'level_after': w.level_after,
                'created_at': w.created_at.isoformat(),
            }
            for w in IQReassessmentWindow.objects.filter(student=student)
        ]

        events_data = [  # 2026-02-27: Serialize each event
            {
                'old_level': e.old_level,
                'new_level': e.new_level,
                'direction': e.direction,
                'triggering_window': e.triggering_window,
                'parent_notified': e.parent_notified,
                'created_at': e.created_at.isoformat(),
            }
            for e in IQReassessmentEvent.objects.filter(student=student)
        ]

        return {  # 2026-02-27: Full history payload
            'success': True,
            'total_mastered_concepts': total_mastered,
            'next_window_at': (
                (total_mastered // cls.WINDOW_SIZE + 1) * cls.WINDOW_SIZE
            ),
            'windows': windows_data,
            'events': events_data,
        }
