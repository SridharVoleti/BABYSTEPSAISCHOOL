"""
2026-02-19: Language registry for Read-Along & Mimic Engine (BS-RAM).

Purpose:
    Provides LANGUAGE_SEED dict used only by data migration and tests.
    At runtime, all language lookups go through the DB via helper functions.
    Admins can add new languages via Django admin without any code changes.
"""

# 2026-02-19: Seed dict used ONLY by data migration and tests — never at runtime
LANGUAGE_SEED = {
    'English':   {'bcp47': 'en-IN', 'tts_rate': 0.9,  'script': 'Latin',      'display_name': 'English',     'sort_order': 1},
    'Hindi':     {'bcp47': 'hi-IN', 'tts_rate': 0.85, 'script': 'Devanagari', 'display_name': 'हिन्दी',      'sort_order': 2},
    'Telugu':    {'bcp47': 'te-IN', 'tts_rate': 0.85, 'script': 'Telugu',     'display_name': 'తెలుగు',     'sort_order': 3},
    'Tamil':     {'bcp47': 'ta-IN', 'tts_rate': 0.85, 'script': 'Tamil',      'display_name': 'தமிழ்',      'sort_order': 4},
    'Kannada':   {'bcp47': 'kn-IN', 'tts_rate': 0.85, 'script': 'Kannada',    'display_name': 'ಕನ್ನಡ',      'sort_order': 5},
    'Malayalam': {'bcp47': 'ml-IN', 'tts_rate': 0.85, 'script': 'Malayalam',  'display_name': 'മലയാളം',     'sort_order': 6},
    'Marathi':   {'bcp47': 'mr-IN', 'tts_rate': 0.85, 'script': 'Devanagari', 'display_name': 'मराठी',       'sort_order': 7},
    'Bengali':   {'bcp47': 'bn-IN', 'tts_rate': 0.85, 'script': 'Bengali',    'display_name': 'বাংলা',       'sort_order': 8},
    'Gujarati':  {'bcp47': 'gu-IN', 'tts_rate': 0.85, 'script': 'Gujarati',   'display_name': 'ગુજરાતી',    'sort_order': 9},
    'Punjabi':   {'bcp47': 'pa-IN', 'tts_rate': 0.85, 'script': 'Gurmukhi',   'display_name': 'ਪੰਜਾਬੀ',     'sort_order': 10},
    'Odia':      {'bcp47': 'or-IN', 'tts_rate': 0.85, 'script': 'Odia',       'display_name': 'ଓଡ଼ିଆ',      'sort_order': 11},
    'Assamese':  {'bcp47': 'as-IN', 'tts_rate': 0.85, 'script': 'Bengali',    'display_name': 'অসমীয়া',    'sort_order': 12},
    'Urdu':      {'bcp47': 'ur-IN', 'tts_rate': 0.85, 'script': 'Nastaliq',   'display_name': 'اردو',        'sort_order': 13},
    'Sanskrit':  {'bcp47': 'sa-IN', 'tts_rate': 0.80, 'script': 'Devanagari', 'display_name': 'संस्कृतम्',  'sort_order': 14},
}


def get_active_languages():
    """
    2026-02-19: Return all active Language rows from DB.

    Returns:
        QuerySet: Active Language objects ordered by sort_order, name.
    """
    from .models import Language  # 2026-02-19: Local import to avoid circular
    return Language.objects.filter(is_active=True)  # 2026-02-19: DB query


def get_language(name: str):
    """
    2026-02-19: Fetch a single active Language by name.

    Args:
        name: Language name, e.g. 'Telugu'.

    Returns:
        Language: Active Language instance.

    Raises:
        Language.DoesNotExist: If language not found or is inactive.
    """
    from .models import Language  # 2026-02-19: Local import to avoid circular
    return Language.objects.get(name=name, is_active=True)  # 2026-02-19: DB lookup


def is_valid_language(name: str) -> bool:
    """
    2026-02-19: Check if a language name is valid and active in DB.

    Args:
        name: Language name to validate.

    Returns:
        bool: True if language exists and is active.
    """
    from .models import Language  # 2026-02-19: Local import
    return Language.objects.filter(name=name, is_active=True).exists()  # 2026-02-19: Check


def get_student_languages(student) -> list:
    """
    2026-02-19: Get student's assigned languages filtered to active DB entries.

    Args:
        student: Student model instance with language_1/2/3 fields.

    Returns:
        list[str]: Ordered list of active language names for this student.
    """
    # 2026-02-19: Collect student's non-empty language preferences
    candidate_names = []
    for lang_field in [student.language_1, student.language_2, student.language_3]:
        if lang_field and lang_field not in candidate_names:
            candidate_names.append(lang_field)

    # 2026-02-19: Filter to only active DB languages
    from .models import Language  # 2026-02-19: Local import
    active_names = set(
        Language.objects.filter(name__in=candidate_names, is_active=True)
        .values_list('name', flat=True)
    )

    # 2026-02-19: Preserve student's preferred order, always include English
    result = [n for n in candidate_names if n in active_names]
    if 'English' not in result and is_valid_language('English'):
        result.insert(0, 'English')  # 2026-02-19: English always available

    return result  # 2026-02-19: Return ordered list
