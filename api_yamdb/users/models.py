from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy


class User(AbstractUser):
    class Role:
        USER = "user"
        MODERATOR = "moderator"
        ADMIN = "admin"
        SUPERUSER = "superuser"

        @classmethod
        def choices(cls):
            return [
                (getattr(cls, k), getattr(cls, k))
                for k in cls.__dict__.keys()
                if isinstance(getattr(cls, k), str) and "_" not in k
            ]

    email = models.EmailField(gettext_lazy("email address"), unique=True)
    bio = models.TextField(max_length=300, blank=True)
    confirmation_code = models.CharField(max_length=60, blank=True)
    description = models.TextField(max_length=300, blank=True)
    role = models.CharField(
        max_length=25, choices=Role.choices(), default=Role.USER
    )

    @property
    def is_admin(self):
        return (self.is_authenticated
                and self.role == self.Role.ADMIN
                or self.is_superuser)

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR
