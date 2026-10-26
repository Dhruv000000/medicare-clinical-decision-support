# ==============================================================================
# FILE: backend/apps/accounts/admin.py
# PURPOSE: Django Admin panel configuration for managing User accounts and clinical role assignments.
# VIVA EXPLANATION: Configures UserAdmin with email-based search, role filtering (Patient, Doctor, Admin), and fieldsets separating credentials, permissions, and audit timestamps.
# ==============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


# --- UserAdmin ---
# What it does: Customizes Django's administrative interface for the email-centric User model.
# Why it's structured this way: Organizes account fields into distinct sections (Personal Info, Roles & Permissions, Dates) and enables filtering by application role.
# Parameters & Returns: Django ModelAdmin class configuring the User model.
# ------------------------------------------------------------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "email", "first_name", "last_name", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff", "created_at")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Roles & Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "first_name", "last_name", "is_active"),
            },
        ),
    )
