# ==============================================================================
# FILE: backend/apps/assistant/urls.py
# PURPOSE: URL routing configuration for AI assistant chat and conversation history.
# VIVA EXPLANATION: Maps HTTP endpoints to assistant views (/chat/ and /history/) under the /api/v1/assistant/ namespace.
# ==============================================================================

from django.urls import path
from .views import AssistantHistoryView, AssistantChatView

# --- urlpatterns ---
# What it does: Registers URL route handlers for real-time RAG chat interaction and historical conversation retrieval.
# Why it's structured this way: Follows RESTful URL conventions under the assistant namespace.
# Parameters & Returns: List of django.urls.path route objects.
# ------------------------------------------------------------------------------
urlpatterns = [
    path("chat/", AssistantChatView.as_view(), name="assistant-chat"),
    path("history/", AssistantHistoryView.as_view(), name="assistant-history"),
]

