from django.shortcuts import render

from djoser.views import UserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated


class RegistrationView(UserViewSet):
    http_method_names = ["post", "options"]

    def get_permissions(self):
        return [AllowAny()]
    
class CurrentUserView(UserViewSet):
    http_method_names = ["get", "head", "options"]

    def get_permissions(self):
        return [IsAuthenticated()]
    
def login_page(request):
    return render(request, "LittleLemonAPI/login.html")





