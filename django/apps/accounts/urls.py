from django.urls import path
from .views import login_user, logout_user

app_name = "accounts"
urlpatterns = [
    path("login/", login_user, name="login_user"),
    path("logout/", logout_user, name="logout_user"),
]
