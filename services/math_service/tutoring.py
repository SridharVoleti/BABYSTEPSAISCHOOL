"""
2026-03-02: AI Math Tutor teaching service (BS-AMT-001).

Purpose:
    Delivers the AI teaching phase BEFORE practice problems begin.
    The tutor explains the concept using the day's teaching_summary and
    worked_examples from the JSON, then handles Socratic follow-up questions
    from the student.

    Ground-Truth Anchor: The LLM is given the pre-authored teaching_summary
    and worked_examples as authoritative content. It explains those — it
    does NOT invent new maths. This is the same Ground-Truth RAG pattern
    used in the evaluator.

    Fallback: If the LLM is unavailable, a structured plain-text message
    is built directly from the JSON fields — zero silent failures.
"""

import logging  # 2026-03-02: Module logger

from django.utils import timezone  # 2026-03-02: Timezone-aware timestamps

from services.llm_service import get_llm_provider, LLMError  # 2026-03-02: LLM factory
from .content_loader import MathContentLoader  # 2026-03-02: JSON content loader
from .models import MathSession, MathTutoringSession  # 2026-03-02: Models

logger = logging.getLogger(__name__)  # 2026-03-02: Module logger

# 2026-03-02: IQ level pacing instructions for the tutor persona
_PACING = {
    'foundation': (
        'This student needs extra support. Use the simplest possible words. '
        'Speak in very short sentences. Repeat the key idea twice. '
        'Give lots of encouragement ("Great!", "Well done!"). '
        'Use concrete everyday examples (mangoes, fingers, stars).'
    ),
    'standard': (
        'This student is at grade level. Use clear, age-appropriate language. '
        'Explain the concept once with one worked example. Be encouraging.'
    ),
    'advanced': (
        'This student is advanced. Be concise. After explaining, challenge '
        'them with a follow-up thinking question ("Can you figure out why?").'
    ),
}

# 2026-03-02: Content safety — keywords that must never appear in tutor output
_BLOCKED = [
    'violence', 'weapon', 'drug', 'alcohol', 'gambling',
    'explicit', 'hatred', 'suicide',
]


class MathTutoringService:
    """
    2026-03-02: AI Math Tutor for the teaching phase of a math session.

    Generates an opening teaching message grounded in the day's JSON content,
    then handles student questions using Socratic dialogue. Never invents
    maths — always anchors to the pre-authored teaching_summary and
    worked_examples.
    """

    # 2026-03-02: Maximum student messages per teaching session (anti-spam)
    MAX_STUDENT_MESSAGES = 10

    @classmethod
    def _build_system_prompt(
        cls,
        character: str,
        iq_level: str,
        topic: str,
        day_title: str,
        learning_objectives: list,
        teaching_summary: str,
        worked_examples: list,
    ) -> str:
        """
        2026-03-02: Build the teaching system prompt anchored to JSON content.

        The prompt instructs the LLM to teach using the pre-authored material,
        not to invent maths. This is the Ground-Truth Anchor principle.

        Args:
            character: Tutor persona name, e.g. 'Bunny the Counter'.
            iq_level: Student's IQ level for pacing.
            topic: Lesson topic, e.g. 'Counting 1-10'.
            day_title: Today's day title, e.g. 'Numbers 1-5'.
            learning_objectives: List of learning objectives.
            teaching_summary: Pre-authored explanation from JSON.
            worked_examples: List of {problem, solution_steps, answer} dicts.

        Returns:
            str: System prompt for the LLM.
        """
        pacing = _PACING.get(iq_level, _PACING['standard'])  # 2026-03-02: Pacing guide

        # 2026-03-02: Format learning objectives
        objectives_text = '\n'.join(
            f'  • {obj}' for obj in learning_objectives
        ) if learning_objectives else '  • Understand today\'s concept'

        # 2026-03-02: Format worked examples
        examples_text = ''
        for i, ex in enumerate(worked_examples, 1):  # 2026-03-02: Each example
            steps = ex.get('solution_steps', [])  # 2026-03-02: Steps list
            steps_text = '\n'.join(
                f'    Step {j + 1}: {s}' for j, s in enumerate(steps)
            )
            examples_text += (
                f'\n  Example {i}:\n'
                f'    Problem: {ex.get("problem", "")}\n'
                f'{steps_text}\n'
                f'    Answer: {ex.get("answer", "")}\n'
            )

        prompt = (
            f'You are {character}, a friendly AI maths teacher at BabySteps Digital School.\n\n'
            f'TODAY\'S LESSON: {topic} — {day_title}\n\n'
            f'LEARNING OBJECTIVES:\n{objectives_text}\n\n'
            f'TEACHING SUMMARY (this is the concept you must teach):\n'
            f'  {teaching_summary}\n\n'
            f'WORKED EXAMPLES (walk through these step by step):\n'
            f'{examples_text}\n'
            f'STUDENT LEVEL: {pacing}\n\n'
            f'YOUR RULES:\n'
            f'1. Keep every message SHORT — 3-5 sentences maximum.\n'
            f'2. Teach ONLY using the Teaching Summary and Worked Examples above.\n'
            f'   Do NOT invent new maths or examples not listed above.\n'
            f'3. Use Socratic method: ask ONE guiding question after explaining.\n'
            f'4. When student shows understanding, encourage them to click '
            f'   "I\'m Ready to Practice!".\n'
            f'5. If student asks something off-topic, gently bring them back.\n'
            f'6. Never reveal the practice problem answers.\n'
            f'7. Be warm, patient, and encouraging at all times.\n'
        )

        return prompt  # 2026-03-02: Return complete system prompt

    @classmethod
    def _build_fallback_message(
        cls,
        character: str,
        day_title: str,
        teaching_summary: str,
        worked_examples: list,
    ) -> str:
        """
        2026-03-02: Build a structured teaching message from JSON without LLM.

        Used when the LLM is unavailable. Guarantees the student always sees
        the teaching content — no silent failures.

        Args:
            character: Tutor name.
            day_title: Today's day title.
            teaching_summary: Pre-authored explanation.
            worked_examples: List of example dicts.

        Returns:
            str: Plain-text teaching message.
        """
        parts = [  # 2026-03-02: Build message parts
            f"Hello! I'm {character}, your maths teacher for today. 😊",
            f"Today we're learning: {day_title}.",
            f"\n{teaching_summary}",
        ]

        if worked_examples:  # 2026-03-02: Add first example
            ex = worked_examples[0]  # 2026-03-02: Use first example
            parts.append(f"\nLet me show you an example!")
            parts.append(f"Problem: {ex.get('problem', '')}")
            for j, step in enumerate(ex.get('solution_steps', []), 1):  # 2026-03-02: Steps
                parts.append(f"Step {j}: {step}")
            parts.append(f"Answer: {ex.get('answer', '')}")

        parts.append(  # 2026-03-02: Call to action
            "\nWhen you feel ready, click 'I'm Ready to Practice!' to start the problems."
        )

        return '\n'.join(parts)  # 2026-03-02: Join all parts

    @classmethod
    def _is_safe(cls, text: str) -> bool:
        """
        2026-03-02: Basic safety check on LLM output.

        Args:
            text: Response text to check.

        Returns:
            bool: True if no blocked keywords found.
        """
        lower = text.lower()  # 2026-03-02: Case-insensitive
        return not any(kw in lower for kw in _BLOCKED)  # 2026-03-02: Check all

    @classmethod
    def get_or_create_session(cls, math_session: MathSession) -> dict:
        """
        2026-03-02: Get the existing tutoring session or create a new one.

        On creation, generates the AI tutor's opening teaching message
        using the day's JSON content as the anchor. Idempotent — safe
        to call multiple times (returns existing session on subsequent calls).

        Args:
            math_session: The MathSession this teaching session belongs to.

        Returns:
            dict: {success, session_id, teaching_complete, messages, character}
        """
        # 2026-03-02: Check for existing session
        existing = MathTutoringSession.objects.filter(
            math_session=math_session
        ).first()

        if existing:  # 2026-03-02: Return existing session as-is
            return cls._session_to_dict(existing, math_session)

        # 2026-03-02: Load day content from JSON
        try:
            day_data = MathContentLoader.get_day_content(
                math_session.lesson.content_json_path,
                math_session.day_number,
            )
        except (FileNotFoundError, ValueError) as exc:  # 2026-03-02: JSON error
            logger.error('MathTutoringService: content load failed: %s', exc)
            return {'success': False, 'error': 'Could not load lesson content.'}

        lesson_data = MathContentLoader.load_lesson(  # 2026-03-02: Full lesson for meta
            math_session.lesson.content_json_path
        )

        character = lesson_data.get('character', 'Maths Tutor')  # 2026-03-02: Persona name
        topic = lesson_data.get('topic', 'Mathematics')  # 2026-03-02: Topic
        learning_objectives = lesson_data.get('learning_objectives', [])  # 2026-03-02: Objectives
        day_title = day_data.get('title', f'Day {math_session.day_number}')  # 2026-03-02: Day title
        teaching_summary = day_data.get('teaching_summary', '')  # 2026-03-02: Core concept
        worked_examples = day_data.get('worked_examples', [])  # 2026-03-02: Examples

        # 2026-03-02: Generate opening message via LLM
        opening_message = cls._generate_opening(
            character=character,
            iq_level=math_session.iq_level,
            topic=topic,
            day_title=day_title,
            learning_objectives=learning_objectives,
            teaching_summary=teaching_summary,
            worked_examples=worked_examples,
        )

        # 2026-03-02: Create tutoring session with opening message
        tutoring = MathTutoringSession.objects.create(
            math_session=math_session,
            messages=[{
                'role': 'tutor',
                'text': opening_message,
                'ts': timezone.now().isoformat(),
            }],
            teaching_complete=False,
        )

        return cls._session_to_dict(tutoring, math_session)  # 2026-03-02: Return

    @classmethod
    def _generate_opening(
        cls,
        character: str,
        iq_level: str,
        topic: str,
        day_title: str,
        learning_objectives: list,
        teaching_summary: str,
        worked_examples: list,
    ) -> str:
        """
        2026-03-02: Generate the AI tutor's opening teaching message via LLM.

        The LLM is given the pre-authored content and asked to present it
        in a warm, child-friendly way. Falls back to a structured plain-text
        message if the LLM fails.

        Args:
            All fields from the day's JSON content.

        Returns:
            str: Opening teaching message text.
        """
        system_prompt = cls._build_system_prompt(  # 2026-03-02: Build persona prompt
            character=character,
            iq_level=iq_level,
            topic=topic,
            day_title=day_title,
            learning_objectives=learning_objectives,
            teaching_summary=teaching_summary,
            worked_examples=worked_examples,
        )

        # 2026-03-02: Ask LLM to generate the opening teaching message
        opening_prompt = (
            f'Start teaching {day_title}. '
            f'Greet the student warmly, introduce what you will learn today, '
            f'then explain the concept using the Teaching Summary. '
            f'Then walk through the first Worked Example step by step. '
            f'End with one simple checking question.'
        )

        try:
            llm = get_llm_provider()  # 2026-03-02: Get LLM provider
            response = llm.chat(  # 2026-03-02: Generate opening
                message=opening_prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=350,
            )
            text = response.text.strip()  # 2026-03-02: Get text

            if text and cls._is_safe(text):  # 2026-03-02: Safety check
                return text  # 2026-03-02: Return LLM message

            logger.warning('MathTutoringService: LLM response failed safety check')

        except (LLMError, Exception) as exc:  # 2026-03-02: LLM unavailable
            logger.warning('MathTutoringService: LLM unavailable, using fallback: %s', exc)

        # 2026-03-02: Fallback — build from JSON directly
        return cls._build_fallback_message(
            character=character,
            day_title=day_title,
            teaching_summary=teaching_summary,
            worked_examples=worked_examples,
        )

    @classmethod
    def chat(cls, math_session: MathSession, student_message: str) -> dict:
        """
        2026-03-02: Handle a student message during the teaching phase.

        Appends the student's message to the conversation, calls the LLM
        with the full conversation history as context (Socratic response),
        and appends the tutor's reply. Falls back to an encouraging nudge
        if the LLM fails.

        Args:
            math_session: The MathSession (used to load tutoring session + content).
            student_message: The student's question or response text.

        Returns:
            dict: {success, reply, teaching_complete, messages, character}
        """
        tutoring = MathTutoringSession.objects.filter(  # 2026-03-02: Get session
            math_session=math_session
        ).first()

        if not tutoring:  # 2026-03-02: Session must exist
            return {'success': False, 'error': 'Teaching session not started.'}

        if tutoring.teaching_complete:  # 2026-03-02: Already done
            return {'success': False, 'error': 'Teaching phase already completed.'}

        # 2026-03-02: Enforce message limit (anti-spam)
        student_msgs = sum(
            1 for m in tutoring.messages if m.get('role') == 'student'
        )
        if student_msgs >= cls.MAX_STUDENT_MESSAGES:  # 2026-03-02: Over limit
            return {
                'success': False,
                'error': 'Too many messages. Please click "Ready to Practice!".',
            }

        # 2026-03-02: Load lesson content for system prompt
        try:
            lesson_data = MathContentLoader.load_lesson(
                math_session.lesson.content_json_path
            )
            day_data = MathContentLoader.get_day_content(
                math_session.lesson.content_json_path,
                math_session.day_number,
            )
        except (FileNotFoundError, ValueError) as exc:  # 2026-03-02: Content error
            logger.error('MathTutoringService.chat: content load failed: %s', exc)
            lesson_data, day_data = {}, {}

        character = lesson_data.get('character', 'Maths Tutor')  # 2026-03-02: Persona
        system_prompt = cls._build_system_prompt(  # 2026-03-02: Rebuild prompt
            character=character,
            iq_level=math_session.iq_level,
            topic=lesson_data.get('topic', 'Mathematics'),
            day_title=day_data.get('title', f'Day {math_session.day_number}'),
            learning_objectives=lesson_data.get('learning_objectives', []),
            teaching_summary=day_data.get('teaching_summary', ''),
            worked_examples=day_data.get('worked_examples', []),
        )

        # 2026-03-02: Append student message to history
        messages = list(tutoring.messages)  # 2026-03-02: Copy
        messages.append({
            'role': 'student',
            'text': student_message,
            'ts': timezone.now().isoformat(),
        })

        # 2026-03-02: Build context string from recent history (last 6 messages)
        history = messages[-6:] if len(messages) > 6 else messages  # 2026-03-02: Recent
        history_text = '\n'.join(
            f"{'Tutor' if m['role'] == 'tutor' else 'Student'}: {m['text']}"
            for m in history[:-1]  # 2026-03-02: Exclude the just-added student msg
        )
        full_message = (  # 2026-03-02: Combine context + new message
            f'[CONVERSATION SO FAR]\n{history_text}\n\n'
            f'[STUDENT SAYS NOW]: {student_message}'
            if history_text else student_message
        )

        # 2026-03-02: Get LLM response (Socratic reply)
        try:
            llm = get_llm_provider()  # 2026-03-02: Get provider
            response = llm.chat(  # 2026-03-02: Generate reply
                message=full_message,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=200,
            )
            reply = response.text.strip()  # 2026-03-02: Extract

            if not reply or not cls._is_safe(reply):  # 2026-03-02: Safety
                logger.warning('MathTutoringService.chat: unsafe/empty LLM reply')
                reply = cls._safe_fallback_reply(character)  # 2026-03-02: Safe fallback

        except (LLMError, Exception) as exc:  # 2026-03-02: LLM error
            logger.warning('MathTutoringService.chat: LLM error: %s', exc)
            reply = cls._safe_fallback_reply(character)  # 2026-03-02: Fallback

        # 2026-03-02: Append tutor reply
        messages.append({
            'role': 'tutor',
            'text': reply,
            'ts': timezone.now().isoformat(),
        })

        tutoring.messages = messages  # 2026-03-02: Save updated messages
        tutoring.save(update_fields=['messages', 'updated_at'])  # 2026-03-02: Persist

        return {  # 2026-03-02: Return response
            'success': True,
            'reply': reply,
            'character': character,
            'teaching_complete': tutoring.teaching_complete,
            'messages': messages,
        }

    @classmethod
    def complete_teaching(cls, math_session: MathSession) -> dict:
        """
        2026-03-02: Mark the teaching phase as complete.

        Called when the student clicks "I'm Ready to Practice!".
        The tutoring session is flagged complete; the frontend then
        transitions to the practice phase.

        Args:
            math_session: The MathSession whose teaching to complete.

        Returns:
            dict: {success, teaching_complete: True}
        """
        tutoring = MathTutoringSession.objects.filter(  # 2026-03-02: Get session
            math_session=math_session
        ).first()

        if not tutoring:  # 2026-03-02: Must exist
            return {'success': False, 'error': 'Teaching session not found.'}

        tutoring.teaching_complete = True  # 2026-03-02: Mark complete
        tutoring.save(update_fields=['teaching_complete', 'updated_at'])  # 2026-03-02: Persist

        return {'success': True, 'teaching_complete': True}  # 2026-03-02: Return

    @classmethod
    def _safe_fallback_reply(cls, character: str) -> str:
        """
        2026-03-02: Return a safe encouragement when LLM fails during chat.

        Args:
            character: Tutor name.

        Returns:
            str: Encouraging fallback message.
        """
        return (  # 2026-03-02: Generic encouraging reply
            f"That's a great question! Let me think... "
            f"Look back at the example I showed you — does that help? "
            f"When you're ready, click 'I'm Ready to Practice!'"
        )

    @classmethod
    def _session_to_dict(
        cls,
        tutoring: MathTutoringSession,
        math_session: MathSession,
    ) -> dict:
        """
        2026-03-02: Serialise a MathTutoringSession to a response dict.

        Args:
            tutoring: MathTutoringSession instance.
            math_session: Linked MathSession (used to load character name).

        Returns:
            dict: Response dict for the API view.
        """
        try:
            lesson_data = MathContentLoader.load_lesson(  # 2026-03-02: Load for character
                math_session.lesson.content_json_path
            )
            character = lesson_data.get('character', 'Maths Tutor')  # 2026-03-02: Name
        except (FileNotFoundError, Exception):  # 2026-03-02: Fallback
            character = 'Maths Tutor'

        return {  # 2026-03-02: Serialised response
            'success': True,
            'session_id': str(tutoring.id),
            'teaching_complete': tutoring.teaching_complete,
            'messages': list(tutoring.messages),
            'character': character,
        }
