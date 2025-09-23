from rest_framework import permissions

class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, or OPTIONS requests (read-only access) for any authenticated user.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user