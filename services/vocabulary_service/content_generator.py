"""
2026-02-20: LLM-backed vocabulary content generator (BS-LNG).

Purpose:
    Generates child-friendly definitions, example sentences, and mnemonics
    for VocabularyWord instances. Results are cached in WordContent to avoid
    repeated LLM calls. Falls back to safe placeholder content on any error.

Design:
    Module-level import of get_llm_provider (same pattern as comprehension_service)
    for testability via patch('services.vocabulary_service.content_generator.get_llm_provider').
"""

import json  # 2026-02-20: JSON parsing for LLM response
import logging  # 2026-02-20: Module logger

from services.llm_service.factory import get_llm_provider  # 2026-02-20: LLM provider (module-level for testability)

logger = logging.getLogger(__name__)  # 2026-02-20: Module logger

# 2026-02-20: Prompt template for child-friendly word content
WORD_CONTENT_PROMPT = """
You are a children's language teacher. Student is in Grade {grade}, learning {target_language}.
Their mother tongue is {mother_tongue}.
Generate child-friendly content for: "{word}" ({word_type})
Respond ONLY as valid JSON:
{{
  "definition": "simple meaning in {mother_tongue} (max 15 words)",
  "example_sentence": "simple sentence using '{word}' in {target_language} (max 10 words)",
  "example_translation": "translation of example in {mother_tongue}",
  "mnemonic": "optional memory trick in {mother_tongue} (blank string if none)"
}}
"""


def _build_fallback(word_text: str, target_language: str) -> dict:
    """
    2026-02-20: Build safe placeholder content when LLM is unavailable.

    Args:
        word_text: The word in native script.
        target_language: Language being learned.

    Returns:
        dict: Fallback content with llm_error=True.
    """
    return {  # 2026-02-20: Neutral fallback content
        'definition': f"(Definition for '{word_text}')",
        'example_sentence': word_text,
        'example_translation': word_text,
        'mnemonic': '',
        'llm_error': True,
    }


def get_word_content(word, mother_tongue) -> dict:
    """
    2026-02-20: Get or generate content for a VocabularyWord in mother tongue.

    Checks WordContent cache first. On cache miss, calls the LLM to generate
    child-friendly content. Stores result (or fallback) in WordContent.
    Never raises — on any error, stores fallback with llm_error=True.

    Args:
        word: VocabularyWord model instance (with language FK loaded).
        mother_tongue: Language model instance for the student's native language.

    Returns:
        dict: definition, example_sentence, example_translation, mnemonic, llm_error.
    """
    from .models import WordContent  # 2026-02-20: Local import to avoid circular

    # 2026-02-20: Check cache — return immediately if found
    try:
        cached = WordContent.objects.get(word=word, mother_tongue=mother_tongue)
        return {  # 2026-02-20: Return cached content
            'definition': cached.definition,
            'example_sentence': cached.example_sentence,
            'example_translation': cached.example_translation,
            'mnemonic': cached.mnemonic,
            'llm_error': cached.llm_error,
        }
    except WordContent.DoesNotExist:
        pass  # 2026-02-20: Cache miss — generate via LLM

    # 2026-02-20: Build LLM prompt
    target_language = word.language.name  # 2026-02-20: Language being learned
    prompt = WORD_CONTENT_PROMPT.format(
        grade=word.grade,
        target_language=target_language,
        mother_tongue=mother_tongue.name,
        word=word.word,
        word_type=word.word_type,
    ).strip()

    content_dict = None  # 2026-02-20: Will hold parsed or fallback content
    llm_error = False  # 2026-02-20: Error flag

    try:
        llm = get_llm_provider()  # 2026-02-20: Get configured provider
        response = llm.chat(  # 2026-02-20: Call LLM
            message=prompt,
            system_prompt='You are a helpful children\'s language teacher. Respond in JSON only.',
        )
        raw_text = response.text.strip()  # 2026-02-20: Extract text

        # 2026-02-20: Strip markdown fences if present
        if raw_text.startswith('```'):
            lines = raw_text.split('\n')
            raw_text = '\n'.join(
                line for line in lines
                if not line.startswith('```')
            ).strip()

        parsed = json.loads(raw_text)  # 2026-02-20: Parse JSON

        # 2026-02-20: Validate required keys
        required_keys = ('definition', 'example_sentence', 'example_translation', 'mnemonic')
        for key in required_keys:
            if key not in parsed:
                raise ValueError(f"Missing key in LLM response: {key}")

        content_dict = {  # 2026-02-20: Validated content
            'definition': str(parsed['definition']),
            'example_sentence': str(parsed['example_sentence']),
            'example_translation': str(parsed['example_translation']),
            'mnemonic': str(parsed.get('mnemonic', '')),
            'llm_error': False,
        }

    except Exception as exc:  # 2026-02-20: Any failure → fallback
        logger.warning(  # 2026-02-20: Log warning but don't block session
            "LLM word content generation failed for '%s' (%s→%s): %s",
            word.word, target_language, mother_tongue.name, exc,
        )
        content_dict = _build_fallback(word.word, target_language)
        llm_error = True

    # 2026-02-20: Store in cache (idempotent via get_or_create)
    try:
        WordContent.objects.update_or_create(
            word=word,
            mother_tongue=mother_tongue,
            defaults={
                'definition': content_dict['definition'],
                'example_sentence': content_dict['example_sentence'],
                'example_translation': content_dict['example_translation'],
                'mnemonic': content_dict['mnemonic'],
                'llm_error': content_dict['llm_error'],
            },
        )
    except Exception as store_exc:  # 2026-02-20: Don't block session on DB error
        logger.warning("Failed to cache WordContent: %s", store_exc)

    return content_dict  # 2026-02-20: Return content (from LLM or fallback)
