# ==============================================================================
# FILE: backend/apps/assistant/models.py
# PURPOSE: Database schema models for multi-turn clinical chat conversations and messages.
# VIVA EXPLANATION: Persists RAG consultation sessions (ChatConversation) and individual dialogue messages (ChatMessage), storing message roles (user/assistant) and structured PubMed literature citations in JSON fields.
# ==============================================================================

from django.conf import settings
from django.db import models


# --- ChatConversation ---
# What it does: Tracks conversational dialogue threads between patients/doctors and the clinical AI assistant.
# Why it's structured this way: Indexed on (user, -updated_at) for fast recent conversation list retrieval.
# Parameters & Returns: Django Model representing a conversation thread.
# ------------------------------------------------------------------------------
class ChatConversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations",
    )
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self):
        return f"Chat: {self.title or 'Conversation'} ({self.user.email})"


# --- ChatMessage ---
# What it does: Stores an individual query or AI response with associated PubMed literature source citations.
# Why it's structured this way: JSONField sources stores structured citation metadata (PMID, title, URL) directly alongside the message.
# Parameters & Returns: Django Model representing a single chat turn.
# ------------------------------------------------------------------------------
class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20)  # user, assistant, system
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."


# Specification compatibility alias
ChatSession = ChatConversation

