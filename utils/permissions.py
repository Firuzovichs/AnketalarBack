from rest_framework.permissions import BasePermission

class IsProfileComplete(BasePermission):
    """User must have completed profile setup."""
    message = "Profil to'liq emas."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile') and request.user.profile.is_complete

class IsFaceVerified(BasePermission):
    """User must have verified face scan."""
    message = "Yuz skaneri tasdiqlanmagan."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile') and request.user.profile.is_face_verified
