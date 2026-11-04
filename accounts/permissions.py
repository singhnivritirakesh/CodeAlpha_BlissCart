from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to Admin users or superusers.
    """
    message = "Access restricted to administrators only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_superuser or request.user.is_staff)
        )


class IsSellerRole(permissions.BasePermission):
    """
    Allows access only to Seller users (and Admins).
    """
    message = "Access restricted to verified sellers."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in ['seller', 'admin'] or request.user.is_superuser)
        )


class IsBuyerRole(permissions.BasePermission):
    """
    Allows access to Buyer users.
    """
    message = "Access restricted to customer accounts."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'buyer' or request.user.is_superuser)
        )

