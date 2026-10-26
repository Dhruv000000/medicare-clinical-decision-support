# ==============================================================================
# FILE: backend/ai/__init__.py
# PURPOSE: Package initializer exposing public clinical AI components, engines, and knowledge matchers.
# VIVA EXPLANATION: Exports core clinical AI abstractions (ClinicalPreprocessor, DiseaseRiskEngine, ClinicalKnowledgeMatcher) to provide a unified facade for application layers.
# ==============================================================================

from .preprocessing import (
    ClinicalPreprocessor,
    PreprocessedClinicalData,
    preprocess_clinical_input,
    get_preprocessor,
    get_preprocessor_v2,
    CANONICAL_SYMPTOMS,
)
from .engine import (
    DiseaseRiskEngine,
    ModelNotLoadedError,
    get_engine,
)
from .clinical_kb import (
    ClinicalKnowledgeMatcher,
    DifferentialDiagnosisCandidate,
    get_knowledge_matcher,
)

__all__ = [
    "ClinicalPreprocessor",
    "PreprocessedClinicalData",
    "preprocess_clinical_input",
    "get_preprocessor",
    "get_preprocessor_v2",
    "CANONICAL_SYMPTOMS",
    "DiseaseRiskEngine",
    "ModelNotLoadedError",
    "get_engine",
    "ClinicalKnowledgeMatcher",
    "DifferentialDiagnosisCandidate",
    "get_knowledge_matcher",
]
