from django.contrib import admin
from django.urls import path

from LittleLemonAPI.views import RegistrationView, CurrentUserView, login_page
from djoser.views import TokenCreateView
 


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/users",
        RegistrationView.as_view({"post": "create"}),
        name="register",
    ),
    path(
        "token/login/", 
        TokenCreateView.as_view(), 
        name="token-login",     
    ),
    path(
        "api/users/users/me/",
        CurrentUserView.as_view({"get": "me"}),
        name="current-user",
    ),
    path("login/", login_page, name="login-page"),
]