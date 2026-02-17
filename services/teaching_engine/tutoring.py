"""
2026-02-17: AI Tutoring service for teaching engine (BS-AIE-002).

Purpose:
    Provides Socratic tutoring conversations during lessons.
    Uses the LLM service (Ollama) to generate mentor responses
    with lesson context, character persona, and IQ-level pacing.
"""

import logging  # 2026-02-17: Logging

from django.utils import timezone  # 2026-02-17: Timestamps

from services.llm_service import get_llm_provider, LLMError  # 2026-02-17: LLM factory
from .models import TutoringSession, StudentLessonProgress  # 2026-02-17: Models
from .content_loader import TeachingContentLoader  # 2026-02-17: Content

logger = logging.getLogger(__name__)  # 2026-02-17: Module logger

# 2026-02-17: Safety keywords to filter from responses
BLOCKED_KEYWORDS = [  # 2026-02-17: Content safety
    'violence', 'weapon', 'drug', 'alcohol', 'gambling',
    'inappropriate', 'explicit', 'hatred',
]


class TutoringService:
    """2026-02-17: AI tutoring chat service for lesson-context conversations."""

    @classmethod
    def _build_system_prompt(cls, character, iq_level, lesson_context=None):
        """
        2026-02-17: Build system prompt for the AI mentor persona.

        Args:
            character: Character name (e.g. 'Ollie the Owl').
            iq_level: Student's IQ level for pacing.
            lesson_context: Optional dict with lesson/day info.

        Returns:
            str: System prompt for LLM.
        """
        pacing_guide = {  # 2026-02-17: IQ pacing instructions
            'foundation': (
                'The student needs extra support. Use very simple words (1-2 syllables). '
                'Speak slowly. Repeat key concepts 2-3 times. Give lots of encouragement. '
                'Break explanations into tiny steps. Use examples from daily life.'
            ),
            'standard': (
                'The student is at grade level. Use age-appropriate vocabulary. '
                'Explain clearly with one example. Encourage questions.'
            ),
            'advanced': (
                'The student is advanced. Use richer vocabulary. Be concise. '
                'Challenge with follow-up questions. Encourage deeper thinking.'
            ),
        }

        pacing = pacing_guide.get(iq_level, pacing_guide['standard'])  # 2026-02-17: Lookup

        prompt = (  # 2026-02-17: Base prompt
            f"You are {character}, a friendly AI teaching mentor for young students "
            f"at BabySteps Digital School. You speak in a warm, encouraging tone.\n\n"
            f"PACING GUIDE: {pacing}\n\n"
            f"RULES:\n"
            f"- Use the Socratic method: ask guiding questions instead of giving direct answers.\n"
            f"- Keep responses short (2-4 sentences max).\n"
            f"- Never give test answers directly.\n"
            f"- Stay on topic related to the lesson.\n"
            f"- Be encouraging and patient.\n"
            f"- Use simple language appropriate for young children.\n"
            f"- If the student asks something unrelated, gently guide them back to the lesson.\n"
        )

        if lesson_context:  # 2026-02-17: Add lesson context
            prompt += (
                f"\nCURRENT LESSON CONTEXT:\n"
                f"- Topic: {lesson_context.get('title', 'Unknown')}\n"
                f"- Day: {lesson_context.get('day_number', 'Unknown')}\n"
                f"- Vocabulary: {', '.join(v.get('word', '') for v in lesson_context.get('vocabulary', []))}\n"
            )

        return prompt  # 2026-02-17: Return

    @classmethod
    def _is_safe_response(cls, text):
        """
        2026-02-17: Basic keyword safety check on LLM response.

        Args:
            text: Response text to check.

        Returns:
            bool: True if response passes safety check.
        """
        lower_text = text.lower()  # 2026-02-17: Case-insensitive
        for keyword in BLOCKED_KEYWORDS:  # 2026-02-17: Check each
            if keyword in lower_text:  # 2026-02-17: Found blocked word
                logger.warning(f"Blocked keyword '{keyword}' in LLM response")
                return False  # 2026-02-17: Unsafe
        return True  # 2026-02-17: Safe

    @classmethod
    def chat(cls, student, message, lesson_id=None, day_number=None):
        """
        2026-02-17: Process a tutoring chat message and return AI response.

        Args:
            student: Student model instance.
            message: Student's message text.
            lesson_id: Optional lesson_id for context.
            day_number: Optional day number for context.

        Returns:
            dict: Response with AI mentor's reply and session info.
        """
        # 2026-02-17: Get lesson context if available
        lesson_context = None  # 2026-02-17: Default
        character = 'Mentor'  # 2026-02-17: Default character
        iq_level = 'standard'  # 2026-02-17: Default IQ
        lesson_progress = None  # 2026-02-17: For session linking

        if lesson_id:  # 2026-02-17: Has lesson context
            progress = StudentLessonProgress.objects.filter(
                student=student, lesson__lesson_id=lesson_id
            ).select_related('lesson').first()

            if progress:  # 2026-02-17: Found progress
                lesson_progress = progress  # 2026-02-17: Link
                iq_level = progress.iq_level  # 2026-02-17: Student's IQ level
                character = progress.lesson.character_name or 'Mentor'  # 2026-02-17: Character

                # 2026-02-17: Load day content for context
                target_day = day_number or progress.current_day  # 2026-02-17: Day
                if 1 <= target_day <= 4:  # 2026-02-17: Valid day
                    try:
                        lesson_context = TeachingContentLoader.get_day_content(
                            progress.lesson.content_json_path, target_day, iq_level
                        )
                        lesson_context['day_number'] = target_day  # 2026-02-17: Add day
                    except (FileNotFoundError, ValueError):  # 2026-02-17: Content error
                        pass  # 2026-02-17: Continue without context

        # 2026-02-17: Build system prompt
        system_prompt = cls._build_system_prompt(  # 2026-02-17: Persona + pacing
            character, iq_level, lesson_context
        )

        # 2026-02-17: Find or create tutoring session
        session = TutoringSession.objects.filter(
            student=student,
            lesson_progress=lesson_progress,
            day_number=day_number,
        ).order_by('-created_at').first()

        if not session:  # 2026-02-17: New session
            session = TutoringSession.objects.create(
                student=student,
                lesson_progress=lesson_progress,
                day_number=day_number,
                messages=[],
            )

        # 2026-02-17: Add student message to session
        messages = list(session.messages or [])  # 2026-02-17: Copy
        messages.append({  # 2026-02-17: Student message
            'role': 'student',
            'text': message,
            'ts': timezone.now().isoformat(),
        })

        # 2026-02-17: Call LLM
        try:
            llm = get_llm_provider()  # 2026-02-17: Get provider
            response = llm.chat(  # 2026-02-17: Generate response
                message=message,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=200,
            )
            reply_text = response.text  # 2026-02-17: Extract text
        except (LLMError, Exception) as e:  # 2026-02-17: LLM error
            logger.error(f"LLM error in tutoring chat: {e}")
            reply_text = (  # 2026-02-17: Fallback response
                f"I'm having a little trouble thinking right now. "
                f"Can you try asking me again in a moment?"
            )

        # 2026-02-17: Safety check
        if not cls._is_safe_response(reply_text):  # 2026-02-17: Failed safety
            reply_text = (  # 2026-02-17: Safe fallback
                "That's a great question! Let's focus on what we're learning today. "
                "What part of the lesson would you like to explore?"
            )

        # 2026-02-17: Add mentor response to session
        messages.append({  # 2026-02-17: Mentor message
            'role': 'mentor',
            'text': reply_text,
            'ts': timezone.now().isoformat(),
        })

        session.messages = messages  # 2026-02-17: Update session
        session.save()  # 2026-02-17: Persist

        return {  # 2026-02-17: Return response
            'success': True,
            'session_id': str(session.id),
            'reply': reply_text,
            'character': character,
            'message_count': len(messages),
        }
