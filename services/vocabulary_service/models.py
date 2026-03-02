"""
2026-02-20: Vocabulary Acquisition System models (BS-LNG).

Purpose:
    VocabularyWord: One row per word per language per grade (frequency-ranked).
    WordContent: LLM-generated cache of definition/example/mnemonic per
                 (word × mother_tongue) pair.
    StudentWordProgress: Per-student mastery tracking for each word.
    VocabularySession: One daily session record (up to 10 words).
    SessionWord: Through model linking session ↔ word with per-word scores.
"""

import uuid  # 2026-02-20: UUID primary keys

from django.db import models  # 2026-02-20: Django ORM
from django.core.validators import (  # 2026-02-20: Field validators
    MinValueValidator, MaxValueValidator
)

from services.auth_service.models import Student  # 2026-02-20: Cross-app FK


class VocabularyWord(models.Model):
    """
    2026-02-20: A single vocabulary word for a specific language and grade.

    Words are frequency-ranked (1 = most common) within each
    (language, grade) pair. Up to 2000 words per grade per language.
    """

    WORD_TYPE_CHOICES = [  # 2026-02-20: Part-of-speech categories
        ('noun', 'Noun'),
        ('verb', 'Verb'),
        ('adjective', 'Adjective'),
        ('adverb', 'Adverb'),
        ('pronoun', 'Pronoun'),
        ('preposition', 'Preposition'),
        ('number', 'Number'),
        ('conjunction', 'Conjunction'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    language = models.ForeignKey(  # 2026-02-20: FK to Language in read_along_service
        'read_along_service.Language',
        on_delete=models.CASCADE,
        related_name='vocabulary_words',
    )
    grade = models.IntegerField(  # 2026-02-20: School grade 1-12
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    frequency_rank = models.IntegerField(  # 2026-02-20: 1 = most common word
        validators=[MinValueValidator(1), MaxValueValidator(20000)]
    )
    word = models.CharField(max_length=100)  # 2026-02-20: Native script
    romanization = models.CharField(  # 2026-02-20: Latin transliteration (blank for English)
        max_length=150, blank=True, default=''
    )
    word_type = models.CharField(  # 2026-02-20: Part of speech
        max_length=20, choices=WORD_TYPE_CHOICES, default='other'
    )
    image_keyword = models.CharField(  # 2026-02-20: Keyword for image lookup
        max_length=100, blank=True, default=''
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Creation time

    class Meta:
        """2026-02-20: Model metadata."""

        unique_together = [  # 2026-02-20: One row per (language, grade, rank)
            ['language', 'grade', 'frequency_rank']
        ]
        ordering = ['grade', 'frequency_rank']  # 2026-02-20: Natural order
        indexes = [  # 2026-02-20: Fast lookup for session creation
            models.Index(fields=['language', 'grade', 'frequency_rank']),
        ]

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.word} ({self.language.name} Grade {self.grade} #{self.frequency_rank})"


class WordContent(models.Model):
    """
    2026-02-20: LLM-generated content cache for (word × mother_tongue) pair.

    Avoids repeat LLM calls: once generated, the definition/example/mnemonic
    are reused for all students who share that mother tongue.
    llm_error=True means the LLM failed and fallback content was stored;
    the next call will retry if desired (but defaults to returning cache).
    """

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    word = models.ForeignKey(  # 2026-02-20: The vocabulary word
        VocabularyWord, on_delete=models.CASCADE, related_name='contents'
    )
    mother_tongue = models.ForeignKey(  # 2026-02-20: Student's native language (for definitions)
        'read_along_service.Language',
        on_delete=models.PROTECT,  # 2026-02-20: PROTECT: don't cascade-delete cache
        related_name='word_contents',
    )
    definition = models.TextField()  # 2026-02-20: Meaning in mother tongue
    example_sentence = models.TextField()  # 2026-02-20: Simple target-language sentence
    example_translation = models.TextField()  # 2026-02-20: Translation of example
    mnemonic = models.TextField(blank=True, default='')  # 2026-02-20: Memory trick
    llm_error = models.BooleanField(default=False)  # 2026-02-20: True if LLM failed
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-20: Last updated

    class Meta:
        """2026-02-20: Model metadata."""

        unique_together = [  # 2026-02-20: One cache entry per (word, mother_tongue)
            ['word', 'mother_tongue']
        ]

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.word.word} → {self.mother_tongue.name}"


class StudentWordProgress(models.Model):
    """
    2026-02-20: Per-student mastery state for a single vocabulary word.

    Tracks exposure count, best pronunciation score, MCQ accuracy,
    and overall status (unseen → introduced → practicing → mastered).
    review_due_at is reserved for BS-SPC spaced repetition integration.
    """

    STATUS_CHOICES = [  # 2026-02-20: Mastery lifecycle
        ('unseen', 'Unseen'),
        ('introduced', 'Introduced'),
        ('practicing', 'Practicing'),
        ('mastered', 'Mastered'),
    ]

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-20: The learning student
        Student, on_delete=models.CASCADE, related_name='word_progress'
    )
    word = models.ForeignKey(  # 2026-02-20: The vocabulary word
        VocabularyWord, on_delete=models.CASCADE, related_name='student_progress'
    )
    status = models.CharField(  # 2026-02-20: Current mastery level
        max_length=15, choices=STATUS_CHOICES, default='unseen'
    )
    exposure_count = models.IntegerField(default=0)  # 2026-02-20: Times seen
    best_pronunciation_score = models.FloatField(  # 2026-02-20: Best mimic score 0.0-1.0
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    mcq_correct_count = models.IntegerField(default=0)  # 2026-02-20: Correct MCQ answers
    last_seen_at = models.DateTimeField(null=True, blank=True)  # 2026-02-20: Last exposure
    review_due_at = models.DateTimeField(  # 2026-02-20: Reserved for BS-SPC spaced repetition
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-20: Last updated

    class Meta:
        """2026-02-20: Model metadata."""

        unique_together = [  # 2026-02-20: One record per (student, word)
            ['student', 'word']
        ]

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.student.full_name} | {self.word.word} — {self.status}"


class VocabularySession(models.Model):
    """
    2026-02-20: One daily vocabulary practice session per (student, language).

    A student gets exactly one session per language per day. The session
    contains 10 words selected from their grade's unmastered word list.
    fluency_star_rating is computed from pronunciation + MCQ performance.
    """

    STATUS_CHOICES = [  # 2026-02-20: Session lifecycle
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-20: The learning student
        Student, on_delete=models.CASCADE, related_name='vocabulary_sessions'
    )
    language = models.ForeignKey(  # 2026-02-20: The language being learned
        'read_along_service.Language',
        on_delete=models.CASCADE,
        related_name='vocabulary_sessions',
    )
    grade = models.IntegerField(  # 2026-02-20: Snapshot of student grade at creation
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    session_date = models.DateField()  # 2026-02-20: Calendar date of session
    status = models.CharField(  # 2026-02-20: Session status
        max_length=15, choices=STATUS_CHOICES, default='in_progress'
    )
    fluency_star_rating = models.IntegerField(  # 2026-02-20: 0-5 stars computed at completion
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_time_seconds = models.IntegerField(default=0)  # 2026-02-20: Total session duration
    completed_at = models.DateTimeField(null=True, blank=True)  # 2026-02-20: Completion time
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-20: Last updated

    class Meta:
        """2026-02-20: Model metadata."""

        unique_together = [  # 2026-02-20: One session per (student, language, day)
            ['student', 'language', 'session_date']
        ]
        ordering = ['-session_date']  # 2026-02-20: Newest first

    def __str__(self):
        """2026-02-20: String representation."""
        return (
            f"{self.student.full_name} | {self.language.name} "
            f"{self.session_date} — {self.status}"
        )


class SessionWord(models.Model):
    """
    2026-02-20: Through model linking VocabularySession to VocabularyWord.

    Records per-word pronunciation score and MCQ result for a session.
    word_order defines the presentation sequence (1-10).
    """

    id = models.UUIDField(  # 2026-02-20: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-02-20: Parent session
        VocabularySession, on_delete=models.CASCADE, related_name='session_words'
    )
    word = models.ForeignKey(  # 2026-02-20: The word in this slot
        VocabularyWord, on_delete=models.CASCADE, related_name='session_words'
    )
    word_order = models.IntegerField(  # 2026-02-20: Position in session (1-10)
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    pronunciation_score = models.FloatField(  # 2026-02-20: Levenshtein similarity 0-1 (null = not scored)
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    mcq_answered = models.BooleanField(default=False)  # 2026-02-20: MCQ attempted
    mcq_correct = models.BooleanField(default=False)  # 2026-02-20: MCQ answered correctly
    time_on_word_seconds = models.IntegerField(default=0)  # 2026-02-20: Time spent on this word
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-20: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-20: Last updated

    class Meta:
        """2026-02-20: Model metadata."""

        unique_together = [  # 2026-02-20: One slot per (session, word)
            ['session', 'word']
        ]
        ordering = ['word_order']  # 2026-02-20: Present words in sequence order

    def __str__(self):
        """2026-02-20: String representation."""
        return f"{self.session} | #{self.word_order} {self.word.word}"
