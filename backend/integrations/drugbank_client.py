# ==============================================================================
# FILE: backend/integrations/drugbank_client.py
# PURPOSE: Integration adapter and client wrapper for the commercial/academic DrugBank pharmaceutical API.
# VIVA EXPLANATION: Implements the DrugBank client with strict security and graceful degradation: reads credentials from environment variables, never leaks keys, and falls back to transparent unconfigured states without crashing or fabricating fake medical data.
# ==============================================================================

import logging
import os
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DRUGBANK_BASE_URL = "https://api.drugbank.com/v1"


# --- DrugBankClient ---
# What it does: Adapter class encapsulating authentication, HTTP request execution, and timeouts for DrugBank.
# Why it's structured this way: Provides graceful degradation; returns structured 'unavailable' status if DRUGBANK_API_KEY is not set.
# Parameters & Returns: Client instance providing get_drug_info and check_interactions methods.
# ------------------------------------------------------------------------------
class DrugBankClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 8.0,
    ):
        self.api_key = api_key or os.getenv("DRUGBANK_API_KEY", "").strip()
        self.base_url = (base_url or os.getenv("DRUGBANK_BASE_URL", "").strip() or DEFAULT_DRUGBANK_BASE_URL).rstrip("/")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Returns True only if a non-empty API key is present."""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _unconfigured_response(self, operation: str) -> Dict[str, Any]:
        return {
            "source": "DrugBank",
            "status": "unavailable",
            "configured": False,
            "operation": operation,
            "message": (
                "DrugBank API key not configured. Licensed DrugBank access requires "
                "DRUGBANK_API_KEY in the environment."
            ),
        }

    # --- get_drug_info ---
    # What it does: Queries DrugBank for drug descriptions, indications, and DrugBank accession IDs.
    # Why it's structured this way: Handles 401, 403, 404, timeouts and network failures without raising unhandled exceptions.
    # Parameters & Returns: name (str) -> Dict containing drug pharmacology or error status.
    # ------------------------------------------------------------------------------
    def get_drug_info(self, name: str) -> Dict[str, Any]:
        clean_name = name.strip()
        if not clean_name:
            return {
                "source": "DrugBank",
                "status": "error",
                "configured": self.is_configured,
                "message": "Drug name cannot be empty.",
            }

        if not self.is_configured:
            logger.info("DrugBank not configured; returning transparent unavailable state for '%s'", clean_name)
            return self._unconfigured_response(f"get_drug_info:{clean_name}")

        try:
            url = f"{self.base_url}/drugs"
            params = {"q": clean_name}
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                results = data if isinstance(data, list) else data.get("drugs", [])
                if not results:
                    return {
                        "source": "DrugBank",
                        "drug": clean_name,
                        "status": "not_found",
                        "configured": True,
                        "message": f"No DrugBank records found for '{clean_name}'.",
                    }
                first = results[0]
                return {
                    "source": "DrugBank",
                    "drug": clean_name,
                    "drugbank_id": first.get("drugbank_id") or first.get("id"),
                    "name": first.get("name", clean_name),
                    "description": first.get("description", ""),
                    "indication": first.get("indication", ""),
                    "status": "success",
                    "configured": True,
                }
            elif response.status_code == 401 or response.status_code == 403:
                logger.error("DrugBank authorization failure: invalid credentials.")
                return {
                    "source": "DrugBank",
                    "status": "unauthorized",
                    "configured": True,
                    "message": "DrugBank API authorization failed. Check DRUGBANK_API_KEY.",
                }
            elif response.status_code == 404:
                return {
                    "source": "DrugBank",
                    "drug": clean_name,
                    "status": "not_found",
                    "configured": True,
                    "message": f"Drug '{clean_name}' not found in DrugBank.",
                }
            else:
                logger.warning("DrugBank API returned status %s for drug '%s'", response.status_code, clean_name)
                return {
                    "source": "DrugBank",
                    "status": "error",
                    "configured": True,
                    "status_code": response.status_code,
                    "message": f"DrugBank API responded with HTTP {response.status_code}.",
                }

        except requests.Timeout:
            logger.warning("DrugBank API request timed out for '%s'", clean_name)
            return {
                "source": "DrugBank",
                "status": "timeout",
                "configured": True,
                "message": "DrugBank API request timed out.",
            }
        except requests.RequestException as e:
            logger.warning("DrugBank API connection error: %s", e)
            return {
                "source": "DrugBank",
                "status": "error",
                "configured": True,
                "message": f"Network error connecting to DrugBank: {str(e)}",
            }

    # --- check_interactions ---
    # What it does: Evaluates pairwise pharmacological interactions across a list of input medications.
    # Why it's structured this way: Validates drug list size (>=2) and parses multi-drug interactions with severity classification.
    # Parameters & Returns: drug_names (List[str]) -> Dict with formatted interactions and severity levels.
    # ------------------------------------------------------------------------------
    def check_interactions(self, drug_names: List[str]) -> Dict[str, Any]:
        clean_names = [d.strip() for d in drug_names if d and d.strip()]
        if len(clean_names) < 2:
            return {
                "source": "DrugBank",
                "status": "error",
                "configured": self.is_configured,
                "message": "At least two distinct drugs are required to evaluate interactions.",
            }

        if not self.is_configured:
            return self._unconfigured_response("check_interactions")

        try:
            url = f"{self.base_url}/interactions"
            params = {"drugs": ",".join(clean_names)}
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = response.json()
                raw_interactions = data if isinstance(data, list) else data.get("interactions", [])
                formatted = []
                for item in raw_interactions:
                    formatted.append({
                        "drug_a": item.get("affected_drug", clean_names[0]).title(),
                        "drug_b": item.get("causing_drug", clean_names[1]).title(),
                        "severity": item.get("severity", "moderate").lower(),
                        "description": item.get("description", ""),
                        "source": "DrugBank",
                        "source_identifier": item.get("id") or item.get("drugbank_id", ""),
                    })
                return {
                    "source": "DrugBank",
                    "status": "success",
                    "configured": True,
                    "drugs": clean_names,
                    "interactions": formatted,
                    "total_interactions": len(formatted),
                }
            else:
                return {
                    "source": "DrugBank",
                    "status": "error",
                    "configured": True,
                    "status_code": response.status_code,
                    "message": f"DrugBank API responded with HTTP {response.status_code}.",
                }
        except requests.Timeout:
            return {
                "source": "DrugBank",
                "status": "timeout",
                "configured": True,
                "message": "DrugBank interaction query timed out.",
            }
        except requests.RequestException as e:
            return {
                "source": "DrugBank",
                "status": "error",
                "configured": True,
                "message": f"DrugBank connection failed: {str(e)}",
            }


# Canonical singleton instance
drugbank_client = DrugBankClient()


# --- get_drugbank_info ---
# What it does: Public convenience function querying drug metadata via the singleton client.
# Why it's structured this way: Backward compatibility wrapper for simpler imports.
# Parameters & Returns: name (str) -> Dict with drug information.
# ------------------------------------------------------------------------------
def get_drugbank_info(name: str) -> dict:
    return drugbank_client.get_drug_info(name)


