"""
2026-02-12: Custom permissions for the authentication service.

Purpose:
    RBAC permission classes for parent and student access control.
"""

from rest_framework.permissions import BasePermission  # 2026-02-12: Base class


class IsParent(BasePermission):
    """2026-02-12: Allow access only to authenticated parent users."""

    def has_permission(self, request, view):
        """
        2026-02-12: Check if user has a parent profile.

        Args:
            request: HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if user is an authenticated parent.
        """
        return (  # 2026-02-12: Check auth and profile
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'parent_profile')
        )


class IsStudent(BasePermission):
    """2026-02-12: Allow access only to authenticated student users."""

    def has_permission(self, request, view):
        """
        2026-02-12: Check if user has a student profile.

        Args:
            request: HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if user is an authenticated student.
        """
        return (  # 2026-02-12: Check auth and profile
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'student_profile')
        )


class IsParentOfStudent(BasePermission):
    """2026-02-12: Allow parent to access only their own children's data."""

    def has_object_permission(self, request, view, obj):
        """
        2026-02-12: Check if the parent owns this student.

        Args:
            request: HTTP request.
            view: The view being accessed.
            obj: The student object being accessed.

        Returns:
            bool: True if user is parent of this student.
        """
        if not hasattr(request.user, 'parent_profile'):  # 2026-02-12: Must be parent
            return False
        return obj.parent_id == request.user.parent_profile.id  # 2026-02-12: Ownership
