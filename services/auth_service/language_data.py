"""
2026-02-12: Language data for NEP 2020 suggestions.

Purpose:
    State-to-language mapping for three-language formula.
    Used to suggest languages based on parent's Indian state.
"""

# 2026-02-12: State to recommended languages mapping (NEP 2020)
STATE_LANGUAGE_MAP = {
    'Andhra Pradesh': {
        'language_1': 'Telugu',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Telangana': {
        'language_1': 'Telugu',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Tamil Nadu': {
        'language_1': 'Tamil',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Karnataka': {
        'language_1': 'Kannada',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Kerala': {
        'language_1': 'Malayalam',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Maharashtra': {
        'language_1': 'Marathi',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Gujarat': {
        'language_1': 'Gujarati',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'West Bengal': {
        'language_1': 'Bengali',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Rajasthan': {
        'language_1': 'Hindi',
        'language_2': 'English',
        'language_3': 'Sanskrit',
    },
    'Uttar Pradesh': {
        'language_1': 'Hindi',
        'language_2': 'English',
        'language_3': 'Sanskrit',
    },
    'Madhya Pradesh': {
        'language_1': 'Hindi',
        'language_2': 'English',
        'language_3': 'Sanskrit',
    },
    'Bihar': {
        'language_1': 'Hindi',
        'language_2': 'English',
        'language_3': 'Maithili',
    },
    'Odisha': {
        'language_1': 'Odia',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Punjab': {
        'language_1': 'Punjabi',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
    'Assam': {
        'language_1': 'Assamese',
        'language_2': 'English',
        'language_3': 'Hindi',
    },
}

# 2026-02-12: Default suggestion when state is unknown
DEFAULT_LANGUAGES = {
    'language_1': 'English',
    'language_2': 'Hindi',
    'language_3': '',
}

# 2026-02-12: All available languages
AVAILABLE_LANGUAGES = [
    'English', 'Hindi', 'Telugu', 'Tamil', 'Kannada', 'Malayalam',
    'Marathi', 'Gujarati', 'Bengali', 'Odia', 'Punjabi', 'Assamese',
    'Maithili', 'Sanskrit', 'Urdu', 'Konkani', 'Manipuri', 'Nepali',
]
