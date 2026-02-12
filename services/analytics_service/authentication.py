"""
Custom Authentication Classes for Analytics Service

Date: 2025-12-12
Author: BabySteps Development Team

Purpose:
    Provide custom authentication that returns 401 Unauthorized
    instead of 403 Forbidden for unauthenticated requests.
"""

from rest_framework.authentication import SessionAuthentication as BaseSessionAuthentication
from rest_framework import exceptions


class SessionAuthentication(BaseSessionAuthentication):
    """
    Custom session authentication that raises AuthenticationFailed
    instead of returning None for unauthenticated requests.
    
    This ensures proper 401 Unauthorized response.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using session authentication.
        
        Returns:
            tuple: (user, auth) if authenticated
            None: if request doesn't have session auth
        
        Raises:
            AuthenticationFailed: Never (handled by permission classes)
        """
        # Call parent authentication
        user = getattr(request._request, 'user', None)
        
        # If no user in session, return None (not authenticated via this method)
        if not user or not user.is_authenticated:
            return None
        
        # Perform CSRF check
        self.enforce_csrf(request)
        
        return (user, None)
