from rest_framework.permissions import BasePermission, SAFE_METHODS

def get_user_role(user):
    if not user.is_authenticated:
        return "Anonymous"

    if user.is_superuser or user.groups.filter(name="Manager").exists():
        return "Manager"

    if user.groups.filter(name="Delivery crew").exists():
        return "Delivery crew"

    return "Customer"


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == "Manager"


class IsDeliveryCrew(BasePermission): 
    def has_permission(self, request, view): 
        return get_user_role(request.user) == "Delivery crew"

class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        role = get_user_role(request.user)

        if role == "Anonymous":
            return False

        # SAFE_METHODS is a tuple containing 'GET', 'HEAD', 'OPTIONS'
        if request.method in SAFE_METHODS:
            return True

        return role == "Manager"
