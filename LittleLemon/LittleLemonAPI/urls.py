from LittleLemonAPI.views import MenuItemsView, SingleMenuItemView
from django.urls import path 


urlpatterns = [
path("menu-items", MenuItemsView.as_view(), name="menu-items"),
path("menu-items/<int:pk>", SingleMenuItemView.as_view(), name="menu-item-detail"), 
]
