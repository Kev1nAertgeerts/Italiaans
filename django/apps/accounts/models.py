from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.username

class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    login_ip = models.GenericIPAddressField(default="")
    login_device = models.CharField(max_length=255, default="")
    login_location = models.CharField(max_length=255, default="")
    login_browser = models.CharField(max_length=255, default="")
    login_os = models.CharField(max_length=255, default="")