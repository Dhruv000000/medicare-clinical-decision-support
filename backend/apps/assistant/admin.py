# ==============================================================================
# FILE: backend/apps/assistant/admin.py
# PURPOSE: Django Admin interface configuration for AI Assistant conversations and messages.
# VIVA EXPLANATION: Registers ChatConversation and ChatMessage models in the Django admin panel with inline message viewing, enabling administrators and clinical reviewers to audit AI interactions.
# ==============================================================================

from django.contrib import admin
from .models import ChatConversation, ChatMessage


# --- ChatMessageInline ---
# What it does: Displays individual chat messages inline inside the parent ChatConversation admin page.
# Why it's structured this way: Provides clinical reviewers a chronological, read-only transcript of user queries and AI responses with sources.
# Parameters & Returns: Django TabularInline admin model configuration.
# ------------------------------------------------------------------------------
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "sources", "created_at")


# --- ChatConversationAdmin ---
# What it does: Custom admin model for searching and browsing patient-AI clinical chat sessions.
# Why it's structured this way: Allows auditing by patient email and title with embedded inline message history.
# Parameters & Returns: Django ModelAdmin configuration.
# ------------------------------------------------------------------------------
@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at", "updated_at")
    search_fields = ("user__email", "title")
    inlines = [ChatMessageInline]
