# ==============================================================================
# FILE: backend/core/pagination.py
# PURPOSE: Standardized API response pagination across all collection endpoints.
# VIVA EXPLANATION: Implements cursor and page-number pagination for clinical records, predictions, and audit logs, preventing database memory exhaustion on large clinical datasets.
# ==============================================================================

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


# --- StandardResultsSetPagination ---
# What it does: Paginates list endpoints with page count, next/previous links, total pages, and current page metadata.
# Why it's structured this way: Enforces a consistent JSON envelope ({ count, total_pages, current_page, results }) expected by frontend React components.
# Parameters & Returns: Default page size of 10, max page size of 100 via '?page_size=' query parameter.
# ------------------------------------------------------------------------------
class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for collection endpoints.
    Default page size: 10
    Max page size: 100
    Query param for custom page size: ?page_size=20
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data,
        })
