"""
2026-02-12: JWT utility functions for token generation.

Purpose:
    Generate JWT tokens with custom claims for parent and student roles.
    Uses djangorestframework-simplejwt for token creation.
"""

from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-12: JWT tokens


def get_tokens_for_parent(parent):
    """
    2026-02-12: Generate JWT tokens for a parent user.

    Args:
        parent: Parent model instance.

    Returns:
        dict: Access and refresh tokens with role claims.
    """
    refresh = RefreshToken.for_user(parent.user)  # 2026-02-12: Create token pair
    refresh['role'] = 'parent'  # 2026-02-12: Custom claim
    refresh['parent_id'] = str(parent.id)  # 2026-02-12: Parent UUID
    return {  # 2026-02-12: Return token pair
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def get_tokens_for_student(student):
    """
    2026-02-12: Generate JWT tokens for a student user.

    Args:
        student: Student model instance.

    Returns:
        dict: Access and refresh tokens with role claims.
    """
    refresh = RefreshToken.for_user(student.user)  # 2026-02-12: Create token pair
    refresh['role'] = 'student'  # 2026-02-12: Custom claim
    refresh['student_id'] = str(student.id)  # 2026-02-12: Student UUID
    refresh['age_group'] = student.age_group  # 2026-02-12: Age group for UI
    return {  # 2026-02-12: Return token pair
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
