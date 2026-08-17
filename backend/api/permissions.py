from rest_framework.permissions import BasePermission,  IsAdminUser, SAFE_METHODS


class IsAdminOrReadOnly(IsAdminUser):
    """Чтение доступно всем, изменение — только администратору."""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or super().has_permission(request, view)
        )


class IsAuthorAdminOrReadOnly(BasePermission):
    """
    Чтение доступно всем.
    Изменение/удаление — автору, модератору или администратору.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.is_staff
        )
