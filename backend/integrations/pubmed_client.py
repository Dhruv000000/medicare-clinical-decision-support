# ==============================================================================
# FILE: backend/integrations/pubmed_client.py
# PURPOSE: Integration adapter and client wrapper for the NCBI PubMed biomedical literature API.
# VIVA EXPLANATION: Implements the PubMed literature retrieval client querying NCBI Entrez E-Utilities. Retrieves peer-reviewed clinical citations, PMIDs, and abstracts to ground RAG (Retrieval-Augmented Generation) responses in authentic medical science.
# ==============================================================================

import os
from typing import List, Dict, Any
from apps.assistant.services.pubmed_service import pubmed_service, PubMedService

BASE_URL = os.getenv("PUBMED_BASE_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


# --- search_pubmed ---
# What it does: Searches NCBI PubMed literature and extracts structured citation dictionaries containing PMIDs and abstracts.
# Why it's structured this way: Encapsulates Entrez ESearch and EFetch calls, providing standardized citation schemas for downstream LLM prompts.
# Parameters & Returns: query (str), retmax (int=5), fetch_abstracts (bool=True) -> List of citation dictionaries with titles, authors, and abstracts.
# ------------------------------------------------------------------------------
def search_pubmed(query: str, retmax: int = 5, fetch_abstracts: bool = True) -> List[Dict[str, Any]]:
    clean_query = query.strip()
    if not clean_query:
        return []

    res = pubmed_service.search_pubmed(clean_query, limit=retmax, fetch_abstracts=fetch_abstracts)
    citations = res.get("citations", [])
    return citations


