from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_admin

class IsLabManagerUser(permissions.BasePermission):
    """
    Allows access only to lab manager users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_lab_manager

class IsTechnicianUser(permissions.BasePermission):
    """
    Allows access only to technician users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_technician

class IsSameUserOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow updating user object if you are the same user or an admin.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_admin or obj == request.user