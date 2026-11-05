from django.urls import path

from .views import health_check_view, home

urlpatterns = [
    path("", home, name="home"),
    path("health/", health_check_view, name="health"),
]
