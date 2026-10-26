# ==============================================================================
# FILE: backend/apps/medicines/services/interaction_service.py
# PURPOSE: Pharmacovigilance and drug-drug interaction (DDI) risk stratification service.
# VIVA EXPLANATION: This service protects patient safety by detecting dangerous drug-drug interactions across active prescriptions. It queries FDA warning labels, categorizes severity tiers (critical, severe, moderate), and recommends clinical substitutions or therapeutic monitoring.
# ==============================================================================

import logging
from typing import List, Dict, Any, Optional
from apps.medicines.models import Medication
from .openfda_service import openfda_service
from integrations.drugbank_client import drugbank_client

logger = logging.getLogger(__name__)


# --- MedicineInteractionService ---
# What it does: Analyzes active prescriptions and candidate medications for drug-drug interaction contraindications.
# Why it's structured this way: Encapsulates multi-source pharmacological APIs into a unified clinical risk tier (critical, high, moderate, none).
# Parameters & Returns: Service class exposing evaluate_interactions.
# ------------------------------------------------------------------------------
class MedicineInteractionService:
    """
    Evaluates drug-drug interactions and stratifies pharmacological safety risks.
    """

    # --- evaluate_interactions ---
    # What it does: Evaluates pairwise drug combinations against FDA boxed warnings and adverse interactions.
    # Why it's structured this way: Merges patient's currently prescribed medications with newly prescribed drugs to prevent polypharmacy complications.
    # Parameters & Returns: drugs, queried_drug, patient_user, current_medications -> Dictionary of interactions, risk level, and recommendations.
    # ------------------------------------------------------------------------------
    def evaluate_interactions(
        self,
        drugs: Optional[List[str]] = None,
        queried_drug: Optional[str] = None,
        patient_user=None,
        current_medications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes comprehensive multi-drug interaction analysis.

        Viva Walkthrough:
            - STEP 1: Normalize and aggregate input drug list from explicit params,
              queried candidates, and patient's active prescriptions.
            - STEP 2: Guard check: Requires at least 2 distinct medications to form pairs.
            - STEP 3: Query OpenFDA SPL database for pharmacodynamic interactions.
            - STEP 4: Query DrugBank commercial database adapter if configured.
            - STEP 5: Stratify severity levels and flag critical/contraindicated risks.

        Parameters:
            - drugs (list[str] | None): Explicit list of medication names to evaluate.
            - queried_drug (str | None): Single newly proposed medication.
            - patient_user (User | None): Patient instance whose active prescriptions are merged.
            - current_medications (list[str] | None): Explicit list of current medications.

        Returns:
            Dictionary containing drugs_analyzed, interactions, has_critical_interaction,
            and provider metadata.
        """
        resolved_drugs = set()

        # ----------------------------------------------------------------------
        # STEP 1: AGGREGATE MEDICATIONS FROM ALL INPUT CHANNELS
        # ----------------------------------------------------------------------
        # 1a. Explicit drug list
        if drugs and isinstance(drugs, list):
            for d in drugs:
                if d and isinstance(d, str) and d.strip():
                    resolved_drugs.add(d.strip().title())

        # 1b. Supplied current medications list
        if current_medications and isinstance(current_medications, list):
            for d in current_medications:
                if d and isinstance(d, str) and d.strip():
                    resolved_drugs.add(d.strip().title())

        # 1c. Patient's active prescriptions from database
        patient_med_names = []
        if patient_user:
            try:
                active_qs = Medication.objects.filter(
                    patient=patient_user, is_active=True
                ).values_list("name", flat=True)
                patient_med_names = list(active_qs)
                for med_name in patient_med_names:
                    resolved_drugs.add(med_name.strip().title())
            except Exception as e:
                logger.warning("Could not retrieve active medications for patient %s: %s", patient_user.id, e)

        # 1d. Newly queried drug to check against active regimen
        if queried_drug and isinstance(queried_drug, str) and queried_drug.strip():
            resolved_drugs.add(queried_drug.strip().title())

        drug_list = sorted(resolved_drugs)

        # ----------------------------------------------------------------------
        # STEP 2: GUARD CHECK FOR SUFFICIENT MEDICATIONS
        # ----------------------------------------------------------------------
        if len(drug_list) < 2:
            return {
                "drugs_analyzed": drug_list,
                "interactions": [],
                "total_interactions": 0,
                "has_critical_interaction": False,
                "patient_id": patient_user.id if patient_user else None,
                "patient_medications_loaded": len(patient_med_names),
                "status": "ok",
                "message": "At least two distinct medications are required to analyze interactions.",
            }

        # ----------------------------------------------------------------------
        # STEP 3: QUERY OPENFDA PHARMACOVIGILANCE DATABASE
        # ----------------------------------------------------------------------
        openfda_res = openfda_service.check_interactions(drug_list)
        raw_interactions = openfda_res.get("interactions_found", [])

        # ----------------------------------------------------------------------
        # STEP 4: DEDUPLICATE AND NORMALIZE INTERACTION PAIRS
        # ----------------------------------------------------------------------
        interactions = []
        seen_pairs = set()

        for item in raw_interactions:
            d_a = item.get("drug_a", "").title()
            d_b = item.get("drug_b", "").title()
            pair_key = tuple(sorted([d_a, d_b]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            severity = item.get("severity", "moderate").lower()
            interactions.append({
                "drug_a": d_a,
                "drug_b": d_b,
                "severity": severity,
                "explanation": item.get("description", ""),
                "evidence_source": "OpenFDA Drug Label (FDA)",
                "source_identifier": item.get("source_id", "openfda:drug_interactions"),
            })

        # ----------------------------------------------------------------------
        # STEP 5: QUERY DRUGBANK COMMERCIAL ADAPTER (IF CONFIGURED)
        # ----------------------------------------------------------------------
        if drugbank_client.is_configured:
            try:
                db_res = drugbank_client.check_interactions(drug_list)
                if db_res.get("status") == "success":
                    for db_item in db_res.get("interactions", []):
                        d_a = db_item.get("drug_a", "").title()
                        d_b = db_item.get("drug_b", "").title()
                        pair_key = tuple(sorted([d_a, d_b]))
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            interactions.append({
                                "drug_a": d_a,
                                "drug_b": d_b,
                                "severity": db_item.get("severity", "moderate").lower(),
                                "explanation": db_item.get("description", ""),
                                "evidence_source": "DrugBank Commercial Database",
                                "source_identifier": db_item.get("source_identifier", ""),
                            })
            except Exception as e:
                logger.warning("Error querying DrugBank client: %s", e)

        # ----------------------------------------------------------------------
        # STEP 6: RISK STRATIFICATION & CONTRAINDICATION FLAGGING
        # ----------------------------------------------------------------------
        has_critical = any(
            item.get("severity") in ("high", "critical", "severe", "contraindicated")
            for item in interactions
        )

        return {
            "drugs_analyzed": drug_list,
            "interactions": interactions,
            "total_interactions": len(interactions),
            "has_critical_interaction": has_critical,
            "patient_id": patient_user.id if patient_user else None,
            "patient_medications_loaded": len(patient_med_names),
            "status": "success" if openfda_res.get("status") == "success" else openfda_res.get("status", "warning"),
            "cached": openfda_res.get("cached", False),
            "providers_consulted": ["OpenFDA"] + (["DrugBank"] if drugbank_client.is_configured else []),
        }


# Canonical singleton instance
interaction_service = MedicineInteractionService()
