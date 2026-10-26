# ==============================================================================
# FILE: backend/integrations/openfda_client.py
# PURPOSE: Integration adapter and client wrapper for the US Food and Drug Administration (FDA) public API.
# VIVA EXPLANATION: Serves as an external HTTP integration adapter querying the official OpenFDA Drug Label API for drug names, adverse events, boxed warnings, and drug interactions, forwarding to the underlying openfda_service.
# ==============================================================================

import os
import requests
from typing import Dict, Any, List
from apps.medicines.services.openfda_service import openfda_service, OpenFDAService

BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov/drug")


# --- search_drug ---
# What it does: Executes HTTP queries against the OpenFDA Drug Label API for brand or generic drug names.
# Why it's structured this way: Encapsulates network timeout and error handling, returning normalized status dicts.
# Parameters & Returns: name (str), limit (int=5) -> Dict with query status, total count, and FDA label results.
# ------------------------------------------------------------------------------
def search_drug(name: str, limit: int = 5) -> Dict[str, Any]:
    clean_name = name.strip()
    if not clean_name:
        return {"results": [], "total": 0, "status": "empty"}

    try:
        response = requests.get(
            f"{BASE_URL}/label.json",
            params={"search": f'openfda.brand_name:"{clean_name}"+openfda.generic_name:"{clean_name}"', "limit": limit},
            timeout=openfda_service.TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"results": [], "total": 0, "status": "not_found", "message": f"No OpenFDA label found for '{clean_name}'."}
        else:
            return {"results": [], "total": 0, "status": "error", "message": f"OpenFDA returned status {response.status_code}."}
    except requests.RequestException as e:
        return {"results": [], "total": 0, "status": "error", "message": f"OpenFDA request failed: {str(e)}"}


# --- get_adverse_reactions ---
# What it does: Retrieves reported adverse physiological reactions for a given pharmaceutical compound.
# Why it's structured this way: Delegates to canonical cached service instance for resilience.
# Parameters & Returns: drug_name (str), limit (int=5) -> Dict with adverse reactions list.
# ------------------------------------------------------------------------------
def get_adverse_reactions(drug_name: str, limit: int = 5) -> Dict[str, Any]:
    return openfda_service.get_adverse_reactions(drug_name, limit=limit)


# --- get_boxed_warnings_and_precautions ---
# What it does: Fetches critical black-box warnings, contraindications, and special clinical precautions from FDA labels.
# Why it's structured this way: Crucial for patient safety to flag life-threatening drug contraindications.
# Parameters & Returns: drug_name (str) -> Dict containing boxed warnings and contraindication strings.
# ------------------------------------------------------------------------------
def get_boxed_warnings_and_precautions(drug_name: str) -> Dict[str, Any]:
    return openfda_service.get_boxed_warnings_and_precautions(drug_name)


# --- check_interactions ---
# What it does: Evaluates pairwise multi-drug interactions across a patient's medication list.
# Why it's structured this way: Implements combinatorial analysis to flag adverse pharmacological combinations.
# Parameters & Returns: drug_list (List[str]) -> Dict detailing interaction severity, descriptions, and warnings.
# ------------------------------------------------------------------------------
def check_interactions(drug_list: List[str]) -> Dict[str, Any]:
    return openfda_service.check_interactions(drug_list)


