from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, SAFE_METHODS

class IsUserOrAdmin(BasePermission):
    """
    Object-level permission to allow a user to view/edit their own profile
    or if the user is a superuser.
    """
    def has_object_permission(self, request, view, obj):
        # A superuser can access any object.
        if request.user.is_superuser:
            return True
        
        # All other users can only access their own profile.
        return obj == request.user


class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a 'user' attribute that links it to the User model.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request.
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions (PUT, DELETE) are only allowed to the owner of the object.
        return obj.user == request.user
