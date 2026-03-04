"""
2026-03-04: Pod Management & Alert business logic (BS-POD + BS-MON).

Purpose:
    PodService: pod CRUD, enrollment management, real-time status
    (traffic-light colours), and monitor dashboard aggregation.
    AlertService: create MonitorAlert records and dispatch parent
    notifications via the existing OTP/WhatsApp provider pattern.
"""

import logging  # 2026-03-04: Module logger

from datetime import timedelta  # 2026-03-04: Time calculations

from django.utils import timezone  # 2026-03-04: Timezone-aware datetimes

from services.auth_service.models import Student  # 2026-03-04: Student model
from .models import (  # 2026-03-04: Pod models
    Pod, PodEnrollment, StudentSession, AttentionEvent, MonitorAlert,
)

logger = logging.getLogger(__name__)  # 2026-03-04: Module logger

# 2026-03-04: Heartbeat alive window in seconds
HEARTBEAT_ALIVE_SECONDS = 90

# 2026-03-04: Attention threshold — below this → not focusing
ATTENTION_THRESHOLD = 0.5


def _is_session_alive(session: StudentSession) -> bool:
    """
    2026-03-04: Return True if the session received a heartbeat in the last 90s.

    Args:
        session: StudentSession instance.

    Returns:
        bool: True if still active.
    """
    cutoff = timezone.now() - timedelta(seconds=HEARTBEAT_ALIVE_SECONDS)  # 2026-03-04: Cutoff
    return session.last_heartbeat >= cutoff  # 2026-03-04: Alive?


class PodService:
    """
    2026-03-04: Core pod management service.

    Handles pod listing, enrollment, status computation (traffic-light),
    and monitor dashboard aggregation.
    """

    @staticmethod
    def get_all_pods():
        """
        2026-03-04: Return all active pods (for admin/monitor listing).

        Returns:
            list[Pod]: All active pods ordered by grade then name.
        """
        return Pod.objects.filter(is_active=True)  # 2026-03-04: Active pods

    @staticmethod
    def get_pod_status(pod_id):
        """
        2026-03-04: Compute real-time traffic-light status for a pod.

        Traffic-light logic:
            GREEN  : all active students are focusing (attention_score > 0.5)
            AMBER  : 1-2 active students not focusing
            RED    : 3+ active students not focusing
            GREY   : fewer than 2 active students (session not in progress)

        Args:
            pod_id: UUID of the pod.

        Returns:
            dict: {pod, status, active_count, focusing_count, students}
        """
        try:
            pod = Pod.objects.get(id=pod_id, is_active=True)  # 2026-03-04: Lookup
        except Pod.DoesNotExist:
            return None  # 2026-03-04: Not found

        enrollments = pod.enrollments.filter(is_active=True).select_related('student')
        student_statuses = []  # 2026-03-04: Per-student status list
        active_count = 0  # 2026-03-04: Students with live heartbeat
        focusing_count = 0  # 2026-03-04: Active AND focusing

        for enrollment in enrollments:  # 2026-03-04: Per-student pass
            student = enrollment.student
            # 2026-03-04: Find most recent session for this enrollment
            session = (
                StudentSession.objects
                .filter(pod_enrollment=enrollment)
                .order_by('-session_start')
                .first()
            )

            # 2026-03-04: Compute student-level indicators
            is_alive = session is not None and _is_session_alive(session)
            attention = session.attention_score if session else 1.0
            is_focusing = is_alive and attention > ATTENTION_THRESHOLD

            if is_alive:
                active_count += 1  # 2026-03-04: Count active
            if is_focusing:
                focusing_count += 1  # 2026-03-04: Count focusing

            # 2026-03-04: Unresolved alerts for this student
            alert_count = MonitorAlert.objects.filter(
                student=student, is_resolved=False
            ).count()

            student_statuses.append({  # 2026-03-04: Student summary
                'student_id': str(student.id),
                'student_name': student.full_name,
                'is_active': is_alive,
                'attention_score': round(attention, 2),
                'is_focusing': is_focusing,
                'alert_count': alert_count,
                'last_heartbeat': (
                    session.last_heartbeat.isoformat() if session else None
                ),
            })

        # 2026-03-04: Compute traffic-light colour
        not_focusing_count = active_count - focusing_count  # 2026-03-04: Count not-focusing
        if active_count < 2:  # 2026-03-04: Session not really in progress
            colour = 'grey'
        elif not_focusing_count == 0:  # 2026-03-04: All good
            colour = 'green'
        elif not_focusing_count <= 2:  # 2026-03-04: Minor concern
            colour = 'amber'
        else:  # 2026-03-04: Serious concern
            colour = 'red'

        return {  # 2026-03-04: Pod status payload
            'pod': {
                'id': str(pod.id),
                'name': pod.name,
                'grade': pod.grade,
                'subject_focus': pod.subject_focus,
                'max_size': pod.max_size,
                'enrolled_count': enrollments.count(),
            },
            'traffic_light': colour,
            'active_count': active_count,
            'focusing_count': focusing_count,
            'students': student_statuses,
        }

    @staticmethod
    def list_all_pod_statuses():
        """
        2026-03-04: Return status for every active pod (monitor dashboard).

        Returns:
            list[dict]: Pod statuses for all active pods.
        """
        pods = Pod.objects.filter(is_active=True)  # 2026-03-04: Active pods
        statuses = []  # 2026-03-04: Accumulate
        for pod in pods:  # 2026-03-04: Per-pod status
            status = PodService.get_pod_status(pod.id)  # 2026-03-04: Compute
            if status:
                statuses.append(status)  # 2026-03-04: Add to list
        return statuses  # 2026-03-04: Return all

    @staticmethod
    def enroll_student(pod_id, student_id):
        """
        2026-03-04: Enroll a student in a pod, enforcing the 5-student cap.

        Args:
            pod_id: UUID of the pod.
            student_id: UUID of the student.

        Returns:
            dict: {success, enrollment/error, code}
        """
        try:
            pod = Pod.objects.get(id=pod_id, is_active=True)  # 2026-03-04: Pod lookup
        except Pod.DoesNotExist:
            return {'success': False, 'error': 'Pod not found.', 'code': 'POD_NOT_FOUND'}

        try:
            student = Student.objects.get(id=student_id, is_active=True)  # 2026-03-04: Student
        except Student.DoesNotExist:
            return {'success': False, 'error': 'Student not found.', 'code': 'STUDENT_NOT_FOUND'}

        # 2026-03-04: Check if already enrolled
        existing = PodEnrollment.objects.filter(pod=pod, student=student).first()
        if existing:
            if existing.is_active:  # 2026-03-04: Already active
                return {'success': False, 'error': 'Already enrolled.', 'code': 'ALREADY_ENROLLED'}
            # 2026-03-04: Re-activate lapsed enrollment
            existing.is_active = True
            existing.save()
            return {'success': True, 'enrollment_id': str(existing.id)}

        # 2026-03-04: Check pod cap
        active_count = pod.enrollments.filter(is_active=True).count()
        if active_count >= pod.max_size:  # 2026-03-04: At capacity
            return {
                'success': False,
                'error': f'Pod is full ({pod.max_size} students max).',
                'code': 'POD_FULL',
            }

        # 2026-03-04: Create enrollment
        enrollment = PodEnrollment.objects.create(pod=pod, student=student)
        logger.info(f"Enrolled {student.full_name} in {pod.name}")  # 2026-03-04: Log
        return {'success': True, 'enrollment_id': str(enrollment.id)}  # 2026-03-04: Return

    @staticmethod
    def unenroll_student(pod_id, student_id):
        """
        2026-03-04: Remove (soft-delete) a student from a pod.

        Args:
            pod_id: UUID of the pod.
            student_id: UUID of the student.

        Returns:
            dict: {success, error/code}
        """
        try:
            enrollment = PodEnrollment.objects.get(  # 2026-03-04: Lookup enrollment
                pod_id=pod_id,
                student_id=student_id,
                is_active=True,
            )
        except PodEnrollment.DoesNotExist:
            return {
                'success': False,
                'error': 'Active enrollment not found.',
                'code': 'NOT_ENROLLED',
            }

        enrollment.is_active = False  # 2026-03-04: Soft-delete
        enrollment.save()  # 2026-03-04: Persist
        logger.info(  # 2026-03-04: Log
            f"Unenrolled {enrollment.student.full_name} from {enrollment.pod.name}"
        )
        return {'success': True}  # 2026-03-04: Return

    @staticmethod
    def get_student_pod(student):
        """
        2026-03-04: Return the student's current active pod enrollment (or None).

        Args:
            student: Student model instance.

        Returns:
            PodEnrollment | None: Active enrollment if exists.
        """
        return PodEnrollment.objects.filter(  # 2026-03-04: Active enrollment
            student=student, is_active=True
        ).select_related('pod').first()

    @staticmethod
    def record_heartbeat(student):
        """
        2026-03-04: Update last_heartbeat for the student's current session.

        Creates a new StudentSession if none exists for today's enrollment.

        Args:
            student: Student model instance.

        Returns:
            dict: {success, is_active}
        """
        enrollment = PodService.get_student_pod(student)  # 2026-03-04: Find pod
        if not enrollment:  # 2026-03-04: Not in a pod
            return {'success': False, 'error': 'Student not enrolled in any pod.', 'code': 'NO_POD'}

        # 2026-03-04: Get or create session for this enrollment
        session, created = StudentSession.objects.get_or_create(  # 2026-03-04: Idempotent
            pod_enrollment=enrollment,
            is_active=True,
            defaults={'student': student},
        )

        # 2026-03-04: Update heartbeat timestamp
        session.last_heartbeat = timezone.now()
        session.student = student  # 2026-03-04: Ensure student FK is set
        session.save(update_fields=['last_heartbeat', 'student'])
        return {'success': True, 'is_active': True}  # 2026-03-04: Return

    @staticmethod
    def record_attention_event(student, event_type, ai_response='', escalated=False):
        """
        2026-03-04: Record an attention anomaly event for a student.

        Args:
            student: Student model instance.
            event_type: One of the ATTENTION_EVENT_TYPES choices.
            ai_response: What the AI said in response.
            escalated: Whether a parent was notified.

        Returns:
            dict: {success, event_id}
        """
        enrollment = PodService.get_student_pod(student)  # 2026-03-04: Find pod
        session = None  # 2026-03-04: Session may not exist
        if enrollment:
            session = (
                StudentSession.objects
                .filter(pod_enrollment=enrollment, is_active=True)
                .order_by('-session_start')
                .first()
            )

        # 2026-03-04: Compute escalation count for this student today
        from django.utils.timezone import now  # 2026-03-04: Local import
        today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
        prior_count = AttentionEvent.objects.filter(
            student=student,
            escalated=True,
            detected_at__gte=today_start,
        ).count()

        event = AttentionEvent.objects.create(  # 2026-03-04: Create event
            student=student,
            session=session,
            event_type=event_type,
            ai_response=ai_response,
            escalated=escalated,
            escalation_count=prior_count + (1 if escalated else 0),
        )

        # 2026-03-04: Update session attention score based on event type
        if session:
            score_penalty = {  # 2026-03-04: Penalty per event type
                'not_visible': 0.3,
                'not_looking': 0.2,
                'sleeping': 0.5,
                'inactive': 0.2,
            }.get(event_type, 0.2)
            session.attention_score = max(0.0, session.attention_score - score_penalty)
            session.save(update_fields=['attention_score'])

        return {'success': True, 'event_id': str(event.id)}  # 2026-03-04: Return


class AlertService:
    """
    2026-03-04: Parent and monitor alert dispatch service.

    Uses the existing OTP/WhatsApp provider pattern for parent notifications.
    In dev mode (mock provider), alerts are logged to console.
    In prod, swap OTP_PROVIDER to 'twilio' to send real WhatsApp messages.
    """

    # 2026-03-04: Alert type → human-readable description
    ALERT_MESSAGES = {
        'not_present': '{name} has not been seen on camera for more than 2 minutes.',
        'not_focusing': '{name} has been distracted for several minutes.',
        'sleeping': '{name} appears to be sleeping during the lesson.',
        'reteach_needed': '{name} is struggling with this topic and will revisit it.',
        'help_request': '{name} pressed the "Need Help" button during their lesson.',
    }

    @staticmethod
    def send_parent_alert(student, alert_type, custom_message=None):
        """
        2026-03-04: Send a WhatsApp notification to the student's parent.

        In dev (mock provider): logs to console only.
        In prod: dispatches via Twilio/Gupshup.

        Args:
            student: Student model instance.
            alert_type: One of the ALERT_MESSAGES keys.
            custom_message: Override message text (optional).

        Returns:
            dict: {success, alert_id}
        """
        # 2026-03-04: Build message text
        template = AlertService.ALERT_MESSAGES.get(
            alert_type,
            '{name} needs attention during their BabySteps session.',
        )
        message = custom_message or template.format(name=student.full_name)

        # 2026-03-04: Record alert in database
        alert = MonitorAlert.objects.create(  # 2026-03-04: Persist
            student=student,
            alert_type='parent_alert',
            message=message,
        )

        # 2026-03-04: Dispatch via WhatsApp provider (mock in dev)
        try:
            parent = student.parent  # 2026-03-04: Get parent
            phone = parent.phone  # 2026-03-04: Parent's phone
            AlertService._dispatch_whatsapp(phone, message)  # 2026-03-04: Send
        except Exception as exc:  # 2026-03-04: Parent not found or provider error
            logger.warning(f"Alert dispatch failed for {student.full_name}: {exc}")

        logger.info(  # 2026-03-04: Log alert
            f"[ALERT:{alert_type}] {student.full_name} → {message}"
        )
        return {'success': True, 'alert_id': str(alert.id)}  # 2026-03-04: Return

    @staticmethod
    def _dispatch_whatsapp(phone, message):
        """
        2026-03-04: Dispatch a WhatsApp message via the OTP provider factory.

        Re-uses OTPFactory (mock/twilio) for transport — same pattern as OTP SMS.

        Args:
            phone: Recipient phone number (e.g. '+919876543210').
            message: Message text to send.
        """
        from services.auth_service.otp_providers.factory import OTPFactory  # 2026-03-04: Factory
        provider = OTPFactory.get_provider()  # 2026-03-04: Get configured provider
        # 2026-03-04: The mock provider logs; Twilio provider sends real WhatsApp
        provider.send_otp(phone, message)  # 2026-03-04: Dispatch (message serves as OTP text)
        logger.info(f"WhatsApp alert dispatched to {phone}")  # 2026-03-04: Log

    @staticmethod
    def create_help_request(student, message=None):
        """
        2026-03-04: Record a student help request and notify monitor.

        Args:
            student: Student model instance.
            message: Optional custom message from student.

        Returns:
            dict: {success, alert_id}
        """
        msg = message or f"{student.full_name} needs help with their current lesson."
        alert = MonitorAlert.objects.create(  # 2026-03-04: Record alert
            student=student,
            alert_type='help_request',
            message=msg,
        )
        logger.info(f"[HELP REQUEST] {student.full_name}: {msg}")  # 2026-03-04: Log
        return {'success': True, 'alert_id': str(alert.id)}  # 2026-03-04: Return

    @staticmethod
    def get_unresolved_alerts():
        """
        2026-03-04: Return all unresolved alerts across all students.

        Returns:
            QuerySet[MonitorAlert]: Unresolved alerts ordered newest first.
        """
        return MonitorAlert.objects.filter(  # 2026-03-04: Unresolved only
            is_resolved=False
        ).select_related('student').order_by('-created_at')

    @staticmethod
    def resolve_alert(alert_id):
        """
        2026-03-04: Mark an alert as resolved.

        Args:
            alert_id: Integer PK of the MonitorAlert.

        Returns:
            dict: {success} or {error}
        """
        try:
            alert = MonitorAlert.objects.get(id=int(alert_id))  # 2026-03-04: Lookup (integer PK)
        except (MonitorAlert.DoesNotExist, ValueError, TypeError):
            return {'success': False, 'error': 'Alert not found.'}
        alert.is_resolved = True  # 2026-03-04: Resolve
        alert.save(update_fields=['is_resolved'])  # 2026-03-04: Persist
        return {'success': True}  # 2026-03-04: Return
