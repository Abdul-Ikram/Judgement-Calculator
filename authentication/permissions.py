from rest_framework.permissions import BasePermission


class IsTasksmith(BasePermission):
    """
    Allows access only to users with role 'tasksmith'.
    """

    def has_permission(self, request, view):
        return request.user and request.user.account_type in ['tasksmith']
        # return request.user and request.user.role in ['admin', 'tasksmith']


class IsAdmin(BasePermission):
    """
    Allows access only to users with role 'admin'.
    """

    def has_permission(self, request, view):
        return request.user and request.user.account_type in ['admin']


class IsAdminOrOwner(BasePermission):
    """
    Custom permission to only allow the owner or admin to delete the task.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.user.account_type == 'admin' or
            obj.user == request.user
        )
