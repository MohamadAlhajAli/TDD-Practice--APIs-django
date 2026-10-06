from django.shortcuts import render

from djoser.views import UserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated 
from LittleLemonAPI.permissions import IsManagerOrReadOnly 
from rest_framework.generics import ListAPIView  
from LittleLemonAPI.models import MenuItem  
from LittleLemonAPI.serializers import MenuItemSerializer

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


# --------- MenuItem  ------------ 

class MenuItemsView(ListAPIView): 

    queryset = MenuItem.objects.select_related("category")  
    serializer_class = MenuItemSerializer 
    permission_classes = [IsManagerOrReadOnly]







