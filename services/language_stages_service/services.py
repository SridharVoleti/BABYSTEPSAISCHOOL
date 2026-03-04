"""
2026-03-02: Business logic for Language Stages Service (BS-LNG-005).

Purpose:
    Orchestrate Michel Thomas Stage 3 conversational practice:
    - List scenarios with unlock status for a student+language
    - Start a session (create DB record + AI opening turn via LLM)
    - Submit a student turn (LLM evaluate + LLM respond)
    - Complete a session (compute fluency stars, update progress)

LLM strategy:
    Two separate calls per student turn:
    1. Evaluation call → JSON with quality (0-100), grammar error, recast
    2. Response call   → AI's next line in the target language

    Both calls fall back gracefully on LLM error.
"""

import json  # 2026-03-02: JSON parsing
import logging  # 2026-03-02: Module logger
import math  # 2026-03-02: ceil()

from django.utils import timezone  # 2026-03-02: Timezone-aware now()
from rest_framework.exceptions import NotFound, ValidationError  # 2026-03-02: DRF errors

from services.read_along_service.language_registry import get_language  # 2026-03-02: Lang lookup
from .models import (  # 2026-03-02: Own models
    ConversationScenario, ConversationSession, ConversationTurn,
    StudentConversationProgress,
)

logger = logging.getLogger(__name__)  # 2026-03-02: Logger

# 2026-03-02: Fluency star thresholds (mean quality 0-100 → stars)
# quality < 20 → 1★, 20-39 → 2★, 40-59 → 3★, 60-79 → 4★, 80+ → 5★
_STAR_BRACKETS = [20, 40, 60, 80]

# 2026-03-02: Minimum prerequisite star rating to unlock next scenario
_UNLOCK_STAR_THRESHOLD = 2


def _quality_to_stars(mean_quality: float) -> int:
    """
    2026-03-02: Map mean quality (0-100) to 1-5 stars.

    Args:
        mean_quality: Average of student turn quality scores scaled to 0-100.

    Returns:
        int: 1-5 stars, or 0 if no quality data.
    """
    if mean_quality <= 0:
        return 0  # 2026-03-02: No turns → 0
    for stars, threshold in enumerate(_STAR_BRACKETS, start=1):
        if mean_quality < threshold:
            return stars
    return 5  # 2026-03-02: >= 80 → 5 stars


class ConversationService:
    """
    2026-03-02: Core service for conversational language practice (BS-LNG-005).
    """

    @classmethod
    def get_scenarios(cls, student, language_name: str) -> list:
        """
        2026-03-02: Return all 20 scenarios with unlock status and best stars.

        Args:
            student: Student model instance.
            language_name: Language name string (e.g. 'Hindi').

        Returns:
            list: Dicts with scenario info + is_unlocked + best_star_rating.

        Raises:
            ValidationError: If language_name is invalid.
        """
        lang_obj = get_language(language_name)  # 2026-03-02: Validate lang

        # 2026-03-02: Get or create progress record for this student+language
        progress, _ = StudentConversationProgress.objects.get_or_create(
            student=student,
            language=lang_obj,
        )
        best_stars = progress.best_star_by_scenario or {}  # 2026-03-02: Dict of scenario# → stars

        scenarios = ConversationScenario.objects.all()  # 2026-03-02: Ordered by number
        result = []
        for scenario in scenarios:
            is_unlocked = cls._is_unlocked(scenario, best_stars)
            result.append({
                'id': str(scenario.id),
                'scenario_number': scenario.scenario_number,
                'title': scenario.title,
                'ai_persona': scenario.ai_persona,
                'difficulty': scenario.difficulty,
                'min_turns': scenario.min_turns,
                'max_turns': scenario.max_turns,
                'unlock_after_scenario': scenario.unlock_after_scenario,
                'is_unlocked': is_unlocked,
                'best_star_rating': int(best_stars.get(str(scenario.scenario_number), 0)),
            })
        return result

    @classmethod
    def start_session(cls, student, language_name: str, scenario_id: str) -> dict:
        """
        2026-03-02: Create a ConversationSession and generate AI opening turn.

        Args:
            student: Student model instance.
            language_name: Target language name.
            scenario_id: UUID string of ConversationScenario.

        Returns:
            dict: session_id, scenario_title, ai_persona, opening_text, complexity_level.

        Raises:
            NotFound: If scenario not found.
            ValidationError: If language invalid or scenario locked.
        """
        lang_obj = get_language(language_name)  # 2026-03-02: Validate

        # 2026-03-02: Fetch scenario
        try:
            scenario = ConversationScenario.objects.get(id=scenario_id)
        except ConversationScenario.DoesNotExist:
            raise NotFound(f"Scenario '{scenario_id}' not found.")

        # 2026-03-02: Check unlock status
        progress, _ = StudentConversationProgress.objects.get_or_create(
            student=student, language=lang_obj
        )
        best_stars = progress.best_star_by_scenario or {}
        if not cls._is_unlocked(scenario, best_stars):
            raise ValidationError(
                f"Scenario '{scenario.title}' is locked. "
                f"Complete scenario {scenario.unlock_after_scenario} first."
            )

        # 2026-03-02: Determine complexity from student's existing sessions
        complexity = cls._determine_complexity(student, scenario)

        # 2026-03-02: Create session
        session = ConversationSession.objects.create(
            student=student,
            language=lang_obj,
            scenario=scenario,
            status='in_progress',
            complexity_level=complexity,
        )

        # 2026-03-02: Generate AI opening turn via LLM
        opening_text = cls._generate_opening(scenario, language_name)

        # 2026-03-02: Persist AI opening turn as turn 1
        ConversationTurn.objects.create(
            session=session,
            turn_number=1,
            role='ai',
            text=opening_text,
        )

        logger.info(
            "ConversationSession started: student=%s lang=%s scenario=%s session=%s",
            student.id, language_name, scenario.scenario_number, session.id,
        )

        return {
            'session_id': str(session.id),
            'scenario_title': scenario.title,
            'ai_persona': scenario.ai_persona,
            'opening_text': opening_text,
            'complexity_level': complexity,
        }

    @classmethod
    def submit_turn(
        cls,
        session_id: str,
        student,
        student_text: str,
        response_time_seconds: int = None,
    ) -> dict:
        """
        2026-03-02: Process a student's conversational turn.

        Steps:
        1. Validate session belongs to student and is in_progress.
        2. Save student ConversationTurn.
        3. LLM evaluation call → quality score (0-100) + recast suggestion.
        4. LLM response call  → AI's next line (in target language, with implicit recast).
        5. Save AI ConversationTurn.
        6. Check completion condition.

        Args:
            session_id: UUID string of ConversationSession.
            student: Student model instance.
            student_text: Student's conversational input.
            response_time_seconds: Optional typing/speaking time.

        Returns:
            dict: ai_response, turn_quality (0-1), recast_applied, is_complete, turn_number.

        Raises:
            NotFound: If session not found.
            ValidationError: If session already completed or not owned by student.
        """
        # 2026-03-02: Fetch and validate session
        try:
            session = ConversationSession.objects.select_related(
                'scenario', 'language', 'student'
            ).get(id=session_id)
        except ConversationSession.DoesNotExist:
            raise NotFound(f"Session '{session_id}' not found.")

        if session.student_id != student.id:
            raise ValidationError("You can only submit turns for your own sessions.")

        if session.status != 'in_progress':
            raise ValidationError(
                f"Session is already '{session.status}'. Cannot submit more turns."
            )

        # 2026-03-02: Determine next turn number (after the AI opening = turn 1)
        last_turn = session.turns.order_by('-turn_number').first()
        next_student_turn_number = (last_turn.turn_number + 1) if last_turn else 2
        next_ai_turn_number = next_student_turn_number + 1

        # 2026-03-02: Save student turn (quality set after LLM eval)
        student_turn = ConversationTurn.objects.create(
            session=session,
            turn_number=next_student_turn_number,
            role='student',
            text=student_text,
            response_time_seconds=response_time_seconds,
        )

        # 2026-03-02: LLM call 1 — evaluate student turn quality
        eval_result = cls._evaluate_turn(
            student_text,
            session.scenario,
            session.language.name,
            session.complexity_level,
        )
        quality_score_0_1 = eval_result['quality'] / 100.0  # 2026-03-02: Normalise
        recast_applied = bool(eval_result.get('recast'))

        # 2026-03-02: Update student turn with quality score
        student_turn.turn_quality_score = quality_score_0_1
        student_turn.recast_applied = recast_applied
        student_turn.save(update_fields=['turn_quality_score', 'recast_applied'])

        # 2026-03-02: LLM call 2 — generate AI response
        conversation_history = cls._build_history(session)
        ai_text = cls._generate_response(
            student_text,
            eval_result,
            session.scenario,
            session.language.name,
            conversation_history,
            session.complexity_level,
        )

        # 2026-03-02: Save AI response turn
        ConversationTurn.objects.create(
            session=session,
            turn_number=next_ai_turn_number,
            role='ai',
            text=ai_text,
        )

        # 2026-03-02: Increment student turn count
        session.turn_count += 1
        session.save(update_fields=['turn_count'])

        # 2026-03-02: Check completion: min_turns reached AND quality was acceptable
        is_complete = (
            session.turn_count >= session.scenario.min_turns
            and quality_score_0_1 >= 0.5
        )

        logger.info(
            "ConversationTurn submitted: session=%s student_turn=%d quality=%.2f recast=%s",
            session_id, next_student_turn_number, quality_score_0_1, recast_applied,
        )

        return {
            'ai_response': ai_text,
            'turn_quality': round(quality_score_0_1, 3),
            'recast_applied': recast_applied,
            'is_complete': is_complete,
            'turn_number': next_student_turn_number,
        }

    @classmethod
    def complete_session(cls, session_id: str, student) -> dict:
        """
        2026-03-02: End a conversation session and award fluency stars.

        Computes mean of all student turn quality scores → maps to 1-5 stars.
        Updates StudentConversationProgress.

        Args:
            session_id: UUID string of ConversationSession.
            student: Student model instance (for ownership check).

        Returns:
            dict: fluency_star_rating, turns_completed, summary.

        Raises:
            NotFound: If session not found.
            ValidationError: If session not owned by student or already closed.
        """
        try:
            session = ConversationSession.objects.select_related(
                'scenario', 'language', 'student'
            ).get(id=session_id)
        except ConversationSession.DoesNotExist:
            raise NotFound(f"Session '{session_id}' not found.")

        if session.student_id != student.id:
            raise ValidationError("You can only complete your own sessions.")

        if session.status != 'in_progress':
            raise ValidationError(f"Session is already '{session.status}'.")

        # 2026-03-02: Compute mean quality from student turns
        student_turns = session.turns.filter(
            role='student', turn_quality_score__isnull=False
        )
        qualities = [t.turn_quality_score for t in student_turns]
        mean_quality_0_1 = (sum(qualities) / len(qualities)) if qualities else 0.0
        mean_quality_100 = mean_quality_0_1 * 100.0

        fluency_stars = _quality_to_stars(mean_quality_100)

        # 2026-03-02: Update session
        session.status = 'completed'
        session.fluency_star_rating = fluency_stars
        session.completed_at = timezone.now()
        session.save()

        # 2026-03-02: Update StudentConversationProgress
        cls._update_progress(session, fluency_stars)

        summary = (
            f"Great conversation! You completed {session.turn_count} turn(s) "
            f"and earned {fluency_stars} star(s). Keep practising!"
        )

        logger.info(
            "ConversationSession completed: session=%s student=%s stars=%d",
            session_id, student.id, fluency_stars,
        )

        return {
            'fluency_star_rating': fluency_stars,
            'turns_completed': session.turn_count,
            'summary': summary,
        }

    @classmethod
    def get_progress(cls, student, language_name: str) -> dict:
        """
        2026-03-02: Return conversation progress for a student and language.

        Args:
            student: Student model instance.
            language_name: Language name string.

        Returns:
            dict: scenarios_completed, total_turns, streak, best_stars_by_scenario.
        """
        lang_obj = get_language(language_name)  # 2026-03-02: Validate
        progress, _ = StudentConversationProgress.objects.get_or_create(
            student=student, language=lang_obj
        )
        return {
            'language': language_name,
            'scenarios_completed': progress.scenarios_completed,
            'total_turns': progress.total_turns,
            'current_streak_days': progress.current_streak_days,
            'best_star_by_scenario': progress.best_star_by_scenario,
            'last_session_date': (
                str(progress.last_session_date) if progress.last_session_date else None
            ),
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _is_unlocked(scenario, best_stars: dict) -> bool:
        """
        2026-03-02: Check if a scenario is unlocked for a given student.

        Args:
            scenario: ConversationScenario instance.
            best_stars: Dict mapping str(scenario_number) → int star rating.

        Returns:
            bool: True if scenario is accessible.
        """
        prereq = scenario.unlock_after_scenario  # 2026-03-02: Prerequisite
        if prereq is None:
            return True  # 2026-03-02: No prerequisite
        prereq_stars = best_stars.get(str(prereq), 0)
        return int(prereq_stars) >= _UNLOCK_STAR_THRESHOLD  # 2026-03-02: Gate

    @staticmethod
    def _determine_complexity(student, scenario) -> str:
        """
        2026-03-02: Pick complexity tier from student's history in this scenario.

        Uses the scenario's own difficulty as default; adapts based on
        prior best star ratings if student has played this scenario before.

        Args:
            student: Student model instance.
            scenario: ConversationScenario instance.

        Returns:
            str: 'beginner', 'intermediate', or 'advanced'.
        """
        best_prior = (
            ConversationSession.objects
            .filter(student=student, scenario=scenario, status='completed')
            .order_by('-fluency_star_rating')
            .values_list('fluency_star_rating', flat=True)
            .first()
        )
        if best_prior is None:
            return scenario.difficulty  # 2026-03-02: First attempt → scenario default
        if best_prior >= 4:
            return 'advanced'  # 2026-03-02: High performer
        if best_prior >= 2:
            return 'intermediate'
        return 'beginner'

    @staticmethod
    def _generate_opening(scenario, language_name: str) -> str:
        """
        2026-03-02: Generate AI opening turn using LLM.

        Fills {target_language} placeholder in the template and prompts the LLM.
        Falls back to the filled template on LLM failure.

        Args:
            scenario: ConversationScenario instance.
            language_name: Target language name.

        Returns:
            str: AI's opening line.
        """
        filled_template = scenario.opening_prompt_template.replace(
            '{target_language}', language_name
        )
        try:
            from services.llm_service import get_llm_provider  # 2026-03-04: Factory pattern

            system_prompt = (
                f"You are a {scenario.ai_persona} in a {language_name} conversation "
                f"practice session for a school student. "
                f"Context: {scenario.context_description} "
                f"Keep your responses to 1-2 sentences and use simple {language_name} "
                f"that a beginner can understand. "
                f"You may include English in parentheses if needed."
            )
            llm = get_llm_provider()  # 2026-03-04: Get configured provider (Ollama/OpenAI/Anthropic)
            response = llm.chat(  # 2026-03-04: LLMResponse object
                message=filled_template,
                system_prompt=system_prompt,
                temperature=0.7,
            )
            return response.text.strip() if response.text else filled_template  # 2026-03-04: .text attr
        except Exception as exc:  # 2026-03-02: LLM failure — use template directly
            logger.warning("LLM opening generation failed: %s", exc)
            return filled_template

    @staticmethod
    def _evaluate_turn(
        student_text: str,
        scenario,
        language_name: str,
        complexity: str,
    ) -> dict:
        """
        2026-03-02: LLM evaluation call for a student's conversational turn.

        Requests JSON with quality (0-100), grammar_error, and recast suggestion.

        Args:
            student_text: What the student said.
            scenario: ConversationScenario instance.
            language_name: Target language name.
            complexity: Current complexity tier.

        Returns:
            dict: {'quality': int 0-100, 'grammar_error': str|None, 'recast': str|None}
        """
        try:
            from services.llm_service import get_llm_provider  # 2026-03-04: Factory pattern

            eval_prompt = (
                f'Evaluate this student response in {language_name} for a '
                f'{complexity} {scenario.title} role-play scenario. '
                f'Student said: "{student_text}". '
                f'Return ONLY valid JSON with exactly these keys: '
                f'{{"quality": <integer 0-100>, '
                f'"grammar_error": <string or null>, '
                f'"recast": <corrected form string or null>}}'
            )
            llm = get_llm_provider()  # 2026-03-04: Get configured provider
            response = llm.chat(  # 2026-03-04: LLMResponse object
                message=eval_prompt,
                system_prompt=(
                    "You are a language teacher evaluating student responses. "
                    "Always respond with valid JSON only. No explanation."
                ),
                temperature=0.3,
            )
            # 2026-03-04: Parse .text attr from LLMResponse; fall back on parse error
            parsed = json.loads(response.text)
            quality = max(0, min(100, int(parsed.get('quality', 50))))
            return {
                'quality': quality,
                'grammar_error': parsed.get('grammar_error'),
                'recast': parsed.get('recast'),
            }
        except Exception as exc:  # 2026-03-02: LLM or parse failure → neutral score
            logger.warning("LLM turn evaluation failed: %s", exc)
            return {'quality': 50, 'grammar_error': None, 'recast': None}

    @staticmethod
    def _generate_response(
        student_text: str,
        eval_result: dict,
        scenario,
        language_name: str,
        history: list,
        complexity: str,
    ) -> str:
        """
        2026-03-02: LLM response call — generate AI's next conversational line.

        If a recast is needed, the AI naturally incorporates the correct form.
        Falls back to a scripted encouragement on LLM failure.

        Args:
            student_text: What the student said.
            eval_result: Dict from _evaluate_turn.
            scenario: ConversationScenario instance.
            language_name: Target language name.
            history: List of prior turn dicts.
            complexity: Complexity tier.

        Returns:
            str: AI's response in target language.
        """
        fallback = "Good try! Please continue our conversation."  # 2026-03-02: Fallback
        try:
            from services.llm_service import get_llm_provider  # 2026-03-04: Factory pattern

            recast = eval_result.get('recast')
            recast_instruction = (
                f" The student made an error. Naturally use the correct form "
                f'"{recast}" in your response without explicitly correcting them.'
                if recast else ""
            )

            history_text = "\n".join(
                f"{t['role'].capitalize()}: {t['text']}" for t in history[-6:]
            )  # 2026-03-02: Last 6 turns for context

            system_prompt = (
                f"You are a {scenario.ai_persona} in a {language_name} conversation "
                f"practice session. Context: {scenario.context_description} "
                f"Respond naturally in {language_name} at {complexity} level. "
                f"Keep response to 1-2 sentences.{recast_instruction}"
            )
            user_message = (
                f"Conversation so far:\n{history_text}\n\n"
                f"Student just said: {student_text}\n"
                f"Respond as the {scenario.ai_persona}:"
            )
            llm = get_llm_provider()  # 2026-03-04: Get configured provider
            response = llm.chat(  # 2026-03-04: LLMResponse object
                message=user_message,
                system_prompt=system_prompt,
                temperature=0.7,
            )
            return response.text.strip() if response.text else fallback  # 2026-03-04: .text attr
        except Exception as exc:  # 2026-03-02: LLM failure — scripted encouragement
            logger.warning("LLM response generation failed: %s", exc)
            return fallback

    @staticmethod
    def _build_history(session) -> list:
        """
        2026-03-02: Build conversation history list for LLM context.

        Args:
            session: ConversationSession instance.

        Returns:
            list: Dicts with 'role' and 'text'.
        """
        turns = session.turns.order_by('turn_number')
        return [{'role': t.role, 'text': t.text} for t in turns]

    @staticmethod
    def _update_progress(session, fluency_stars: int) -> None:
        """
        2026-03-02: Update StudentConversationProgress after session completion.

        Args:
            session: Completed ConversationSession instance.
            fluency_stars: Star rating awarded.
        """
        progress, _ = StudentConversationProgress.objects.get_or_create(
            student=session.student,
            language=session.language,
        )
        scenario_key = str(session.scenario.scenario_number)  # 2026-03-02: JSON key
        best_stars = progress.best_star_by_scenario or {}

        # 2026-03-02: Update best_star if improved
        is_new_best = fluency_stars > int(best_stars.get(scenario_key, 0))
        if is_new_best:
            best_stars[scenario_key] = fluency_stars
            progress.best_star_by_scenario = best_stars
            if fluency_stars >= _UNLOCK_STAR_THRESHOLD:
                progress.scenarios_completed = len(
                    [v for v in best_stars.values() if int(v) >= _UNLOCK_STAR_THRESHOLD]
                )

        # 2026-03-02: Accumulate turn count
        progress.total_turns += session.turn_count

        # 2026-03-02: Update streak
        today = timezone.now().date()
        if progress.last_session_date:
            delta = (today - progress.last_session_date).days
            if delta == 0:
                pass  # 2026-03-02: Same day, no change
            elif delta == 1:
                progress.current_streak_days += 1  # 2026-03-02: Consecutive day
            else:
                progress.current_streak_days = 1  # 2026-03-02: Streak broken
        else:
            progress.current_streak_days = 1  # 2026-03-02: First ever session

        progress.last_session_date = today
        progress.save()
