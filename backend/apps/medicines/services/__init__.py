# ==============================================================================
# FILE: backend/apps/medicines/services/__init__.py
# PURPOSE: Package initializer exposing OpenFDA pharmaceutical queries and drug-drug interaction services.
# VIVA EXPLANATION: Exports OpenFDAService and MedicineInteractionService singletons for multi-drug risk screening.
# ==============================================================================

from .openfda_service import OpenFDAService, openfda_service
from .interaction_service import MedicineInteractionService, interaction_service

__all__ = [
    "OpenFDAService",
    "openfda_service",
    "MedicineInteractionService",
    "interaction_service",
]

