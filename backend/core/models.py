from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_guest = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(AbstractUser.Meta):
        verbose_name = 'core user'
        verbose_name_plural = 'core users'
        db_table = 'core_user'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


def create_core_user(*, username, email='', password=None, **extra_fields):
    """Thin helper that avoids auth.User accessor clashes in interactive scripts."""
    return User.objects.create_user(username=username, email=email, password=password, **extra_fields)
