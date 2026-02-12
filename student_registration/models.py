"""
Student Registration Models
Author: Cascade AI
Date: 2025-12-13
Description: Models for student registration and admin approval workflow
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, EmailValidator
import uuid


# Get the User model for foreign key relationships
User = get_user_model()


class StudentRegistration(models.Model):
    """
    Model to store student registration requests pending admin approval
    
    Stores complete student information including personal details,
    parent/guardian information, and tracks approval workflow status.
    """
    
    # Status choices for registration workflow
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Language choices
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('telugu', 'Telugu'),
        ('both', 'Both'),
    ]
    
    # Primary key - unique registration ID
    registration_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Auto-generated unique registration identifier"
    )
    
    # Student Information
    student_name = models.CharField(
        max_length=200,
        help_text="Full name of the student"
    )
    
    student_email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Student's email address for communication"
    )
    
    date_of_birth = models.DateField(
        help_text="Student's date of birth"
    )
    
    grade = models.CharField(
        max_length=10,
        help_text="Current grade/class of the student"
    )
    
    school_name = models.CharField(
        max_length=300,
        help_text="Name of the school student is currently attending"
    )
    
    preferred_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default='english',
        help_text="Preferred language for learning content"
    )
    
    # Parent/Guardian Information
    parent_name = models.CharField(
        max_length=200,
        help_text="Full name of parent or guardian"
    )
    
    parent_email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Parent/guardian email for notifications"
    )
    
    # Phone validator - exactly 10 digits
    phone_validator = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be exactly 10 digits"
    )
    
    phone = models.CharField(
        max_length=10,
        validators=[phone_validator],
        help_text="Contact phone number (10 digits)"
    )
    
    # Address Information
    address = models.TextField(
        help_text="Complete residential address"
    )
    
    city = models.CharField(
        max_length=100,
        help_text="City name"
    )
    
    state = models.CharField(
        max_length=100,
        help_text="State name"
    )
    
    # Pincode validator - exactly 6 digits
    pincode_validator = RegexValidator(
        regex=r'^\d{6}$',
        message="Pincode must be exactly 6 digits"
    )
    
    pincode = models.CharField(
        max_length=6,
        validators=[pincode_validator],
        help_text="Postal pincode (6 digits)"
    )
    
    # Registration Status and Workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of registration"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when registration was submitted"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last update"
    )
    
    # Approval tracking
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_registrations',
        help_text="Admin user who approved the registration"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when registration was approved"
    )
    
    # Rejection tracking
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection if status is rejected"
    )
    
    class Meta:
        """Meta options for StudentRegistration model"""
        ordering = ['-created_at']  # Newest registrations first
        verbose_name = 'Student Registration'
        verbose_name_plural = 'Student Registrations'
        indexes = [
            models.Index(fields=['status', '-created_at']),  # For filtering by status
            models.Index(fields=['student_email']),  # For email lookups
        ]
    
    def __str__(self):
        """String representation of registration"""
        return f"{self.student_name} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Override save to perform validation before saving"""
        # Perform full validation
        self.full_clean()
        # Call parent save method
        super().save(*args, **kwargs)
