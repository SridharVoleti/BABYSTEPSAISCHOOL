"""
Analytics Service Permissions

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Define custom permissions for analytics API endpoints.
    Implements role-based access control for student data privacy.

Permission Hierarchy:
    - Students: Can only view/modify their own data
    - Teachers (staff): Can view all student data
    - Admins: Full access to all operations

Design Principles:
    - Least privilege: Users get minimum necessary permissions
    - Privacy-first: Student data is protected by default
    - Audit trail: All access is logged
"""

# Django REST Framework imports
from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated


class IsAuthenticatedOrRaise401(permissions.BasePermission):
    """
    Custom authentication permission that raises 401 instead of 403.
    
    DRF's IsAuthenticated returns 403 Forbidden for unauthenticated requests.
    This custom class raises NotAuthenticated (401) instead for proper HTTP semantics.
    
    Date: 2025-12-12
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        
        Raises:
            NotAuthenticated: If user is not authenticated (returns 401)
        
        Returns:
            bool: True if authenticated
        """
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated(detail='Authentication credentials were not provided.')
        return True


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission class that allows:
    - Students to access only their own data
    - Staff (teachers/admins) to access all data
    
    Purpose:
        Ensures student data privacy while allowing teachers to monitor progress.
    
    Usage:
        Add to viewset: permission_classes = [IsOwnerOrStaff]
    
    Logic:
        - For list views: Filter queryset by user
        - For detail views: Check object ownership
        - Staff bypass all ownership checks
    """
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        
        Args:
            request: HTTP request object with authenticated user
            view: The view being accessed
            
        Returns:
            bool: True if user has permission, False otherwise
            
        Logic:
            - Assumes user is already authenticated (checked by IsAuthenticatedOrRaise401)
            - All authenticated users can access list views (filtered by ownership)
        
        Note:
            - Do NOT check authentication here - use IsAuthenticatedOrRaise401 for that
            - This prevents 403 from overriding 401 for unauthenticated requests
        """
        # All authenticated users can access list views
        # Queryset filtering will handle data access control
        # Authentication check is done by IsAuthenticatedOrRaise401
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access specific object.
        
        Args:
            request: HTTP request object
            view: The view being accessed
            obj: The specific object (Activity or Progress)
            
        Returns:
            bool: True if user can access object, False otherwise
            
        Logic:
            - Staff can access any object
            - Students can only access their own objects
            - Check obj.student field for ownership
        """
        # Staff (teachers and admins) can access all data
        # This allows teachers to monitor student progress
        if request.user.is_staff:
            return True
        
        # Students can only access their own data
        # Check if the object's student field matches the requesting user
        # Handle both StudentActivity and StudentProgress models
        if hasattr(obj, 'student'):
            return obj.student == request.user
        
        # If object doesn't have student field, deny access
        # This is a safety fallback
        return False


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Read access for all authenticated users
    - Write access only for staff
    
    Purpose:
        Used for endpoints where students should read but not modify data.
        Example: Summary statistics, aggregated analytics
    
    Usage:
        permission_classes = [IsStaffOrReadOnly]
    """
    
    def has_permission(self, request, view):
        """
        Check view-level permission.
        
        Args:
            request: HTTP request object
            view: The view being accessed
            
        Returns:
            bool: True if permitted, False otherwise
            
        Logic:
            - GET, HEAD, OPTIONS allowed for all authenticated users
            - POST, PUT, PATCH, DELETE require staff status
        """
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read-only methods allowed for all authenticated users
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write operations require staff privileges
        return request.user.is_staff


class IsStudentOwner(permissions.BasePermission):
    """
    Permission class for student-specific operations.
    
    Purpose:
        Ensures students can only perform actions on their own account.
        Used for endpoints that modify student-specific data.
    
    Logic:
        - Check that request.user matches the student in the request
        - Prevent students from modifying others' data
    """
    
    def has_permission(self, request, view):
        """
        Check if user can access the view.
        
        Logic:
            - Must be authenticated
            - For POST requests, check 'student' field in data
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For POST requests creating new objects
        # Check that student field matches requesting user
        if request.method == 'POST':
            # Get student from request data
            student_id = request.data.get('student')
            
            # If student not specified, use requesting user
            if student_id is None:
                return True
            
            # Staff can create for any student
            if request.user.is_staff:
                return True
            
            # Students can only create for themselves
            # Compare as integers (student_id might be string)
            return int(student_id) == request.user.id
        
        # For other methods, default to allow
        # Object-level permissions will handle detail views
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permission.
        
        Logic:
            - Staff can access any object
            - Students can only access own objects
        """
        if request.user.is_staff:
            return True
        
        if hasattr(obj, 'student'):
            return obj.student == request.user
        
        return False


class CanDeleteAnalytics(permissions.BasePermission):
    """
    Permission class for deletion operations.
    
    Purpose:
        Analytics data should generally not be deleted (audit trail).
        Only admins can delete analytics records.
    
    Logic:
        - Only superusers can delete
        - Regular staff cannot delete
        - Students definitely cannot delete
    """
    
    def has_permission(self, request, view):
        """
        Check if user can delete analytics data.
        
        Returns:
            bool: True only for superusers
        """
        # Only superusers can delete analytics data
        # This preserves audit trail and data integrity
        if request.method == 'DELETE':
            return request.user and request.user.is_superuser
        
        # For other methods, allow (handled by other permissions)
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level delete permission check.
        
        Returns:
            bool: True only for superusers
        """
        if request.method == 'DELETE':
            return request.user and request.user.is_superuser
        
        return True


class CanViewAggregatedAnalytics(permissions.BasePermission):
    """
    Permission for viewing aggregated/summary analytics.
    
    Purpose:
        Control access to dashboard summaries and aggregated statistics.
        Students see own summaries, teachers see class summaries.
    
    Logic:
        - Students can view own summary
        - Teachers can view class/school summaries
        - Admins can view all summaries
    """
    
    def has_permission(self, request, view):
        """
        Check permission for summary endpoints.
        
        Logic:
            - All authenticated users can access summaries
            - Queryset filtering handles data scope
        """
        # Require authentication for all summary data
        return request.user and request.user.is_authenticated


# Permission sets for different use cases
# These can be imported and used as: permission_classes = STUDENT_DATA_PERMISSIONS

STUDENT_DATA_PERMISSIONS = [
    permissions.IsAuthenticated,
    IsOwnerOrStaff,
]

STAFF_ONLY_PERMISSIONS = [
    permissions.IsAuthenticated,
    permissions.IsAdminUser,
]

SUMMARY_PERMISSIONS = [
    permissions.IsAuthenticated,
    CanViewAggregatedAnalytics,
]

READ_ONLY_PERMISSIONS = [
    permissions.IsAuthenticated,
    IsStaffOrReadOnly,
]
