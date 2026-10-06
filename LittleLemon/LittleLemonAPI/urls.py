from LittleLemonAPI.views import MenuItemsView
from django.urls import path 


urlpatterns = [
path("menu-items", MenuItemsView.as_view(), name="menu-items"),
]
