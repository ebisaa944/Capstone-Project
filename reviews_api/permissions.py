from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, SAFE_METHODS


class IsUserOrAdmin(BasePermission):
    """
    Permission that grants access if the requesting user is:
    - A superuser (full access), or
    - Accessing their own user profile.
    """

    def has_object_permission(self, request, view, obj):
        # Superusers have unrestricted access
        if request.user and request.user.is_superuser:
            return True

        # Regular users can only access their own profile
        return obj == request.user


class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Permission that allows:
    - Read-only access to any authenticated user, and
    - Write access (PUT, PATCH, DELETE) only to the owner of the object.

    Assumes the model instance has a `user` attribute linking it to the User model.
    """

    def has_object_permission(self, request, view, obj):
        # Safe methods (GET, HEAD, OPTIONS) are always allowed
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only allowed for the owner of the object
        return hasattr(obj, "user") and obj.user == request.user
