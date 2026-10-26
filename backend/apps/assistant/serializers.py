# ==============================================================================
# FILE: backend/apps/assistant/serializers.py
# PURPOSE: Serializers for chat messages, conversations, and literature citations.
# VIVA EXPLANATION: Serializes dialogue turns (ChatMessageSerializer) and nested conversation histories (ChatConversationSerializer) into clean JSON responses for the frontend patient portal.
# ==============================================================================

from rest_framework import serializers
from .models import ChatConversation, ChatMessage


# --- ChatMessageSerializer ---
# What it does: Serializes individual chat messages with role, text content, and citation sources.
# Why it's structured this way: All fields are read-only to ensure chat messages cannot be modified after creation.
# Parameters & Returns: ModelSerializer subclass.
# ------------------------------------------------------------------------------
class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "sources", "created_at"]
        read_only_fields = fields


# --- ChatConversationSerializer ---
# What it does: Serializes a conversation thread including nested messages.
# Why it's structured this way: Inlines messages directly for complete conversation rendering in the UI.
# Parameters & Returns: ModelSerializer subclass.
# ------------------------------------------------------------------------------
class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = ["id", "title", "messages", "created_at", "updated_at"]
        read_only_fields = fields

