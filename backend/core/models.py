from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_guest = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)