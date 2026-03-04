"""
2026-03-04: AI Learning Gap Detection service (BS-MON).

Purpose:
    Monitors student answer patterns to detect when a student is stuck.
    Generates gentle diagnostic check-in questions via LLM when 2+
    consecutive wrong answers are detected. Flags concepts for re-teaching
    and resets the day to the teaching phase.

    LLM pattern: mirrors services/math_service/tutoring.py.
    Fallback: graceful plain-text response if LLM is unavailable.
"""

import logging  # 2026-03-04: Module logger

from services.llm_service import get_llm_provider, LLMError  # 2026-03-04: LLM factory

logger = logging.getLogger(__name__)  # 2026-03-04: Module logger


class AIMonitorService:
    """
    2026-03-04: AI monitoring service for learning gap detection.

    Hooks into the teaching engine to detect consecutive wrong answers
    and generate re-teaching interventions via the LLM.
    """

    # 2026-03-04: Minimum consecutive wrong answers before intervention
    WRONG_ANSWER_THRESHOLD = 2

    @staticmethod
    def check_student_progress(student, lesson_progress):
        """
        2026-03-04: Detect if a student is stuck based on recent answer patterns.

        Examines the last N PracticeResponse records. If 2+ consecutive wrong
        answers exist, triggers a check-in question via LLM.

        Args:
            student: Student model instance.
            lesson_progress: StudentLessonProgress instance (current lesson).

        Returns:
            dict: {stuck: bool, checkin_question: str | None, concept: str | None}
        """
        from services.teaching_engine.models import (  # 2026-03-04: Local import (avoid circular)
            PracticeResponse, PracticeSession,
        )

        # 2026-03-04: Find the most recent practice session for this lesson
        practice_session = PracticeSession.objects.filter(
            student=student,
            lesson_id=lesson_progress.lesson_id,
        ).order_by('-started_at').first()

        if not practice_session:  # 2026-03-04: No practice yet
            return {'stuck': False, 'checkin_question': None, 'concept': None}

        # 2026-03-04: Get the last 3 responses (newest first)
        recent = PracticeResponse.objects.filter(
            session=practice_session,
        ).order_by('-answered_at')[:3]

        if len(recent) < 2:  # 2026-03-04: Not enough data
            return {'stuck': False, 'checkin_question': None, 'concept': None}

        # 2026-03-04: Count consecutive wrong answers from the most recent
        consecutive_wrong = 0
        for response in recent:  # 2026-03-04: Iterate newest first
            if not response.is_correct:
                consecutive_wrong += 1  # 2026-03-04: Wrong — keep counting
            else:
                break  # 2026-03-04: Hit a correct answer — stop

        if consecutive_wrong < AIMonitorService.WRONG_ANSWER_THRESHOLD:  # 2026-03-04: Not stuck
            return {'stuck': False, 'checkin_question': None, 'concept': None}

        # 2026-03-04: Student is stuck — generate a check-in question
        concept = lesson_progress.lesson.title if lesson_progress.lesson else 'this concept'
        question = AIMonitorService.generate_checkin_question(student, concept)

        logger.info(  # 2026-03-04: Log intervention
            f"Student {student.full_name} stuck on '{concept}' "
            f"({consecutive_wrong} wrong answers) — check-in triggered"
        )

        return {  # 2026-03-04: Return intervention
            'stuck': True,
            'checkin_question': question,
            'concept': concept,
            'consecutive_wrong': consecutive_wrong,
        }

    @staticmethod
    def generate_checkin_question(student, concept):
        """
        2026-03-04: Generate a gentle diagnostic question via LLM.

        The LLM asks a simple diagnostic question to find where the student
        got confused. Falls back to a safe template if LLM is unavailable.

        Args:
            student: Student model instance.
            concept: Name of the concept the student is stuck on.

        Returns:
            str: A gentle check-in question for the student.
        """
        prompt = (  # 2026-03-04: LLM prompt
            f"A student named {student.full_name} (grade {getattr(student, 'grade', '?')}) "
            f"seems confused about '{concept}'. "
            "Please ask ONE gentle, simple diagnostic question to help find "
            "where they got lost. Use very simple language. Be encouraging. "
            "Do not give away the answer. Reply with just the question — "
            "no preamble, no explanation."
        )

        try:
            llm = get_llm_provider()  # 2026-03-04: Get configured LLM
            response = llm.chat(  # 2026-03-04: Generate question via factory-provided LLM
                message=prompt,
                system_prompt=(
                    "You are a kind AI tutor for Indian school students. "
                    "You speak in simple, warm language. Keep responses very short."
                ),
            )
            question = response.text.strip()  # 2026-03-04: Extract text from LLMResponse
            logger.info(f"LLM check-in question for {student.full_name}: {question}")
            return question  # 2026-03-04: Return LLM question

        except (LLMError, Exception) as exc:  # 2026-03-04: LLM unavailable
            logger.warning(f"LLM check-in failed ({exc}) — using fallback")
            return (  # 2026-03-04: Safe fallback
                f"Hey {student.full_name}! Let's figure this out together. "
                f"Can you tell me what part of '{concept}' feels confusing?"
            )

    @staticmethod
    def flag_for_reteach(student, concept, day_progress):
        """
        2026-03-04: Mark a concept for re-teaching and reset day to teaching phase.

        Sets DayProgress.status to 'revision' so the teaching engine re-serves
        the concept from the beginning on next load.

        Args:
            student: Student model instance.
            concept: Name of the concept to re-teach.
            day_progress: DayProgress model instance (the day to reset).

        Returns:
            dict: {success, message}
        """
        # 2026-03-04: Reset day to revision (will re-serve teaching content)
        day_progress.status = 'revision'  # 2026-03-04: Reset status
        day_progress.save(update_fields=['status'])  # 2026-03-04: Persist

        # 2026-03-04: Create a monitor alert for tracking
        from .models import MonitorAlert  # 2026-03-04: Local import
        from services.auth_service.models import Student as StudentModel  # 2026-03-04: Import
        MonitorAlert.objects.create(  # 2026-03-04: Record alert
            student=student,
            alert_type='monitor_flag',
            message=(
                f"{student.full_name} is being re-taught '{concept}' "
                f"(Day {day_progress.day_number} reset to revision)."
            ),
        )

        logger.info(  # 2026-03-04: Log reteach
            f"Re-teach triggered: {student.full_name} → '{concept}' "
            f"(day {day_progress.day_number} reset)"
        )

        return {  # 2026-03-04: Return result
            'success': True,
            'message': (
                f"No problem! Let me explain '{concept}' a different way. "
                "We'll go through it again together."
            ),
        }
