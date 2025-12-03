from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class that only allows admin users to access the view.
    Checks if user.user_type == 'ADMIN' or user.is_staff
    """

    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is admin or staff
        return (
            getattr(request.user, 'user_type', None) == 'ADMIN' or
            request.user.is_staff or
            request.user.is_superuser
        )
