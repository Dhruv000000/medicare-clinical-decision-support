# ==============================================================================
# FILE: backend/apps/medicines/services/openfda_service.py
# PURPOSE: Pharmacovigilance service integrating FDA openFDA APIs for adverse events and drug warnings.
# VIVA EXPLANATION: This service connects to the US FDA openFDA database to retrieve real-world Adverse Event Reporting System (FAERS) reaction frequencies, black-box warnings, and drug-drug interactions, with 24-hour caching and resilient offline fallback behavior.
# ==============================================================================

import logging
import requests
from typing import List, Dict, Any, Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)


# --- OpenFDAService ---
# What it does: Client querying FDA Structured Product Labels (SPL) and Adverse Event Reporting System (FAERS).
# Why it's structured this way: Enforces 24-hour cache TTL and non-blocking timeout fallbacks to ensure zero latency impact on clinical users.
# Parameters & Returns: Service class with adverse reactions, boxed warnings, and interaction querying methods.
# ------------------------------------------------------------------------------
class OpenFDAService:
    """
    Pharmacological Intelligence Service connecting to OpenFDA REST API.
    Enforces 24-hour caching (86400s) via django.core.cache and graceful fallback handling.
    """

    LABEL_URL = "https://api.fda.gov/drug/label.json"
    EVENT_URL = "https://api.fda.gov/drug/event.json"
    CACHE_TTL = 86400  # 24 hours
    TIMEOUT = 5.0      # seconds

    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        clean_id = identifier.strip().lower().replace(" ", "_")
        return f"openfda:{prefix}:{clean_id}"

    def get_adverse_reactions(self, drug_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Retrieves top reported adverse reactions from OpenFDA.
        Caches results for 24 hours. Gracefully falls back to empty structure on failure.

        Step-by-Step Logic (Viva Walkthrough):
            - STEP 1: Query normalization and cache lookup.
            - STEP 2: Query FDA FAERS event endpoint for MedDRA reaction frequencies.
            - STEP 3: Map reaction terms and reported incident case counts.
            - STEP 4: Store results in cache with 24-hour TTL.
        """
        clean_name = drug_name.strip()
        if not clean_name:
            return {
                "drug": "",
                "adverse_reactions": [],
                "status": "warning",
                "message": "Drug name cannot be empty.",
                "cached": False,
            }

        cache_key = self._get_cache_key("reactions", f"{clean_name}_{limit}")
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            cached_copy = dict(cached_data)
            cached_copy["cached"] = True
            return cached_copy

        params = {
            "search": f'patient.drug.medicinalproduct:"{clean_name}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
        }

        try:
            response = requests.get(self.EVENT_URL, params=params, timeout=self.TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])[:limit]
                reactions = [
                    {
                        "reaction": item.get("term", "").title(),
                        "reported_cases": item.get("count", 0),
                    }
                    for item in results
                ]
                result_payload = {
                    "drug": clean_name,
                    "adverse_reactions": reactions,
                    "total_reactions_reported": len(reactions),
                    "status": "success",
                    "cached": False,
                }
                cache.set(cache_key, result_payload, timeout=self.CACHE_TTL)
                return result_payload
            else:
                logger.warning("OpenFDA Event API returned status %s for drug %s", response.status_code, clean_name)
        except requests.RequestException as e:
            logger.warning("OpenFDA Event API connection failure for %s: %s", clean_name, e)
        except Exception as e:
            logger.exception("Unexpected error querying OpenFDA: %s", e)

        # Fallback response
        return {
            "drug": clean_name,
            "adverse_reactions": [],
            "total_reactions_reported": 0,
            "status": "warning",
            "message": f"Could not retrieve adverse reactions for '{clean_name}' from OpenFDA. Fallback active.",
            "cached": False,
        }

    def get_boxed_warnings_and_precautions(self, drug_name: str) -> Dict[str, Any]:
        """
        Retrieves boxed warnings, general warnings, and precautions from OpenFDA label endpoint.
        """
        clean_name = drug_name.strip()
        if not clean_name:
            return {
                "drug": "",
                "has_boxed_warning": False,
                "boxed_warnings": [],
                "precautions": [],
                "status": "warning",
                "message": "Drug name cannot be empty.",
                "cached": False,
            }

        cache_key = self._get_cache_key("warnings", clean_name)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            cached_copy = dict(cached_data)
            cached_copy["cached"] = True
            return cached_copy

        params = {
            "search": f'openfda.brand_name:"{clean_name}"+openfda.generic_name:"{clean_name}"',
            "limit": 1,
        }

        try:
            response = requests.get(self.LABEL_URL, params=params, timeout=self.TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    label = results[0]
                    raw_boxed = label.get("boxed_warning", [])
                    raw_warnings = label.get("warnings", []) or label.get("warnings_and_cautions", [])
                    raw_precautions = label.get("precautions", [])

                    boxed_list = [raw_boxed] if isinstance(raw_boxed, str) else list(raw_boxed)
                    precautions_list = [raw_precautions] if isinstance(raw_precautions, str) else list(raw_precautions)

                    result_payload = {
                        "drug": clean_name,
                        "has_boxed_warning": len(boxed_list) > 0,
                        "boxed_warnings": boxed_list,
                        "warnings": [raw_warnings] if isinstance(raw_warnings, str) else list(raw_warnings),
                        "precautions": precautions_list,
                        "status": "success",
                        "cached": False,
                    }
                    cache.set(cache_key, result_payload, timeout=self.CACHE_TTL)
                    return result_payload
            else:
                logger.warning("OpenFDA Label API returned status %s for drug %s", response.status_code, clean_name)
        except requests.RequestException as e:
            logger.warning("OpenFDA Label API error for %s: %s", clean_name, e)
        except Exception as e:
            logger.exception("Unexpected error in OpenFDA label query: %s", e)

        return {
            "drug": clean_name,
            "has_boxed_warning": False,
            "boxed_warnings": [],
            "warnings": [],
            "precautions": [],
            "status": "warning",
            "message": f"Could not retrieve label warnings for '{clean_name}'. Fallback active.",
            "cached": False,
        }

    def check_interactions(self, drug_list: List[str]) -> Dict[str, Any]:
        """
        Analyzes pairwise pharmacological interactions between a list of medications.
        Queries OpenFDA label drug_interactions data.
        """
        clean_drugs = sorted(set(d.strip().lower() for d in drug_list if d.strip()))
        if len(clean_drugs) < 2:
            return {
                "drugs_analyzed": clean_drugs,
                "interactions_found": [],
                "total_interactions": 0,
                "status": "ok",
                "message": "At least two distinct drugs are required to check for interactions.",
                "cached": False,
            }

        cache_key = self._get_cache_key("interactions", "_".join(clean_drugs))
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            cached_copy = dict(cached_data)
            cached_copy["cached"] = True
            return cached_copy

        interactions = []

        try:
            for i, drug_a in enumerate(clean_drugs):
                params = {
                    "search": f'openfda.brand_name:"{drug_a}"+openfda.generic_name:"{drug_a}"',
                    "limit": 1,
                }
                res = requests.get(self.LABEL_URL, params=params, timeout=self.TIMEOUT)
                if res.status_code != 200:
                    continue

                label_results = res.json().get("results", [])
                if not label_results:
                    continue

                interactions_text = " ".join(label_results[0].get("drug_interactions", [])).lower()
                for drug_b in clean_drugs:
                    if drug_a == drug_b:
                        continue
                    if drug_b in interactions_text:
                        # Extract context window around drug name
                        idx = interactions_text.find(drug_b)
                        start = max(0, idx - 100)
                        end = min(len(interactions_text), idx + 200)
                        snippet = interactions_text[start:end].strip()

                        # Prevent duplicate reverse pairs
                        pair_exists = any(
                            (x["drug_a"] == drug_b and x["drug_b"] == drug_a) or
                            (x["drug_a"] == drug_a and x["drug_b"] == drug_b)
                            for x in interactions
                        )
                        if not pair_exists:
                            severity = "high" if any(w in interactions_text for w in ["contraindicated", "fatal", "toxic", "severe"]) else "moderate"
                            interactions.append({
                                "drug_a": drug_a.title(),
                                "drug_b": drug_b.title(),
                                "severity": severity,
                                "description": snippet,
                            })

            result_payload = {
                "drugs_analyzed": [d.title() for d in clean_drugs],
                "interactions_found": interactions,
                "total_interactions": len(interactions),
                "status": "success",
                "cached": False,
            }
            cache.set(cache_key, result_payload, timeout=self.CACHE_TTL)
            return result_payload

        except requests.RequestException as e:
            logger.warning("OpenFDA interactions network error: %s", e)
        except Exception as e:
            logger.exception("Unexpected error in check_interactions: %s", e)

        return {
            "drugs_analyzed": [d.title() for d in clean_drugs],
            "interactions_found": [],
            "total_interactions": 0,
            "status": "warning",
            "message": "External OpenFDA service unreachable or timed out. Fallback active.",
            "cached": False,
        }


# Singleton instance
openfda_service = OpenFDAService()
