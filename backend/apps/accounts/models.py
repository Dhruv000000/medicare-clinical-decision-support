# ==============================================================================
# FILE: backend/apps/accounts/models.py
# PURPOSE: Custom User model and authentication manager utilizing email-based identity.
# VIVA EXPLANATION: Replaces default Django username authentication with email credentials and introduces strict RBAC role enums (Patient, Doctor, Administrator).
# ==============================================================================

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


# --- CustomUserManager ---
# What it does: Manages user creation using normalized lowercase email as the primary login credential.
# Why it's structured this way: Eliminates legacy username requirements and standardizes user provisioning.
# Parameters & Returns: create_user and create_superuser methods returning configured User instances.
# ------------------------------------------------------------------------------
class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication
    instead of usernames.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Roles.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# --- User ---
# What it does: Primary authentication and identity model extending Django's AbstractUser.
# Why it's structured this way: Stores core user identity, email, first/last names, and role classification (PATIENT, DOCTOR, ADMIN).
# Parameters & Returns: Custom Django User model.
# ------------------------------------------------------------------------------
class User(AbstractUser):
    class Roles(models.TextChoices):
        PATIENT = "patient", "Patient"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Administrator"

    username = None  # Remove username completely
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    objects = CustomUserManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.role})"
