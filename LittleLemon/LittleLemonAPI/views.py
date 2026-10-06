from django.shortcuts import render
from django.db.models.deletion import ProtectedError
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from LittleLemonAPI.models import MenuItem
from LittleLemonAPI.permissions import IsManagerOrReadOnly
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

class MenuItemsView(ListCreateAPIView):

    queryset = MenuItem.objects.select_related("category")
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]


class SingleMenuItemView(RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related("category")
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]


    def destroy(self, request, *args, **kwargs):
        try:
            super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete a menu item used in an order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Deleted successfully."},
            status=status.HTTP_200_OK,
        )