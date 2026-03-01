"""
User model for Printy API.
Email as USERNAME_FIELD for allauth compatibility.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from common.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Custom manager for email-based auth."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    """
    Custom user with email as primary identifier.
    Alias: AUTH_USER_MODEL = "accounts.User" (same as CustomUser for compatibility).
    """

    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    preferred_language = models.CharField(
        max_length=10,
        blank=True,
        default="en",
        help_text="Preferred language code (en, sw). Used for authenticated requests.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email
