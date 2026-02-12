"""
Mastery Tracking Models

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Models for skill-based mastery tracking system.
    Enables fine-grained tracking of student learning progress.

Models:
    - Skill: Individual learning objectives
    - Concept: Hierarchical knowledge structure
    - StudentMastery: Student mastery level per skill
    - MasteryEvidence: Evidence supporting mastery claims

Design Pattern:
    - Skill Taxonomy: Hierarchical skill organization
    - Evidence-Based: Mastery backed by assessment data
    - Progressive: Track mastery development over time
    - Adaptive: Informs personalized learning paths
"""

# Django imports
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Python standard library
import uuid
from decimal import Decimal


class Skill(models.Model):
    """
    Skill model representing a learning objective.
    
    Purpose:
        Define atomic learning skills that students must master.
        Skills are the building blocks of curriculum.
    
    Attributes:
        id: UUID primary key
        code: Unique skill identifier (e.g., MATH_ADD_2DIGIT)
        name: Human-readable skill name
        description: Detailed skill description
        subject: Subject area (Math, Science, etc.)
        grade_level: Target grade level (1-12)
        difficulty: Difficulty rating (1-5)
        concept: Related concept (optional)
        prerequisites: Skills that must be mastered first
        is_active: Whether skill is currently taught
        created_at: When skill was created
        updated_at: Last update timestamp
    
    Business Rules:
        - Skills have unique codes
        - Difficulty ranges from 1 (easiest) to 5 (hardest)
        - Skills can have prerequisites (directed acyclic graph)
        - Skills belong to concepts for organization
    
    Example:
        skill = Skill.objects.create(
            code='MATH_ADD_2DIGIT',
            name='Addition of 2-digit numbers',
            subject='Mathematics',
            grade_level=2,
            difficulty=3
        )
    """
    
    # UUID primary key for distributed systems
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the skill"
    )
    
    # Skill code (unique identifier)
    # Used in curriculum mapping and analytics
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique skill code (e.g., MATH_ADD_2DIGIT)"
    )
    
    # Skill name (human-readable)
    name = models.CharField(
        max_length=200,
        help_text="Skill name"
    )
    
    # Detailed description
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the skill"
    )
    
    # Subject classification
    subject = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Subject area (Mathematics, Science, etc.)"
    )
    
    # Grade level
    grade_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        db_index=True,
        help_text="Target grade level (1-12)"
    )
    
    # Difficulty rating
    difficulty = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Difficulty level (1=easiest, 5=hardest)"
    )
    
    # Related concept (optional)
    # Enables hierarchical organization
    concept = models.ForeignKey(
        'Concept',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skills',
        help_text="Parent concept"
    )
    
    # Prerequisites (many-to-many self-reference)
    # Defines learning dependencies
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_skills',
        help_text="Skills that must be mastered first"
    )
    
    # Active flag
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this skill is currently taught"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When skill was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    
    class Meta:
        """Model metadata."""
        # Database table name
        db_table = 'analytics_skill'
        
        # Ordering
        ordering = ['subject', 'grade_level', 'code']
        
        # Indexes for performance
        indexes = [
            models.Index(fields=['subject', 'grade_level']),
            models.Index(fields=['code']),
        ]
        
        # Human-readable names
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
    
    def __str__(self):
        """
        String representation.
        
        Returns:
            str: Skill code, name, and grade level
        """
        return f"{self.code}: {self.name} (Grade {self.grade_level})"


class Concept(models.Model):
    """
    Concept model for hierarchical knowledge organization.
    
    Purpose:
        Organize skills into hierarchical concepts.
        Provides curriculum structure and navigation.
    
    Attributes:
        id: UUID primary key
        code: Unique concept identifier
        name: Concept name
        description: Concept description
        subject: Subject area
        parent: Parent concept (for hierarchy)
        order: Display order within parent
        created_at: Creation timestamp
        updated_at: Update timestamp
    
    Hierarchy Example:
        Mathematics (subject)
        └── Arithmetic (concept)
            ├── Addition (concept)
            │   ├── 1-digit addition (skill)
            │   └── 2-digit addition (skill)
            └── Subtraction (concept)
                └── ... (skills)
    """
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Concept code (unique)
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique concept code"
    )
    
    # Concept name
    name = models.CharField(
        max_length=200,
        help_text="Concept name"
    )
    
    # Description
    description = models.TextField(
        blank=True,
        help_text="Concept description"
    )
    
    # Subject
    subject = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Subject area"
    )
    
    # Parent concept (self-reference for hierarchy)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent concept"
    )
    
    # Display order
    order = models.IntegerField(
        default=0,
        help_text="Display order within parent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Model metadata."""
        db_table = 'analytics_concept'
        ordering = ['subject', 'parent', 'order', 'name']
        indexes = [
            models.Index(fields=['subject']),
            models.Index(fields=['parent', 'order']),
        ]
        verbose_name = 'Concept'
        verbose_name_plural = 'Concepts'
    
    def __str__(self):
        """String representation."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class StudentMastery(models.Model):
    """
    Student mastery tracking model.
    
    Purpose:
        Track student's mastery level for each skill.
        Provides granular progress monitoring.
    
    Attributes:
        id: UUID primary key
        student: User (student)
        skill: Skill being mastered
        mastery_level: Current mastery level (0-5)
        confidence_score: AI confidence in mastery (0-100)
        practice_count: Number of practice attempts
        success_count: Number of successful attempts
        first_attempted: When student first attempted
        last_practiced: Most recent practice
        mastered_at: When mastery achieved (level >= 4)
        created_at: Record creation
        updated_at: Last update
    
    Mastery Levels:
        0: Not attempted
        1: Introduced (< 40% success)
        2: Developing (40-60% success)
        3: Practicing (60-80% success)
        4: Proficient (80-90% success)
        5: Mastered (> 90% success)
    
    Business Rules:
        - One mastery record per student+skill
        - Mastery level increases with evidence
        - Confidence score updated by AI
        - Timestamps track progression
    """
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Student reference
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skill_masteries',
        help_text="Student user"
    )
    
    # Skill reference
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='student_masteries',
        help_text="Skill being mastered"
    )
    
    # Mastery level (0-5)
    mastery_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        default=0,
        db_index=True,
        help_text="Mastery level (0=not attempted, 5=mastered)"
    )
    
    # Confidence score (0-100)
    # AI-generated confidence in mastery assessment
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal('0.00'),
        help_text="AI confidence score (0-100)"
    )
    
    # Practice statistics
    practice_count = models.IntegerField(
        default=0,
        help_text="Number of practice attempts"
    )
    
    success_count = models.IntegerField(
        default=0,
        help_text="Number of successful attempts"
    )
    
    # Timestamps
    first_attempted = models.DateTimeField(
        auto_now_add=True,
        help_text="When student first attempted this skill"
    )
    
    last_practiced = models.DateTimeField(
        auto_now=True,
        help_text="Most recent practice"
    )
    
    mastered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When mastery was achieved (level >= 4)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Model metadata."""
        db_table = 'analytics_student_mastery'
        
        # Unique constraint: one mastery record per student+skill
        unique_together = [['student', 'skill']]
        
        ordering = ['-last_practiced']
        
        indexes = [
            models.Index(fields=['student', 'mastery_level']),
            models.Index(fields=['skill', 'mastery_level']),
            models.Index(fields=['-last_practiced']),
        ]
        
        verbose_name = 'Student Mastery'
        verbose_name_plural = 'Student Masteries'
    
    def __str__(self):
        """String representation."""
        return f"{self.student.username} - {self.skill.code} (Level {self.mastery_level})"
    
    def success_rate(self):
        """
        Calculate success rate percentage.
        
        Returns:
            float: Success rate (0-100)
        """
        # Avoid division by zero
        if self.practice_count == 0:
            return 0
        
        # Calculate percentage
        return (self.success_count / self.practice_count) * 100
    
    def is_mastered(self):
        """
        Check if skill is mastered.
        
        Returns:
            bool: True if mastery_level >= 4
        """
        return self.mastery_level >= 4
    
    def save(self, *args, **kwargs):
        """
        Override save to update mastered_at timestamp.
        
        Purpose:
            Automatically set mastered_at when mastery achieved.
        """
        # If mastery level is 4 or 5 and mastered_at not set
        if self.mastery_level >= 4 and self.mastered_at is None:
            self.mastered_at = timezone.now()
        
        # If mastery level drops below 4, clear mastered_at
        elif self.mastery_level < 4:
            self.mastered_at = None
        
        # Call parent save
        super().save(*args, **kwargs)


class MasteryEvidence(models.Model):
    """
    Evidence for mastery claims.
    
    Purpose:
        Link mastery levels to specific assessment results.
        Provides audit trail and justification for mastery.
    
    Attributes:
        id: UUID primary key
        mastery: StudentMastery record
        evidence_type: Type of evidence (quiz, test, practice, etc.)
        score: Score achieved
        max_score: Maximum possible score
        assessment_id: Reference to assessment
        metadata: Additional evidence data (JSON)
        recorded_at: When evidence was recorded
    
    Evidence Types:
        - quiz: Quiz results
        - test: Test results
        - practice: Practice session results
        - observation: Teacher observation
        - project: Project evaluation
    """
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Mastery reference
    mastery = models.ForeignKey(
        StudentMastery,
        on_delete=models.CASCADE,
        related_name='evidence',
        help_text="Related mastery record"
    )
    
    # Evidence type
    EVIDENCE_TYPES = [
        ('quiz', 'Quiz'),
        ('test', 'Test'),
        ('practice', 'Practice'),
        ('observation', 'Teacher Observation'),
        ('project', 'Project'),
        ('peer_review', 'Peer Review'),
    ]
    
    evidence_type = models.CharField(
        max_length=20,
        choices=EVIDENCE_TYPES,
        db_index=True,
        help_text="Type of evidence"
    )
    
    # Score data
    score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Score achieved"
    )
    
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Maximum possible score"
    )
    
    # Assessment reference
    assessment_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Reference to source assessment"
    )
    
    # Additional metadata (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional evidence metadata"
    )
    
    # Timestamp
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When evidence was recorded"
    )
    
    class Meta:
        """Model metadata."""
        db_table = 'analytics_mastery_evidence'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['mastery', '-recorded_at']),
            models.Index(fields=['evidence_type']),
        ]
        verbose_name = 'Mastery Evidence'
        verbose_name_plural = 'Mastery Evidence'
    
    def __str__(self):
        """String representation."""
        return f"{self.evidence_type}: {self.score}/{self.max_score} ({self.score_percentage():.1f}%)"
    
    def score_percentage(self):
        """
        Calculate score as percentage.
        
        Returns:
            float: Score percentage (0-100)
        """
        # Avoid division by zero
        if self.max_score == 0:
            return 0
        
        # Calculate percentage
        return (float(self.score) / float(self.max_score)) * 100
