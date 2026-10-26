# ==============================================================================
# FILE: backend/ai/clinical_kb.py
# PURPOSE: Tier 2 Clinical Knowledge Base covering 530+ medical conditions with TF-IDF similarity.
# VIVA EXPLANATION: This module powers the Tier 2 diagnostic safety net. While the ML model handles the top 100 diseases, this knowledge matcher indexes 530+ conditions with ICD-10 codes, hallmark symptoms, and secondary symptoms using TF-IDF cosine similarity, ensuring the CDSS can identify rare diseases and atypical presentations.
# ==============================================================================

from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

DEFAULT_KB_PATH = os.path.join(os.path.dirname(__file__), "clinical_kb_data.json")


def normalize_disease_name(name: str) -> str:
    """Strips taxonomy suffixes such as 'of Pulmonology', 'of Gastroenterology', etc."""
    if not name or not isinstance(name, str):
        return name
    clean = re.sub(r"\s+of\s+[A-Za-z\s]+$", "", name).strip()
    if clean in ["Community-Acquired Pneumonia", "Community Acquired Pneumonia"]:
        return "Pneumonia"
    return clean


# --- DifferentialDiagnosisCandidate ---
# What it does: Dataclass encapsulating a candidate condition from the knowledge base with similarity scores and matched hallmarks.
# Why it's structured this way: Provides strongly-typed data representation for differential diagnosis lists and serialized API responses.
# Parameters & Returns: condition_id, name, category, icd10, urgency, score, confidence_pct, matched_features, matched_hallmarks, missing_hallmarks, description, typical_vitals.
# ------------------------------------------------------------------------------
@dataclass
class DifferentialDiagnosisCandidate:
    """Represents a scored candidate condition in the Tier 2 differential diagnosis."""
    condition_id: str
    name: str
    category: str
    icd10: str
    urgency: str
    score: float
    confidence_pct: float
    matched_features: List[str]
    matched_hallmarks: List[str]
    missing_hallmarks: List[str]
    description: str
    typical_vitals: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "category": self.category,
            "icd10": self.icd10,
            "urgency": self.urgency,
            "score": self.score,
            "confidence_pct": self.confidence_pct,
            "matched_features": self.matched_features,
            "matched_hallmarks": self.matched_hallmarks,
            "missing_hallmarks": self.missing_hallmarks,
            "description": self.description,
            "typical_vitals": self.typical_vitals,
        }


# ---------------------------------------------------------------------------
# Exhaustive 100-Disease Pathognomonic Signature Catalog (All 10 Specialties)
# ---------------------------------------------------------------------------

TARGET_100_PATHOGNOMONIC_SIGNATURES: Dict[str, Dict[str, Any]] = {
    # 1. Infectious Disease (10)
    "Malaria": {
        "id": "malaria",
        "category": "Infectious Disease",
        "icd10": "B54",
        "pathognomonic_symptoms": ["fever", "chills", "sweating", "myalgia", "headache"],
        "secondary_symptoms": ["nausea", "fatigue", "vomiting"],
        "urgency": "urgent",
        "description": "Cyclical mosquito-borne protozoan infection with paroxysmal chills, shivering, spikes of high fever, and drenching diaphoresis.",
    },
    "Dengue Fever": {
        "id": "dengue_fever",
        "category": "Infectious Disease",
        "icd10": "A90",
        "pathognomonic_symptoms": ["eye_pain", "bone_pain", "arthralgia", "skin_rash", "fever"],
        "secondary_symptoms": ["headache", "petechiae", "fatigue"],
        "urgency": "urgent",
        "description": "Arboviral breakbone fever presenting with retro-orbital pain, severe musculoskeletal aches, high fever, and petechial rash.",
    },
    "Typhoid Fever": {
        "id": "typhoid_fever",
        "category": "Infectious Disease",
        "icd10": "A01.0",
        "pathognomonic_symptoms": ["fever", "abdominal_pain", "diarrhea", "skin_rash", "fatigue"],
        "secondary_symptoms": ["headache", "sore_tongue", "anorexia"],
        "urgency": "urgent",
        "description": "Salmonella enterica bacteremia presenting with step-ladder fever, rose spots, pea-soup diarrhea, and coated tongue.",
    },
    "Pulmonary Tuberculosis": {
        "id": "pulmonary_tuberculosis",
        "category": "Infectious Disease",
        "icd10": "A15.0",
        "pathognomonic_symptoms": ["cough", "hemoptysis", "night_sweats", "weight_loss", "fever_low_grade"],
        "secondary_symptoms": ["fatigue", "chest_pain", "dyspnea"],
        "urgency": "urgent",
        "description": "Mycobacterium tuberculosis infection causing chronic cough lasting >3 weeks, hemoptysis, drenching night sweats, and unintentional wasting.",
    },
    "Leptospirosis": {
        "id": "leptospirosis",
        "category": "Infectious Disease",
        "icd10": "A27.9",
        "pathognomonic_symptoms": ["myalgia", "eye_redness", "fever", "jaundice"],
        "secondary_symptoms": ["headache", "chills", "nausea"],
        "urgency": "urgent",
        "description": "Zoonotic spirochete infection following contaminated water exposure with marked calf pain/tenderness, conjunctival suffusion, and jaundice.",
    },
    "Chickenpox": {
        "id": "chickenpox",
        "category": "Infectious Disease",
        "icd10": "B01.9",
        "pathognomonic_symptoms": ["skin_rash", "itching", "fever", "fatigue"],
        "secondary_symptoms": ["body_aches", "headache", "anorexia"],
        "urgency": "routine",
        "description": "Varicella zoster primary infection presenting with pruritic vesicular lesions in all stages of development with low-grade fever.",
    },
    "Cholera": {
        "id": "cholera",
        "category": "Infectious Disease",
        "icd10": "A00.9",
        "pathognomonic_symptoms": ["diarrhea", "dehydration", "vomiting", "fatigue"],
        "secondary_symptoms": ["muscle_cramps", "oliguria", "nausea"],
        "urgency": "emergency",
        "description": "Vibrio cholerae enterotoxin-mediated profuse painless rice-water diarrhea resulting in rapid severe dehydration and sunken eyes.",
    },
    "Influenza": {
        "id": "influenza",
        "category": "Infectious Disease",
        "icd10": "J11.1",
        "pathognomonic_symptoms": ["fever", "cough", "myalgia", "chills", "fatigue"],
        "secondary_symptoms": ["sore_throat", "headache", "rhinorrhea"],
        "urgency": "routine",
        "description": "Acute orthomyxovirus respiratory infection causing abrupt high fever, diffuse myalgias, shivering, and nonproductive cough.",
    },
    "Pneumonia": {
        "id": "community_acquired_pneumonia",
        "category": "Pulmonology",
        "icd10": "J18.9",
        "pathognomonic_symptoms": ["cough", "fever", "dyspnea", "purulent_sputum", "chest_tightness"],
        "secondary_symptoms": ["tachypnea", "chills", "fatigue", "pleuritic_chest_pain"],
        "urgency": "urgent",
        "description": "Lower respiratory alveolar consolidation with productive purulent sputum, fever, tachypnea, and pleuritic chest discomfort.",
    },
    "Community-Acquired Pneumonia": {
        "id": "community_acquired_pneumonia",
        "category": "Pulmonology",
        "icd10": "J18.9",
        "pathognomonic_symptoms": ["cough", "fever", "dyspnea", "purulent_sputum", "chest_tightness"],
        "secondary_symptoms": ["tachypnea", "chills", "fatigue", "pleuritic_chest_pain"],
        "urgency": "urgent",
        "description": "Lower respiratory alveolar consolidation with productive purulent sputum, fever, tachypnea, and pleuritic chest discomfort.",
    },
    "Acute Viral Hepatitis": {
        "id": "acute_viral_hepatitis",
        "category": "Infectious Disease",
        "icd10": "B19.9",
        "pathognomonic_symptoms": ["jaundice", "dark_urine", "fatigue", "nausea", "abdominal_pain"],
        "secondary_symptoms": ["anorexia", "clay_colored_stools", "fever_low_grade"],
        "urgency": "urgent",
        "description": "Acute hepatocyte necrosis characterized by icteric sclerae, dark tea-colored urine, right upper quadrant pain, and profound fatigue.",
    },

    # 2. Cardiovascular (10)
    "Acute Myocardial Infarction": {
        "id": "acute_myocardial_infarction",
        "category": "Cardiology",
        "icd10": "I21.9",
        "pathognomonic_symptoms": ["chest_pain", "dyspnea", "excessive_sweating", "syncope"],
        "secondary_symptoms": ["nausea", "palpitations", "dizziness"],
        "urgency": "emergency",
        "description": "Ischemic myocardial necrosis causing crushing substernal chest pressure, radiation to left arm or jaw, Levine sign, and cold diaphoresis.",
    },
    "Congestive Heart Failure": {
        "id": "congestive_heart_failure",
        "category": "Cardiology",
        "icd10": "I50.9",
        "pathognomonic_symptoms": ["orthopnea", "paroxysmal_nocturnal_dyspnea", "leg_swelling", "dyspnea"],
        "secondary_symptoms": ["fatigue", "cough", "weight_gain"],
        "urgency": "urgent",
        "description": "Impaired ventricular pump function with waking up gasping at night, orthopnea requiring elevation, and bilateral pitting ankle edema.",
    },
    "Essential Hypertension": {
        "id": "essential_hypertension",
        "category": "Cardiology",
        "icd10": "I10",
        "pathognomonic_symptoms": ["headache", "dizziness", "blurred_vision"],
        "secondary_symptoms": ["palpitations", "epistaxis", "fatigue"],
        "urgency": "routine",
        "description": "Persistently elevated systemic vascular resistance causing occipital morning headaches, lightheadedness, and visual blurring.",
    },
    "Infective Endocarditis": {
        "id": "infective_endocarditis",
        "category": "Cardiology",
        "icd10": "I33.0",
        "pathognomonic_symptoms": ["fever", "chills", "night_sweats", "fatigue", "petechiae"],
        "secondary_symptoms": ["dyspnea", "joint_pain", "chest_pain"],
        "urgency": "emergency",
        "description": "Microbial infection of valvular endocardium manifesting with bacteremic fevers, peripheral stigmata, splinter hemorrhages, and petechiae.",
    },
    "Atrial Fibrillation": {
        "id": "atrial_fibrillation",
        "category": "Cardiology",
        "icd10": "I48.91",
        "pathognomonic_symptoms": ["palpitations", "dyspnea", "dizziness", "fatigue"],
        "secondary_symptoms": ["chest_pain", "presyncope", "anxiety"],
        "urgency": "urgent",
        "description": "Supraventricular tachyarrhythmia with irregularly irregular rapid heartbeat, sensation of chest fluttering, and effort breathlessness.",
    },
    "Deep Vein Thrombosis": {
        "id": "deep_vein_thrombosis",
        "category": "Cardiology",
        "icd10": "I82.40",
        "pathognomonic_symptoms": ["leg_swelling", "erythema", "focal_weakness"],
        "secondary_symptoms": ["claudication", "calf_pain", "edema"],
        "urgency": "urgent",
        "description": "Thrombotic occlusion of deep venous sinuses causing unilateral calf swelling, erythema, localized warmth, and pain with dorsiflexion.",
    },
    "Angina Pectoris": {
        "id": "angina_pectoris",
        "category": "Cardiology",
        "icd10": "I20.9",
        "pathognomonic_symptoms": ["chest_pain", "chest_tightness", "dyspnea"],
        "secondary_symptoms": ["fatigue", "palpitations", "dizziness"],
        "urgency": "urgent",
        "description": "Transient myocardial ischemia producing exertional retrosternal heaviness and tightness relieved by rest or sublingual nitrates.",
    },
    "Acute Pericarditis": {
        "id": "acute_pericarditis",
        "category": "Cardiology",
        "icd10": "I30.9",
        "pathognomonic_symptoms": ["pleuritic_chest_pain", "chest_pain", "fever"],
        "secondary_symptoms": ["dyspnea", "cough", "palpitations"],
        "urgency": "urgent",
        "description": "Pericardial inflammation causing sharp pleuritic chest pain aggravated by supine posture or deep inspiration and relieved by leaning forward.",
    },
    "Peripheral Artery Disease": {
        "id": "peripheral_artery_disease",
        "category": "Cardiology",
        "icd10": "I73.9",
        "pathognomonic_symptoms": ["claudication", "leg_swelling", "numbness"],
        "secondary_symptoms": ["focal_weakness", "tingling", "cold_extremities"],
        "urgency": "routine",
        "description": "Atherosclerotic stenoses in lower extremities provoking reproducible exercise-induced calf claudication relieved within minutes of rest.",
    },
    "Aortic Stenosis": {
        "id": "aortic_stenosis",
        "category": "Cardiology",
        "icd10": "I35.0",
        "pathognomonic_symptoms": ["syncope", "chest_pain", "dyspnea", "fatigue"],
        "secondary_symptoms": ["palpitations", "presyncope", "dizziness"],
        "urgency": "urgent",
        "description": "Fixed obstruction to left ventricular outflow manifesting with classical triad of exertional dyspnea, angina pectoris, and exertional syncope.",
    },

    # 3. Pulmonology (10)
    "Bronchial Asthma": {
        "id": "bronchial_asthma",
        "category": "Pulmonology",
        "icd10": "J45.909",
        "pathognomonic_symptoms": ["wheezing", "chest_tightness", "cough", "dyspnea"],
        "secondary_symptoms": ["tachypnea", "nighttime_cough", "sputum_production"],
        "urgency": "urgent",
        "description": "Reversible airway hyperreactivity presenting with audible expiratory wheezing, chest tightness in cold air, and nocturnal dry cough.",
    },
    "Chronic Obstructive Pulmonary Disease": {
        "id": "chronic_obstructive_pulmonary_disease",
        "category": "Pulmonology",
        "icd10": "J44.9",
        "pathognomonic_symptoms": ["dyspnea", "cough", "sputum_production"],
        "secondary_symptoms": ["wheezing", "barrel_chest", "fatigue"],
        "urgency": "urgent",
        "description": "Progressive airflow limitation in long-term smokers with chronic cough, barrel chest deformity, and exertional breathlessness with clear/white sputum.",
    },
    "Acute Bronchitis": {
        "id": "acute_bronchitis",
        "category": "Pulmonology",
        "icd10": "J20.9",
        "pathognomonic_symptoms": ["cough", "purulent_sputum", "fever_low_grade", "fatigue"],
        "secondary_symptoms": ["chest_tightness", "sore_throat", "rhinorrhea"],
        "urgency": "routine",
        "description": "Transient tracheobronchial inflammation following viral infection with prominent hacking cough and mucopurulent sputum.",
    },
    "Pulmonary Embolism": {
        "id": "pulmonary_embolism",
        "category": "Pulmonology",
        "icd10": "I26.99",
        "pathognomonic_symptoms": ["pleuritic_chest_pain", "dyspnea", "hemoptysis", "tachypnea"],
        "secondary_symptoms": ["tachycardia", "syncope", "cough"],
        "urgency": "emergency",
        "description": "Sudden occlusion of pulmonary arterial tree after prolonged immobility presenting with acute pleuritic chest pain, tachypnea, and hemoptysis.",
    },
    "Bronchiectasis": {
        "id": "bronchiectasis",
        "category": "Pulmonology",
        "icd10": "J47.9",
        "pathognomonic_symptoms": ["cough", "purulent_sputum", "hemoptysis", "dyspnea"],
        "secondary_symptoms": ["wheezing", "fatigue", "weight_loss"],
        "urgency": "urgent",
        "description": "Irreversible bronchial dilation causing chronic copious daily foul-smelling purulent sputum, recurrent hemoptysis, and dyspnea.",
    },
    "Pleurisy": {
        "id": "pleurisy",
        "category": "Pulmonology",
        "icd10": "R09.1",
        "pathognomonic_symptoms": ["pleuritic_chest_pain", "dyspnea", "cough"],
        "secondary_symptoms": ["fever_low_grade", "tachypnea", "fatigue"],
        "urgency": "routine",
        "description": "Inflammation of parietal pleura producing knife-like chest pain provoked by inspiration, sneezing, or cough.",
    },
    "Spontaneous Pneumothorax": {
        "id": "spontaneous_pneumothorax",
        "category": "Pulmonology",
        "icd10": "J93.9",
        "pathognomonic_symptoms": ["pleuritic_chest_pain", "dyspnea", "tachypnea"],
        "secondary_symptoms": ["cyanosis", "chest_tightness", "tachycardia"],
        "urgency": "emergency",
        "description": "Rupture of subpleural apical blebs presenting with abrupt unilateral tearing chest pain and acute breathless distress without fever.",
    },
    "Idiopathic Pulmonary Fibrosis": {
        "id": "idiopathic_pulmonary_fibrosis",
        "category": "Pulmonology",
        "icd10": "J84.112",
        "pathognomonic_symptoms": ["dyspnea", "cough", "fatigue", "nail_clubbing"],
        "secondary_symptoms": ["weight_loss", "chest_pain", "tachypnea"],
        "urgency": "urgent",
        "description": "Chronic progressive parenchymal fibrosing interstitial pneumonia causing insidious dry cough, Velcro-like rales, and digital clubbing.",
    },
    "Obstructive Sleep Apnea": {
        "id": "obstructive_sleep_apnea",
        "category": "Pulmonology",
        "icd10": "G47.33",
        "pathognomonic_symptoms": ["snoring", "excessive_daytime_sleepiness", "fatigue", "headache"],
        "secondary_symptoms": ["insomnia", "nocturia", "memory_loss"],
        "urgency": "routine",
        "description": "Repetitive upper airway collapse during sleep manifesting with habitual loud snoring, witnessed apneas, morning headaches, and hypersomnolence.",
    },
    "Croup": {
        "id": "croup",
        "category": "Pulmonology",
        "icd10": "J05.0",
        "pathognomonic_symptoms": ["stridor", "cough", "hoarseness"],
        "secondary_symptoms": ["dyspnea", "fever_low_grade", "tachypnea"],
        "urgency": "urgent",
        "description": "Parainfluenza laryngotracheobronchitis in young pediatric patients featuring hallmark barking seal-like cough, inspiratory stridor, and hoarseness.",
    },

    # 4. Gastroenterology & Hepatic (10)
    "Gastroesophageal Reflux Disease": {
        "id": "gastroesophageal_reflux_disease",
        "category": "Gastroenterology",
        "icd10": "K21.9",
        "pathognomonic_symptoms": ["heartburn", "dysphagia", "acid_reflux"],
        "secondary_symptoms": ["odynophagia", "chest_pain", "cough"],
        "urgency": "routine",
        "description": "Retrograde flow of gastric contents causing substernal pyrosis behind breastbone, sour acid regurgitation, and water brash.",
    },
    "Peptic Ulcer Disease": {
        "id": "peptic_ulcer_disease",
        "category": "Gastroenterology",
        "icd10": "K27.9",
        "pathognomonic_symptoms": ["abdominal_pain", "melena", "heartburn"],
        "secondary_symptoms": ["nausea", "vomiting", "early_satiety"],
        "urgency": "urgent",
        "description": "Mucosal erosion in stomach or duodenum causing burning epigastric gnawing pain relieved by meals or antacids, with dark tarry stools.",
    },
    "Acute Pancreatitis": {
        "id": "acute_pancreatitis",
        "category": "Gastroenterology",
        "icd10": "K85.90",
        "pathognomonic_symptoms": ["abdominal_pain", "vomiting", "nausea"],
        "secondary_symptoms": ["fever", "tachycardia", "distended_abdomen"],
        "urgency": "emergency",
        "description": "Autodigestion of pancreatic parenchyma characterized by severe continuous epigastric pain radiating directly to back, relieved by fetal posture.",
    },
    "Acute Cholecystitis": {
        "id": "acute_cholecystitis",
        "category": "Gastroenterology",
        "icd10": "K81.0",
        "pathognomonic_symptoms": ["abdominal_pain", "nausea", "vomiting", "fever"],
        "secondary_symptoms": ["jaundice", "anorexia", "dark_urine"],
        "urgency": "urgent",
        "description": "Cystic duct gallstone impaction with right upper quadrant tenderness after fatty ingestion, positive Murphy sign, and right shoulder radiation.",
    },
    "Acute Appendicitis": {
        "id": "acute_appendicitis_cond",
        "category": "Gastroenterology",
        "icd10": "K35.80",
        "pathognomonic_symptoms": ["abdominal_pain", "nausea", "fever_low_grade"],
        "secondary_symptoms": ["acute_appendicitis", "rebound_tenderness", "right_lower_quadrant_pain", "periumbilical_pain"],
        "urgency": "emergency",
        "description": "Acute appendiceal lumen obstruction with dull periumbilical ache migrating to sharp right lower quadrant McBurney point tenderness and rebound pain.",
    },
    "Liver Cirrhosis": {
        "id": "liver_cirrhosis",
        "category": "Gastroenterology",
        "icd10": "K74.60",
        "pathognomonic_symptoms": ["jaundice", "ascites", "dark_urine", "easy_bruising"],
        "secondary_symptoms": ["fatigue", "pruritus_ani", "clay_colored_stools"],
        "urgency": "urgent",
        "description": "End-stage hepatic parenchymal fibrosis with portal hypertension causing yellow jaundice, distended fluid belly ascites, spider angiomas, and coagulopathy.",
    },
    "Ulcerative Colitis": {
        "id": "ulcerative_colitis",
        "category": "Gastroenterology",
        "icd10": "K51.90",
        "pathognomonic_symptoms": ["diarrhea", "hematochezia", "abdominal_pain", "tenesmus"],
        "secondary_symptoms": ["weight_loss", "fatigue", "fever_low_grade"],
        "urgency": "urgent",
        "description": "Continuous mucosal inflammation of colon causing frequent bloody mucus-laden diarrhea, lower abdominal cramping, and rectal tenesmus.",
    },
    "Crohn's Disease": {
        "id": "crohns_disease",
        "category": "Gastroenterology",
        "icd10": "K50.90",
        "pathognomonic_symptoms": ["diarrhea", "abdominal_pain", "weight_loss", "fatigue"],
        "secondary_symptoms": ["fever_low_grade", "ulcers_oral", "joint_pain"],
        "urgency": "urgent",
        "description": "Transmural granulomatous enteritis with skip lesions, non-bloody chronic diarrhea, recurrent crampy abdominal pain, and weight loss.",
    },
    "Acute Diverticulitis": {
        "id": "acute_diverticulitis",
        "category": "Gastroenterology",
        "icd10": "K57.92",
        "pathognomonic_symptoms": ["abdominal_pain", "fever", "constipation", "nausea"],
        "secondary_symptoms": ["diarrhea", "vomiting", "bloating"],
        "urgency": "urgent",
        "description": "Microperforation in colonic outpouchings presenting with constant left lower quadrant pain, pyrexia, altered bowel habits, and leukocytosis.",
    },
    "Celiac Disease": {
        "id": "celiac_disease",
        "category": "Gastroenterology",
        "icd10": "K90.0",
        "pathognomonic_symptoms": ["steatorrhea", "bloating", "diarrhea", "weight_loss"],
        "secondary_symptoms": ["fatigue", "abdominal_pain", "flatulence"],
        "urgency": "routine",
        "description": "Gluten-sensitive autoimmune enteropathy presenting with chronic abdominal distension, bulky foul-smelling fatty stools, and unexplained iron deficiency.",
    },

    # 5. Neurology (10)
    "Migraine": {
        "id": "migraine",
        "category": "Neurology",
        "icd10": "G43.909",
        "pathognomonic_symptoms": ["headache", "photophobia", "phonophobia", "visual_aura", "nausea"],
        "secondary_symptoms": ["vomiting", "dizziness", "fatigue"],
        "urgency": "routine",
        "description": "Neurovascular cephalalgia featuring unilateral throbbing pulsating hemicranial headache, scintillating visual scotomas, photophobia, and phonophobia.",
    },
    "Cluster Headache": {
        "id": "cluster_headache",
        "category": "Neurology",
        "icd10": "G44.009",
        "pathognomonic_symptoms": ["headache", "eye_pain", "epiphora", "rhinorrhea"],
        "secondary_symptoms": ["nasal_congestion", "facial_sweating", "restlessness"],
        "urgency": "urgent",
        "description": "Trigeminal autonomic cephalalgia provoking excruciating strictly unilateral orbital boring pain accompanied by ipsilateral lacrimation and rhinorrhea.",
    },
    "Tension Headache": {
        "id": "tension_headache",
        "category": "Neurology",
        "icd10": "G44.209",
        "pathognomonic_symptoms": ["headache", "body_aches"],
        "secondary_symptoms": ["fatigue", "insomnia", "dizziness", "photophobia"],
        "urgency": "routine",
        "description": "Bilateral band-like constricting pressure across forehead and occiput without nausea, aggravated by emotional stress or muscle fatigue.",
    },
    "Ischemic Stroke": {
        "id": "ischemic_stroke",
        "category": "Neurology",
        "icd10": "I63.9",
        "pathognomonic_symptoms": ["focal_weakness", "dysarthria", "facial_droop"],
        "secondary_symptoms": ["aphasia", "ataxia", "confusion"],
        "urgency": "emergency",
        "description": "Acute focal cerebral infarction causing sudden onset hemiparesis of arm and leg, garbled slurred speech, and facial asymmetry.",
    },
    "Transient Ischemic Attack": {
        "id": "transient_ischemic_attack",
        "category": "Neurology",
        "icd10": "G45.9",
        "pathognomonic_symptoms": ["focal_weakness", "dysarthria", "dizziness"],
        "secondary_symptoms": ["facial_droop", "diplopia", "presyncope"],
        "urgency": "emergency",
        "description": "Brief episode of neurological dysfunction caused by focal brain ischemia with complete symptom resolution within 24 hours.",
    },
    "Benign Paroxysmal Positional Vertigo": {
        "id": "benign_paroxysmal_positional_vertigo",
        "category": "Neurology",
        "icd10": "H81.10",
        "pathognomonic_symptoms": ["vertigo", "nausea", "gait_unsteadiness"],
        "secondary_symptoms": ["vomiting", "dizziness", "nystagmus"],
        "urgency": "routine",
        "description": "Dislodged canaliths provoking brief intense rotational room-spinning vertigo triggered by turning head in bed or looking up.",
    },
    "Parkinson's Disease": {
        "id": "parkinsons_disease",
        "category": "Neurology",
        "icd10": "G20",
        "pathognomonic_symptoms": ["tremor", "gait_unsteadiness", "focal_weakness"],
        "secondary_symptoms": ["rigidity", "bradykinesia", "fatigue"],
        "urgency": "routine",
        "description": "Nigrostriatal dopaminergic neurodegeneration with asymmetric resting pill-rolling hand tremor, cogwheel rigidity, and shuffling gait.",
    },
    "Bell's Palsy": {
        "id": "bells_palsy",
        "category": "Neurology",
        "icd10": "G51.0",
        "pathognomonic_symptoms": ["facial_droop", "loss_of_taste", "ear_pain"],
        "secondary_symptoms": ["epiphora", "facial_palsy", "cranial_nerve_deficit"],
        "urgency": "routine",
        "description": "Acute idiopathic peripheral facial nerve paresis causing inability to close eye, forehead smoothing, corner of mouth drooping, and hyperacusis.",
    },
    "Acute Bacterial Meningitis": {
        "id": "acute_bacterial_meningitis",
        "category": "Neurology",
        "icd10": "G00.9",
        "pathognomonic_symptoms": ["stiff_neck", "fever", "headache", "altered_mental_status", "photophobia"],
        "secondary_symptoms": ["nausea", "vomiting", "purpura"],
        "urgency": "emergency",
        "description": "Leptomeningeal bacterial infection presenting with classic triad of nuchal rigidity, high spiking fever, intractable headache, and altered mentation.",
    },
    "Sciatica": {
        "id": "sciatica",
        "category": "Neurology",
        "icd10": "M54.30",
        "pathognomonic_symptoms": ["sciatica", "focal_weakness", "numbness", "tingling"],
        "secondary_symptoms": ["joint_pain", "gait_unsteadiness", "muscle_cramps"],
        "urgency": "routine",
        "description": "Lumbosacral radiculopathy causing lancinating shock-like electric pain radiating down buttock, posterior thigh, calf, and foot.",
    },

    # 6. Endocrinology & Metabolic (10)
    "Type 1 Diabetes": {
        "id": "type_1_diabetes",
        "category": "Endocrinology",
        "icd10": "E10.9",
        "pathognomonic_symptoms": ["polydipsia", "polyuria", "weight_loss", "hyperphagia", "fatigue"],
        "secondary_symptoms": ["blurred_vision", "nausea", "weakness"],
        "urgency": "urgent",
        "description": "Autoimmune pancreatic beta-cell destruction manifesting with unquenchable thirst, frequent nighttime urination, rapid weight loss, and polyphagia.",
    },
    "Type 2 Diabetes": {
        "id": "type_2_diabetes",
        "category": "Endocrinology",
        "icd10": "E11.9",
        "pathognomonic_symptoms": ["polyuria", "polydipsia", "fatigue", "blurred_vision"],
        "secondary_symptoms": ["weight_loss", "hyperphagia", "slow_healing"],
        "urgency": "routine",
        "description": "Peripheral insulin resistance with progressive secretory defect causing chronic mild polyuria, polydipsia, fatigue, and osmotic blurred vision.",
    },
    "Hypothyroidism": {
        "id": "hypothyroidism",
        "category": "Endocrinology",
        "icd10": "E03.9",
        "pathognomonic_symptoms": ["cold_intolerance", "weight_gain", "constipation", "fatigue", "hair_loss"],
        "secondary_symptoms": ["dry_skin", "generalized_weakness", "goiter"],
        "urgency": "routine",
        "description": "Systemic thyroid hormone deficiency causing chronic fatigue, cold intolerance, unexplained weight gain, severe constipation, and coarse hair loss.",
    },
    "Hyperthyroidism": {
        "id": "hyperthyroidism",
        "category": "Endocrinology",
        "icd10": "E05.90",
        "pathognomonic_symptoms": ["heat_intolerance", "palpitations", "tremor", "weight_loss"],
        "secondary_symptoms": ["hyperphagia", "excessive_sweating", "goiter"],
        "urgency": "routine",
        "description": "Hypermetabolic thyrotoxic state causing resting sinus tachycardia, fine hand tremors, heat intolerance, and rapid weight loss despite increased appetite.",
    },
    "Cushing's Syndrome": {
        "id": "cushings_syndrome",
        "category": "Endocrinology",
        "icd10": "E24.9",
        "pathognomonic_symptoms": ["weight_gain", "easy_bruising", "generalized_weakness", "hirsutism"],
        "secondary_symptoms": ["moon_facies", "hypertension", "fatigue"],
        "urgency": "routine",
        "description": "Hypercortisolemia characterized by central truncal adiposity, purple striae, easy skin bruising, proximal muscle weakness, and hirsutism.",
    },
    "Addison's Disease": {
        "id": "addisons_disease",
        "category": "Endocrinology",
        "icd10": "E27.1",
        "pathognomonic_symptoms": ["fatigue", "weight_loss", "dizziness", "anorexia"],
        "secondary_symptoms": ["hyperpigmentation", "nausea", "salt_craving"],
        "urgency": "urgent",
        "description": "Primary adrenocortical insufficiency manifesting with bronzing of palmar skin creases, orthostatic hypotension, salt craving, and progressive cachexia.",
    },
    "Acute Gout": {
        "id": "acute_gout",
        "category": "Endocrinology",
        "icd10": "M10.9",
        "pathognomonic_symptoms": ["joint_pain", "joint_swelling", "erythema", "myalgia"],
        "secondary_symptoms": ["fever_low_grade", "podagra", "tender_joint"],
        "urgency": "urgent",
        "description": "Monosodium urate crystal synovitis causing excruciating sudden pain, erythema, and fiery warmth over first metatarsophalangeal joint (podagra).",
    },
    "Hypoglycemia": {
        "id": "hypoglycemia",
        "category": "Endocrinology",
        "icd10": "E16.2",
        "pathognomonic_symptoms": ["hypoglycemia_symptoms", "excessive_sweating", "tremor", "dizziness", "palpitations"],
        "secondary_symptoms": ["confusion", "fatigue", "hunger"],
        "urgency": "urgent",
        "description": "Acute neuroglycopenic crisis characterized by profuse cold diaphoresis, jitteriness, fine tremor, palpitations, hunger, and lightheadedness.",
    },
    "Diabetic Ketoacidosis": {
        "id": "diabetic_ketoacidosis",
        "category": "Endocrinology",
        "icd10": "E10.10",
        "pathognomonic_symptoms": ["polyuria", "polydipsia", "vomiting", "abdominal_pain", "confusion"],
        "secondary_symptoms": ["fruity_breath", "dehydration", "tachypnea"],
        "urgency": "emergency",
        "description": "Acute metabolic crisis from absolute insulin lack producing Kussmaul respirations, acetone fruity breath, diffuse abdominal pain, and ketonuria.",
    },
    "Primary Hyperparathyroidism": {
        "id": "primary_hyperparathyroidism",
        "category": "Endocrinology",
        "icd10": "E21.0",
        "pathognomonic_symptoms": ["bone_pain", "polyuria", "abdominal_pain", "fatigue"],
        "secondary_symptoms": ["constipation", "nephrolithiasis", "generalized_weakness"],
        "urgency": "routine",
        "description": "Autonomous parathyroid hormone hypersecretion causing stones, painful bones, abdominal groans, polyuria, and psychiatric moans.",
    },

    # 7. Nephrology & Urology (10)
    "Acute Cystitis": {
        "id": "acute_cystitis_cond",
        "category": "Nephrology & Urology",
        "icd10": "N30.00",
        "pathognomonic_symptoms": ["dysuria", "urinary_urgency", "urinary_frequency", "suprapubic_pain"],
        "secondary_symptoms": ["hematuria", "nocturia", "cloudy_urine"],
        "urgency": "routine",
        "description": "Superficial bacterial bladder infection producing intense scalding dysuria, small-volume urinary frequency, urgency, and suprapubic cramping.",
    },
    "Acute Pyelonephritis": {
        "id": "acute_pyelonephritis_cond",
        "category": "Nephrology & Urology",
        "icd10": "N10",
        "pathognomonic_symptoms": ["flank_pain", "fever", "chills", "dysuria"],
        "secondary_symptoms": ["nausea", "vomiting", "urinary_frequency"],
        "urgency": "urgent",
        "description": "Upper urinary tract parenchymal infection presenting with acute costovertebral angle flank pain, shaking rigors, high spiking fever, and pyuria.",
    },
    "Nephrolithiasis": {
        "id": "nephrolithiasis",
        "category": "Nephrology/Urology",
        "icd10": "N20.0",
        "pathognomonic_symptoms": ["flank_pain", "hematuria"],
        "secondary_symptoms": ["nausea", "vomiting", "dysuria", "urinary_frequency"],
        "urgency": "urgent",
        "description": "Calculus migration within ureter provoking excruciating colicky flank spasms radiating toward ipsilateral groin, with frank hematuria.",
    },
    "Acute Kidney Injury": {
        "id": "acute_kidney_injury",
        "category": "Nephrology & Urology",
        "icd10": "N17.9",
        "pathognomonic_symptoms": ["oliguria", "leg_swelling", "fatigue", "nausea"],
        "secondary_symptoms": ["confusion", "dyspnea", "anuria"],
        "urgency": "emergency",
        "description": "Abrupt decline in renal excretory clearance leading to acute oliguria, peripheral volume overload edema, and progressive azotemic nausea.",
    },
    "Chronic Kidney Disease": {
        "id": "chronic_kidney_disease",
        "category": "Nephrology & Urology",
        "icd10": "N18.9",
        "pathognomonic_symptoms": ["fatigue", "leg_swelling", "pruritus_ani", "anorexia", "frothy_urine"],
        "secondary_symptoms": ["nocturia", "nausea", "hypertension"],
        "urgency": "routine",
        "description": "Longstanding renal parenchymal attrition resulting in persistent proteinuria frothy urine, periorbital/pretibial edema, uremic pruritus, and anemia.",
    },
    "Benign Prostatic Hyperplasia": {
        "id": "benign_prostatic_hyperplasia",
        "category": "Nephrology & Urology",
        "icd10": "N40.0",
        "pathognomonic_symptoms": ["urinary_hesitancy", "nocturia", "urinary_frequency"],
        "secondary_symptoms": ["dysuria", "weak_stream", "incomplete_emptying"],
        "urgency": "routine",
        "description": "Adenomatous periurethral stromal proliferation producing hesitancy, weak interrupted urinary stream, nocturia waking >3 times, and post-void dribbling.",
    },
    "Nephrotic Syndrome": {
        "id": "nephrotic_syndrome",
        "category": "Nephrology & Urology",
        "icd10": "N04.9",
        "pathognomonic_symptoms": ["leg_swelling", "frothy_urine", "ascites", "fatigue"],
        "secondary_symptoms": ["weight_gain", "anorexia", "edema"],
        "urgency": "urgent",
        "description": "Glomerular podocyte effacement with heavy proteinuria (>3.5 g/day), frothy urine, profound hypoalbuminemia, anasarca edema, and ascites.",
    },
    "Acute Glomerulonephritis": {
        "id": "acute_glomerulonephritis",
        "category": "Nephrology & Urology",
        "icd10": "N00.9",
        "pathognomonic_symptoms": ["hematuria", "frothy_urine", "leg_swelling", "headache"],
        "secondary_symptoms": ["oliguria", "hypertension", "fatigue"],
        "urgency": "urgent",
        "description": "Immune complex glomerular endotheliosis provoking classic nephritic syndrome: smoky tea-colored hematuria, hypertension, and facial puffiness.",
    },
    "Urethritis": {
        "id": "urethritis",
        "category": "Nephrology & Urology",
        "icd10": "N34.2",
        "pathognomonic_symptoms": ["dysuria", "penile_discharge", "urinary_frequency"],
        "secondary_symptoms": ["itching", "urinary_urgency", "pelvic_pain"],
        "urgency": "routine",
        "description": "Infectious inflammation of the urethral mucosa characterized by meatal pruritus, painful stinging urination, and mucoid/purulent discharge.",
    },
    "Interstitial Cystitis": {
        "id": "interstitial_cystitis",
        "category": "Nephrology & Urology",
        "icd10": "N30.10",
        "pathognomonic_symptoms": ["suprapubic_pain", "dysuria", "urinary_frequency", "urinary_urgency"],
        "secondary_symptoms": ["pelvic_pain", "nocturia", "dyspareunia"],
        "urgency": "routine",
        "description": "Chronic painful bladder syndrome characterized by suprapubic pelvic discomfort that worsens with bladder filling and is temporarily relieved by voiding.",
    },

    # 8. Rheumatology & Musculoskeletal (10)
    "Osteoarthritis": {
        "id": "osteoarthritis",
        "category": "Rheumatology",
        "icd10": "M19.90",
        "pathognomonic_symptoms": ["joint_pain", "morning_stiffness", "joint_swelling"],
        "secondary_symptoms": ["crepitus", "bone_spurs", "limited_mobility"],
        "urgency": "routine",
        "description": "Non-inflammatory degenerative cartilage loss causing deep mechanical joint aching aggravated by weight-bearing and brief morning stiffness (<30 min).",
    },
    "Rheumatoid Arthritis": {
        "id": "rheumatoid_arthritis",
        "category": "Rheumatology",
        "icd10": "M06.9",
        "pathognomonic_symptoms": ["joint_pain", "joint_swelling", "morning_stiffness"],
        "secondary_symptoms": ["fatigue", "fever_low_grade", "rheumatoid_nodules"],
        "urgency": "routine",
        "description": "Systemic autoimmune synovitis provoking symmetric swelling and boggy tenderness of MCP and PIP hand joints with morning stiffness lasting >1 hour.",
    },
    "Systemic Lupus Erythematosus": {
        "id": "systemic_lupus_erythematosus",
        "category": "Rheumatology/Immunology",
        "icd10": "M32.9",
        "pathognomonic_symptoms": ["butterfly_rash", "photosensitivity", "joint_pain", "fatigue"],
        "secondary_symptoms": ["fever_low_grade", "ulcers_oral", "hair_loss"],
        "urgency": "urgent",
        "description": "Multisystem autoimmune connective tissue disease presenting with photosensitive malar butterfly rash across cheeks and nose, arthralgias, and fatigue.",
    },
    "Ankylosing Spondylitis": {
        "id": "ankylosing_spondylitis",
        "category": "Rheumatology",
        "icd10": "M45.9",
        "pathognomonic_symptoms": ["morning_stiffness", "joint_pain", "generalized_weakness"],
        "secondary_symptoms": ["fatigue", "limited_spine_mobility", "chest_pain"],
        "urgency": "routine",
        "description": "Seronegative HLA-B27 spondyloarthropathy causing chronic inflammatory low back pain and buttock stiffness waking patient at night, relieved by exercise.",
    },
    "Fibromyalgia": {
        "id": "fibromyalgia",
        "category": "Rheumatology",
        "icd10": "M79.7",
        "pathognomonic_symptoms": ["body_aches", "fatigue", "insomnia", "generalized_weakness"],
        "secondary_symptoms": ["headache", "brain_fog", "morning_stiffness"],
        "urgency": "routine",
        "description": "Central pain amplification syndrome with chronic widespread musculoskeletal aching across multiple tender points, unrefreshing sleep, and brain fog.",
    },
    "Polymyalgia Rheumatica": {
        "id": "polymyalgia_rheumatica",
        "category": "Rheumatology",
        "icd10": "M35.3",
        "pathognomonic_symptoms": ["morning_stiffness", "joint_pain", "generalized_weakness", "fatigue"],
        "secondary_symptoms": ["fever_low_grade", "weight_loss", "anorexia"],
        "urgency": "routine",
        "description": "Inflammatory disorder in elderly individuals causing bilateral aching and severe morning stiffness across shoulder and pelvic girdles.",
    },
    "Systemic Sclerosis": {
        "id": "systemic_sclerosis",
        "category": "Rheumatology",
        "icd10": "M34.9",
        "pathognomonic_symptoms": ["raynaud_phenomenon", "skin_thickening", "dysphagia", "joint_pain"],
        "secondary_symptoms": ["fatigue", "telangiectasia", "cough"],
        "urgency": "urgent",
        "description": "Microvascular obliterative collagen deposition resulting in tricolor Raynaud cold fingers, sclerodactyly skin thickening, and esophageal aperistalsis.",
    },
    "Sjögren's Syndrome": {
        "id": "sjogrens_syndrome",
        "category": "Rheumatology",
        "icd10": "M35.00",
        "pathognomonic_symptoms": ["dry_eyes", "dry_mouth", "fatigue", "joint_pain"],
        "secondary_symptoms": ["dry_skin", "swollen_glands", "difficulty_swallowing"],
        "urgency": "routine",
        "description": "Autoimmune exocrine gland destruction resulting in chronic keratoconjunctivitis sicca (dry eyes), xerostomia (dry mouth), and arthralgias.",
    },
    "Psoriatic Arthritis": {
        "id": "psoriatic_arthritis",
        "category": "Rheumatology",
        "icd10": "L40.50",
        "pathognomonic_symptoms": ["joint_pain", "joint_swelling", "skin_rash", "scaly_rash", "nail_clubbing"],
        "secondary_symptoms": ["morning_stiffness", "dactylitis", "fatigue"],
        "urgency": "routine",
        "description": "Inflammatory seronegative arthritis associated with plaque psoriasis, sausage-digit dactylitis, DIP joint involvement, and nail pitting.",
    },
    "Dermatomyositis": {
        "id": "dermatomyositis",
        "category": "Rheumatology",
        "icd10": "M33.90",
        "pathognomonic_symptoms": ["focal_weakness", "skin_rash", "photosensitivity", "myalgia"],
        "secondary_symptoms": ["dysphagia", "fatigue", "heliotrope_rash"],
        "urgency": "urgent",
        "description": "Immune-mediated microangiopathy causing symmetric proximal muscle weakness, heliotrope violaceous eyelid rash, and Gottron papules on knuckles.",
    },

    # 9. Dermatology (10)
    "Plaque Psoriasis": {
        "id": "plaque_psoriasis",
        "category": "Dermatology",
        "icd10": "L40.0",
        "pathognomonic_symptoms": ["skin_rash", "scaly_rash", "itching", "skin_peeling", "erythema"],
        "secondary_symptoms": ["joint_pain", "nail_clubbing", "dry_skin"],
        "urgency": "routine",
        "description": "Hyperproliferative autoimmune dermatosis presenting with sharply demarcated salmon-pink plaques covered with silvery micaceous scales on extensor knees/elbows and nail pitting.",
    },
    "Atopic Dermatitis": {
        "id": "atopic_dermatitis",
        "category": "Dermatology",
        "icd10": "L20.9",
        "pathognomonic_symptoms": ["itching", "skin_rash", "erythema"],
        "secondary_symptoms": ["skin_peeling", "dry_skin", "lichenification"],
        "urgency": "routine",
        "description": "Chronic relapsing pruritic eczematous dermatosis with intense itching and dry lichenified plaques in flexural creases of elbows and knees.",
    },
    "Herpes Zoster": {
        "id": "herpes_zoster",
        "category": "Dermatology",
        "icd10": "B02.9",
        "pathognomonic_symptoms": ["skin_rash", "erythema", "body_aches"],
        "secondary_symptoms": ["bullae", "itching", "stabbing_nerve_pain"],
        "urgency": "urgent",
        "description": "Reactivation of latent varicella-zoster virus causing unilateral dermatomal band of clustered painful fluid-filled vesicles preceded by burning neuralgia.",
    },
    "Cellulitis": {
        "id": "cellulitis",
        "category": "Dermatology",
        "icd10": "L03.90",
        "pathognomonic_symptoms": ["erythema", "leg_swelling", "fever"],
        "secondary_symptoms": ["skin_warmth", "tender_skin", "lymphadenopathy"],
        "urgency": "urgent",
        "description": "Acute spreading pyogenic dermis and subcutaneous infection with rapidly advancing warm red tender swollen borders and systemic fever.",
    },
    "Scabies": {
        "id": "scabies",
        "category": "Dermatology",
        "icd10": "B86",
        "pathognomonic_symptoms": ["itching", "skin_rash"],
        "secondary_symptoms": ["burrows", "excoriations", "nocturnal_pruritus"],
        "urgency": "routine",
        "description": "Sarcoptes scabiei mite infestation producing intractable nocturnal pruritus and serpiginous web-space burrows between fingers and wrists.",
    },
    "Acute Urticaria": {
        "id": "acute_urticaria",
        "category": "Dermatology",
        "icd10": "L50.9",
        "pathognomonic_symptoms": ["hives", "itching", "erythema"],
        "secondary_symptoms": ["swelling", "flushing", "burning_skin"],
        "urgency": "routine",
        "description": "Mast cell degranulation triggering sudden transient pruritic edematous erythematous wheals and hives that resolve within 24 hours.",
    },
    "Contact Dermatitis": {
        "id": "contact_dermatitis",
        "category": "Dermatology",
        "icd10": "L25.9",
        "pathognomonic_symptoms": ["skin_rash", "itching", "erythema", "skin_peeling"],
        "secondary_symptoms": ["bullae", "edema", "burning_skin"],
        "urgency": "routine",
        "description": "Localized delayed-type hypersensitivity reaction occurring at sites of allergen contact with erythema, microvesicles, and intense pruritus.",
    },
    "Impetigo": {
        "id": "impetigo",
        "category": "Dermatology",
        "icd10": "L01.00",
        "pathognomonic_symptoms": ["skin_rash", "bullae", "erythema", "itching"],
        "secondary_symptoms": ["honey_crusts", "skin_peeling", "tender_skin"],
        "urgency": "routine",
        "description": "Superficial epidermal staphylococcal or streptococcal infection characterized by fragile vesicles that rupture into classic honey-colored adherent crusts.",
    },
    "Alopecia Areata": {
        "id": "alopecia_areata",
        "category": "Dermatology",
        "icd10": "L63.9",
        "pathognomonic_symptoms": ["hair_loss"],
        "secondary_symptoms": ["pitting_nails", "itching", "scalp_erythema"],
        "urgency": "routine",
        "description": "T-cell-mediated autoimmune attack on hair bulb follicles resulting in well-circumscribed round or oval patches of sudden non-scarring smooth hair loss.",
    },
    "Erythema Multiforme": {
        "id": "erythema_multiforme",
        "category": "Dermatology",
        "icd10": "L51.9",
        "pathognomonic_symptoms": ["skin_rash", "erythema", "ulcers_oral", "bullae"],
        "secondary_symptoms": ["itching", "fever_low_grade", "joint_pain"],
        "urgency": "urgent",
        "description": "Immune complex hypersensitivity presenting with symmetric target or iris-like cutaneous lesions with central dusky vesiculation and oral mucosal erosion.",
    },

    # 10. ENT & Ophthalmology (10)
    "Acute Otitis Media": {
        "id": "acute_otitis_media",
        "category": "ENT & Ophthalmology",
        "icd10": "H66.90",
        "pathognomonic_symptoms": ["ear_pain", "fever", "hearing_loss"],
        "secondary_symptoms": ["ear_discharge", "headache", "irritability"],
        "urgency": "urgent",
        "description": "Suppurative bacterial middle ear effusion with severe throbbing otalgia, bulging hyperemic tympanic membrane, hearing impairment, and pyrexia.",
    },
    "Acute Sinusitis": {
        "id": "acute_sinusitis",
        "category": "ENT & Ophthalmology",
        "icd10": "J01.90",
        "pathognomonic_symptoms": ["nasal_congestion", "headache", "rhinorrhea", "purulent_sputum"],
        "secondary_symptoms": ["facial_pain", "fever_low_grade", "halitosis"],
        "urgency": "routine",
        "description": "Secondary paranasal sinus inflammation causing facial fullness and maxillary pressure worsening on bending forward, purulent rhinorrhea, and nasal obstruction.",
    },
    "Streptococcal Pharyngitis": {
        "id": "streptococcal_pharyngitis",
        "category": "ENT & Ophthalmology",
        "icd10": "J02.0",
        "pathognomonic_symptoms": ["sore_throat", "fever", "lymphadenopathy"],
        "secondary_symptoms": ["tonsillar_exudates", "headache", "odynophagia"],
        "urgency": "routine",
        "description": "Group A beta-hemolytic streptococcal infection with abrupt severe sore throat, purulent tonsillopharyngeal exudates, high fever, and tender anterior cervical nodes without cough.",
    },
    "Acute Angle-Closure Glaucoma": {
        "id": "acute_angle_closure_glaucoma",
        "category": "ENT & Ophthalmology",
        "icd10": "H40.20X0",
        "pathognomonic_symptoms": ["eye_pain", "headache", "blurred_vision", "nausea"],
        "secondary_symptoms": ["vomiting", "colored_halos", "eye_redness"],
        "urgency": "emergency",
        "description": "Ophthalmic emergency with pupillary block causing sudden unilateral excruciating eye and frontal brow pain, colored halos around lights, hazy steamy cornea, and fixed mid-dilated pupil.",
    },
    "Infectious Conjunctivitis": {
        "id": "infectious_conjunctivitis",
        "category": "ENT & Ophthalmology",
        "icd10": "H10.9",
        "pathognomonic_symptoms": ["eye_redness", "epiphora", "eye_pain", "itching"],
        "secondary_symptoms": ["foreign_body_sensation", "photophobia", "discharge"],
        "urgency": "routine",
        "description": "Infectious conjunctival inflammation producing pink eye erythema, grittiness foreign body sensation, morning eyelid crusting, and epiphora.",
    },
    "Allergic Rhinitis": {
        "id": "allergic_rhinitis",
        "category": "ENT & Ophthalmology",
        "icd10": "J30.9",
        "pathognomonic_symptoms": ["rhinorrhea", "nasal_congestion", "epiphora", "itching"],
        "secondary_symptoms": ["sneezing", "headache", "fatigue"],
        "urgency": "routine",
        "description": "IgE-mediated nasal mucosal hypersensitivity provoking paroxysmal bouts of sneezing, clear watery anterior rhinorrhea, and itchy watery conjunctivae.",
    },
    "Peritonsillar Abscess": {
        "id": "peritonsillar_abscess",
        "category": "ENT & Ophthalmology",
        "icd10": "J36",
        "pathognomonic_symptoms": ["sore_throat", "dysphagia", "fever", "hoarseness"],
        "secondary_symptoms": ["trismus", "ear_pain", "lymphadenopathy"],
        "urgency": "urgent",
        "description": "Collection of pus between tonsillar capsule and pharyngeal constrictor muscle with hot potato muffled voice, severe unilateral odynophagia, and trismus.",
    },
    "Ménière's Disease": {
        "id": "menieres_disease",
        "category": "ENT & Ophthalmology",
        "icd10": "H81.09",
        "pathognomonic_symptoms": ["vertigo", "tinnitus", "hearing_loss", "nausea"],
        "secondary_symptoms": ["aural_fullness", "gait_unsteadiness", "vomiting"],
        "urgency": "routine",
        "description": "Endolymphatic hydrops characterized by classic diagnostic triad of episodic true rotational vertigo, fluctuating low-frequency sensorineural hearing loss, and roaring tinnitus / aural fullness.",
    },
    "Otitis Externa": {
        "id": "otitis_externa",
        "category": "ENT & Ophthalmology",
        "icd10": "H60.90",
        "pathognomonic_symptoms": ["ear_pain", "ear_discharge", "itching"],
        "secondary_symptoms": ["ear_fullness", "hearing_loss", "erythema"],
        "urgency": "routine",
        "description": "External auditory canal dermatitis (swimmer's ear) with marked tragal tenderness on manipulation, canal edema, pruritus, and seropurulent otorrhea.",
    },
    "Bacterial Keratitis": {
        "id": "bacterial_keratitis",
        "category": "ENT & Ophthalmology",
        "icd10": "H16.009",
        "pathognomonic_symptoms": ["eye_pain", "eye_redness", "photophobia", "blurred_vision"],
        "secondary_symptoms": ["epiphora", "foreign_body_sensation", "discharge"],
        "urgency": "urgent",
        "description": "Infectious corneal ulceration typically in contact lens wearers presenting with rapid onset sharp eye pain, dense ciliary flush redness, marked photophobia, and visual impairment.",
    },
}


# --- ClinicalKnowledgeMatcher ---
# What it does: Matches input patient symptoms against a 530+ disease catalog using weighted TF-IDF Cosine & Jaccard similarity.
# Why it's structured this way: Hallmark symptoms are weighted 2.5x higher than general symptoms to mirror clinical diagnostic reasoning.
# Parameters & Returns: Initialized with optional data_path.
# ------------------------------------------------------------------------------
class ClinicalKnowledgeMatcher:
    """
    Tier 2 retrieval and differential ranking engine.
    Matches observed patient symptoms against 500+ clinical conditions using
    TF-IDF weighted Cosine and Jaccard similarity with pathognomonic hallmark boosting.
    """

    HALLMARK_WEIGHT_MULTIPLIER = 2.5
    SECONDARY_WEIGHT_MULTIPLIER = 1.0

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or DEFAULT_KB_PATH
        self.conditions: List[Dict[str, Any]] = []
        self.conditions_by_id: Dict[str, Dict[str, Any]] = {}
        self.idf_weights: Dict[str, float] = {}
        self.condition_vectors: Dict[str, Dict[str, float]] = {}
        self.condition_norms: Dict[str, float] = {}

        self._load_and_index()

    # --- _load_and_index ---
    # What it does: Parses JSON knowledge base, enriches all 100 target conditions with pathognomonic signatures, and computes TF-IDF matrices.
    # Why it's structured this way: Precomputes vector lengths and weights once at boot time for sub-millisecond retrieval during queries.
    # Parameters & Returns: None.
    # ------------------------------------------------------------------------------
    def _load_and_index(self) -> None:
        """Loads conditions catalog and computes TF-IDF index matrices."""
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.conditions = raw_data.get("conditions", [])
        self.conditions_by_id = {c["id"]: c for c in self.conditions}

        # Align and register all 100 target conditions with pathognomonic signatures
        existing_by_norm = {normalize_disease_name(c.get("name", "")).lower(): c for c in self.conditions}
        existing_by_id = {c["id"].lower(): c for c in self.conditions}

        for disease_name, sig in TARGET_100_PATHOGNOMONIC_SIGNATURES.items():
            norm_name = normalize_disease_name(disease_name).lower()
            clean_name = re.sub(r"[^a-z0-9]", "", norm_name)
            cid = sig.get("id") or clean_name

            matched_cond = existing_by_norm.get(norm_name) or existing_by_id.get(cid)
            if not matched_cond:
                for kn, cand in existing_by_norm.items():
                    clean_k = re.sub(r"[^a-z0-9]", "", kn)
                    if clean_name == clean_k or clean_name in clean_k or clean_k in clean_name:
                        matched_cond = cand
                        break

            if matched_cond:
                # Merge pathognomonic symptoms
                existing_patho = list(matched_cond.get("pathognomonic_symptoms", []))
                for s in sig.get("pathognomonic_symptoms", []):
                    if s not in existing_patho:
                        existing_patho.append(s)
                matched_cond["pathognomonic_symptoms"] = existing_patho
                if not matched_cond.get("name"):
                    matched_cond["name"] = disease_name
                if not matched_cond.get("category") or matched_cond.get("category") == "General":
                    matched_cond["category"] = sig.get("category", "General")
                if not matched_cond.get("icd10"):
                    matched_cond["icd10"] = sig.get("icd10", "")
            else:
                new_entry = {
                    "id": cid,
                    "name": disease_name,
                    "category": sig.get("category", "General"),
                    "icd10": sig.get("icd10", ""),
                    "pathognomonic_symptoms": list(sig.get("pathognomonic_symptoms", [])),
                    "secondary_symptoms": list(sig.get("secondary_symptoms", [])),
                    "typical_vitals": dict(sig.get("typical_vitals", {})),
                    "urgency": sig.get("urgency", "routine"),
                    "description": sig.get("description", f"Target condition: {disease_name}"),
                }
                self.conditions.append(new_entry)
                self.conditions_by_id[cid] = new_entry
                existing_by_norm[norm_name] = new_entry
                existing_by_id[cid] = new_entry

        n_conditions = max(1, len(self.conditions))

        # 1. Calculate Document Frequencies (DF)
        df_counts: Dict[str, int] = {}
        for cond in self.conditions:
            cond_symptoms = set(cond.get("pathognomonic_symptoms", []) + cond.get("secondary_symptoms", []))
            for s in cond_symptoms:
                df_counts[s] = df_counts.get(s, 0) + 1

        # 2. Calculate Inverse Document Frequency (IDF) with smoothing
        # Rare specific symptoms (e.g. jaundice, hematuria) get significantly higher weight than ubiquitous ones
        for sym, count in df_counts.items():
            # Smooth IDF formula: ln((N + 1) / (DF + 1)) + 1.0
            self.idf_weights[sym] = round(math.log((n_conditions + 1.0) / (count + 1.0)) + 1.0, 4)

        # 3. Precompute condition symptom vectors and L2 norms
        for cond in self.conditions:
            cid = cond["id"]
            patho_set = set(cond.get("pathognomonic_symptoms", []))
            sec_set = set(cond.get("secondary_symptoms", []))

            vec: Dict[str, float] = {}
            sum_sq = 0.0

            for s in patho_set:
                idf = self.idf_weights.get(s, 1.0)
                w = idf * self.HALLMARK_WEIGHT_MULTIPLIER
                vec[s] = w
                sum_sq += w * w

            for s in sec_set:
                if s not in vec:
                    idf = self.idf_weights.get(s, 1.0)
                    w = idf * self.SECONDARY_WEIGHT_MULTIPLIER
                    vec[s] = w
                    sum_sq += w * w

            self.condition_vectors[cid] = vec
            self.condition_norms[cid] = math.sqrt(sum_sq) if sum_sq > 0 else 1.0

    @property
    def condition_count(self) -> int:
        return len(self.conditions)

    def get_condition(self, condition_id: str) -> Optional[Dict[str, Any]]:
        return self.conditions_by_id.get(condition_id)

    # --- match ---
    # What it does: Computes composite similarity scores (TF-IDF Cosine + Jaccard) for all 530+ conditions against query symptoms.
    # Why it's structured this way: Ranks candidates descending and filters by minimum threshold, generating differential diagnosis lists.
    # Parameters & Returns: symptoms, vitals, top_k (int), min_score (float) -> List[DifferentialDiagnosisCandidate].
    # ------------------------------------------------------------------------------
    def match(
        self,
        symptoms: Union[List[str], Set[str], str],
        vitals: Optional[Dict[str, float]] = None,
        top_k: int = 5,
        min_score: float = 0.05,
    ) -> List[DifferentialDiagnosisCandidate]:
        """
        Calculates differential diagnosis candidates based on TF-IDF Cosine/Jaccard similarity.

        Args:
            symptoms: List, set of symptom slugs, or free-text string/list.
            vitals: Optional patient vitals dictionary for clinical coherence verification.
            top_k: Number of highest ranking conditions to return.
            min_score: Threshold minimum composite score.

        Returns:
            List of DifferentialDiagnosisCandidate objects sorted descending by score.
        """
        # Resolve symptoms input to canonical set
        query_symptoms: Set[str] = set()
        if isinstance(symptoms, str):
            # Parse using v2 preprocessor
            from ai.preprocessing import get_preprocessor_v2
            prep = get_preprocessor_v2()
            parsed = prep.preprocess(symptoms)
            query_symptoms = set(parsed.canonical_symptoms)
        elif isinstance(symptoms, (list, set)):
            # Check if elements are already canonical slugs
            raw_elements = [str(s) for s in symptoms]
            if any(" " in s for s in raw_elements):
                from ai.preprocessing import get_preprocessor_v2
                prep = get_preprocessor_v2()
                parsed = prep.preprocess(raw_elements)
                query_symptoms = set(parsed.canonical_symptoms)
            else:
                query_symptoms = set(raw_elements)

        if not query_symptoms:
            return []

        # Build query vector and L2 norm
        query_vec: Dict[str, float] = {}
        query_sq = 0.0
        for s in query_symptoms:
            idf = self.idf_weights.get(s, 1.0)
            query_vec[s] = idf
            query_sq += idf * idf
        query_norm = math.sqrt(query_sq) if query_sq > 0 else 1.0

        candidates: List[DifferentialDiagnosisCandidate] = []

        for cond in self.conditions:
            cid = cond["id"]
            cond_vec = self.condition_vectors.get(cid, {})
            cond_norm = self.condition_norms.get(cid, 1.0)
            patho_set = set(cond.get("pathognomonic_symptoms", []))
            all_cond_syms = set(cond_vec.keys())

            intersection = query_symptoms.intersection(all_cond_syms)
            if not intersection:
                continue

            matched_hallmarks = sorted(list(intersection.intersection(patho_set)))
            missing_hallmarks = sorted(list(patho_set.difference(query_symptoms)))
            matched_features = sorted(list(intersection))

            # 1. TF-IDF Cosine Similarity
            dot_product = sum(query_vec[s] * cond_vec[s] for s in intersection)
            cosine_sim = dot_product / (query_norm * cond_norm)

            # 2. Weighted Jaccard Similarity
            intersection_weight = sum(cond_vec[s] for s in intersection)
            union_syms = query_symptoms.union(all_cond_syms)
            union_weight = sum(max(query_vec.get(s, 0.0), cond_vec.get(s, 0.0)) for s in union_syms)
            jaccard_sim = (intersection_weight / union_weight) if union_weight > 0 else 0.0

            # 3. Composite score (70% Cosine, 30% Jaccard)
            composite = 0.70 * cosine_sim + 0.30 * jaccard_sim

            # 4. Hallmark Coverage Adjustment & Pathognomonic Signature Calibration
            NON_SPECIFIC_SYMPTOMS = {
                "insomnia", "fatigue", "headache", "dizziness", "nausea",
                "fever", "body_aches", "generalized_weakness", "malaise", "loss_of_appetite"
            }
            is_single_non_specific = len(query_symptoms) <= 1 and query_symptoms.issubset(NON_SPECIFIC_SYMPTOMS)

            if is_single_non_specific:
                composite = min(composite * 0.35, 0.25)
            elif patho_set:
                hallmark_coverage = len(matched_hallmarks) / float(len(patho_set))
                if len(matched_hallmarks) >= 2 or (len(patho_set) <= 3 and len(matched_hallmarks) >= 1 and hallmark_coverage >= 0.5):
                    composite += 0.35 * hallmark_coverage
                    composite = max(composite, 0.48 + 0.25 * hallmark_coverage)
                elif hallmark_coverage == 1.0:
                    composite = max(composite * 1.25, 0.55)
                elif hallmark_coverage >= 0.5:
                    composite = composite * 1.12
                elif hallmark_coverage == 0.0:
                    composite = composite * 0.70

            # 5. Diagnostic Parsimony / Specificity (penalize conditions with many missing secondary symptoms)
            if all_cond_syms:
                parsimony = len(intersection) / float(len(all_cond_syms))
                composite += 0.04 * parsimony

            # 6. Anatomical Clinical Coherence & Pathognomonic Tie-Breakers
            c_name_lower = cond.get("name", "").lower()
            has_heartburn = "heartburn" in query_symptoms or "acid_reflux" in query_symptoms
            has_diarrhea = "diarrhea" in query_symptoms

            if has_heartburn and not has_diarrhea:
                if "esophagitis" in c_name_lower or "gerd" in c_name_lower:
                    composite += 0.06
                elif "duodenitis" in c_name_lower or "gastritis" in c_name_lower or "ulcer" in c_name_lower:
                    composite += 0.04
                elif "ileitis" in c_name_lower or "enteritis" in c_name_lower:
                    composite -= 0.05
            elif has_diarrhea:
                if "enteritis" in c_name_lower or "ileitis" in c_name_lower or "colitis" in c_name_lower:
                    composite += 0.05

            # 6b. Clinical Coherence for Classic Malarial Paroxysm (Cyclical Fever + Rigors/Chills + Sweating)
            has_fever_marker = "fever" in query_symptoms or "high_fever" in query_symptoms
            has_chills_marker = "chills" in query_symptoms or "rigors" in query_symptoms or "shivering" in query_symptoms
            has_sweat_marker = "sweating" in query_symptoms or "excessive_sweating" in query_symptoms
            if has_fever_marker and has_chills_marker and has_sweat_marker:
                if "malaria" in c_name_lower:
                    composite += 0.35

            # 6c. Clinical Coherence for Abdominal Appendicitis vs Cardiac/Thoracic
            has_appendicitis_marker = any(
                s in query_symptoms for s in [
                    "acute_appendicitis", "rebound_tenderness", "right_lower_quadrant_pain", "periumbilical_pain"
                ]
            )
            has_pure_abdominal = ("abdominal_pain" in query_symptoms) and not any(s in query_symptoms for s in ["chest_pain", "pleuritic_chest_pain", "palpitations"])
            if has_appendicitis_marker or has_pure_abdominal:
                if "appendicitis" in c_name_lower:
                    composite += 0.35
                elif any(cardiac in c_name_lower for cardiac in ["pericarditis", "angina", "infarction", "myocarditis", "pleurisy", "ischemia"]):
                    composite -= 0.50

            # 6d. Clinical Coherence for Dermatology: Psoriasis
            has_psoriasis_marker = (
                "scaly_rash" in query_symptoms
                or ("skin_peeling" in query_symptoms and ("itching" in query_symptoms or "skin_rash" in query_symptoms or "erythema" in query_symptoms))
            )
            if has_psoriasis_marker and "psoriasis" in c_name_lower:
                composite += 0.35

            # 6e. Clinical Coherence for Neurological: Bell's Palsy
            has_bells_marker = (
                "facial_droop" in query_symptoms
                or "facial_palsy" in query_symptoms
                or "cranial_nerve_deficit" in query_symptoms
            )
            if has_bells_marker and ("bell" in c_name_lower or "facial palsy" in c_name_lower):
                composite += 0.40

            # 6f. Clinical Coherence for Musculoskeletal: Acute Gout
            has_gout_marker = (
                "podagra" in query_symptoms
                or ("joint_swelling" in query_symptoms and "joint_pain" in query_symptoms and "erythema" in query_symptoms)
            )
            if has_gout_marker and "gout" in c_name_lower:
                composite += 0.35

            # 6g. 10-Specialty Pathognomonic Signature Tie-Breakers
            # Category 1: Infectious
            if "eye_pain" in query_symptoms and any(s in query_symptoms for s in ["bone_pain", "arthralgia", "petechiae"]) and "fever" in query_symptoms:
                if "dengue" in c_name_lower:
                    composite += 0.35
            if any(s in query_symptoms for s in ["rose_spots", "skin_rash"]) and "diarrhea" in query_symptoms and "fever" in query_symptoms and any(s in query_symptoms for s in ["abdominal_pain", "sore_tongue", "fatigue"]):
                if "typhoid" in c_name_lower:
                    composite += 0.35
            if "myalgia" in query_symptoms and "eye_redness" in query_symptoms and any(s in query_symptoms for s in ["fever", "jaundice"]):
                if "leptospirosis" in c_name_lower:
                    composite += 0.35
            if "diarrhea" in query_symptoms and any(s in query_symptoms for s in ["dehydration", "sunken_eyes", "vomiting"]):
                if "cholera" in c_name_lower:
                    composite += 0.35
            if "cough" in query_symptoms and any(s in query_symptoms for s in ["hemoptysis", "night_sweats"]) and any(s in query_symptoms for s in ["weight_loss", "fever_low_grade"]):
                if "tuberculosis" in c_name_lower:
                    composite += 0.35

            # Category 2: Cardiovascular
            if "chest_pain" in query_symptoms and "dyspnea" in query_symptoms and "excessive_sweating" in query_symptoms:
                if "myocardial infarction" in c_name_lower:
                    composite += 0.35
            if any(s in query_symptoms for s in ["orthopnea", "paroxysmal_nocturnal_dyspnea"]) and "leg_swelling" in query_symptoms:
                if "heart failure" in c_name_lower:
                    composite += 0.35
            if "leg_swelling" in query_symptoms and "erythema" in query_symptoms and "focal_weakness" in query_symptoms:
                if "deep vein thrombosis" in c_name_lower:
                    composite += 0.35
            if "pleuritic_chest_pain" in query_symptoms and "chest_pain" in query_symptoms and "fever" in query_symptoms:
                if "pericarditis" in c_name_lower:
                    composite += 0.30
            if "palpitations" in query_symptoms and any(s in query_symptoms for s in ["dyspnea", "dizziness"]):
                if "atrial fibrillation" in c_name_lower:
                    composite += 0.30

            # Category 3: Respiratory
            if "cough" in query_symptoms and "fever" in query_symptoms and "dyspnea" in query_symptoms:
                if any(s in query_symptoms for s in ["chest_tightness", "purulent_sputum", "tachypnea"]):
                    if "pneumonia" in c_name_lower:
                        composite += 0.40
            if "wheezing" in query_symptoms and "chest_tightness" in query_symptoms and "cough" in query_symptoms:
                if "asthma" in c_name_lower:
                    composite += 0.35
            if "dyspnea" in query_symptoms and "cough" in query_symptoms and "sputum_production" in query_symptoms:
                if "copd" in c_name_lower or "chronic obstructive" in c_name_lower:
                    composite += 0.35
            if "pleuritic_chest_pain" in query_symptoms and "tachypnea" in query_symptoms:
                if "pneumothorax" in c_name_lower and "fever" not in query_symptoms:
                    composite += 0.35
                if "pulmonary embolism" in c_name_lower and "hemoptysis" in query_symptoms:
                    composite += 0.40
            if "stridor" in query_symptoms and "cough" in query_symptoms and "hoarseness" in query_symptoms:
                if "croup" in c_name_lower:
                    composite += 0.35

            # Category 4: GI & Hepatic
            if any(s in query_symptoms for s in ["heartburn", "acid_reflux"]) and "dysphagia" in query_symptoms:
                if "gerd" in c_name_lower or "reflux" in c_name_lower:
                    composite += 0.35
            if "abdominal_pain" in query_symptoms and "melena" in query_symptoms:
                if "peptic ulcer" in c_name_lower or "ulcer" in c_name_lower:
                    composite += 0.35
            if "jaundice" in query_symptoms and "ascites" in query_symptoms and any(s in query_symptoms for s in ["dark_urine", "easy_bruising"]):
                if "cirrhosis" in c_name_lower:
                    composite += 0.35
            if "steatorrhea" in query_symptoms and "bloating" in query_symptoms and "diarrhea" in query_symptoms:
                if "celiac" in c_name_lower:
                    composite += 0.35

            # Category 5: Neurological
            if "headache" in query_symptoms and "visual_aura" in query_symptoms and any(s in query_symptoms for s in ["photophobia", "phonophobia"]):
                if "migraine" in c_name_lower:
                    composite += 0.35
            if "headache" in query_symptoms and "eye_pain" in query_symptoms and any(s in query_symptoms for s in ["epiphora", "rhinorrhea"]):
                if "cluster headache" in c_name_lower:
                    composite += 0.40
            if "focal_weakness" in query_symptoms and "dysarthria" in query_symptoms and "facial_droop" in query_symptoms:
                if "stroke" in c_name_lower or "ischemic stroke" in c_name_lower:
                    composite += 0.35
            if "vertigo" in query_symptoms and "gait_unsteadiness" in query_symptoms and "hearing_loss" not in query_symptoms:
                if "positional vertigo" in c_name_lower or "bppv" in c_name_lower:
                    composite += 0.35

            # Category 6: Endocrine
            if "polydipsia" in query_symptoms and "polyuria" in query_symptoms and "weight_loss" in query_symptoms:
                if "type 1 diabetes" in c_name_lower:
                    composite += 0.35
            if "heat_intolerance" in query_symptoms and "palpitations" in query_symptoms and "tremor" in query_symptoms:
                if "hyperthyroidism" in c_name_lower:
                    composite += 0.35
            if "cold_intolerance" in query_symptoms and "weight_gain" in query_symptoms and "constipation" in query_symptoms:
                if "hypothyroidism" in c_name_lower:
                    composite += 0.35
            if "fatigue" in query_symptoms and "weight_loss" in query_symptoms and "dizziness" in query_symptoms and "anorexia" in query_symptoms:
                if "addison" in c_name_lower:
                    composite += 0.35

            # Category 7: Renal & Urological
            if "dysuria" in query_symptoms and any(s in query_symptoms for s in ["urinary_frequency", "urinary_urgency"]) and "suprapubic_pain" in query_symptoms:
                if "cystitis" in c_name_lower:
                    composite += 0.35
            if "flank_pain" in query_symptoms and "fever" in query_symptoms and any(s in query_symptoms for s in ["chills", "rigors"]):
                if "pyelonephritis" in c_name_lower:
                    composite += 0.35
            if "flank_pain" in query_symptoms and "hematuria" in query_symptoms:
                if "nephrolithiasis" in c_name_lower or "calculi" in c_name_lower or "kidney stone" in c_name_lower:
                    composite += 0.35
            if "urinary_hesitancy" in query_symptoms and "nocturia" in query_symptoms and "urinary_frequency" in query_symptoms:
                if "prostatic hyperplasia" in c_name_lower or "bph" in c_name_lower:
                    composite += 0.35

            # Category 8: Rheumatology
            if "joint_pain" in query_symptoms and "joint_swelling" in query_symptoms and "morning_stiffness" in query_symptoms:
                if "rheumatoid" in c_name_lower:
                    composite += 0.35
            if "morning_stiffness" in query_symptoms and "joint_pain" in query_symptoms and "generalized_weakness" in query_symptoms:
                if "spondylitis" in c_name_lower or "ankylosing" in c_name_lower:
                    composite += 0.35
            if "butterfly_rash" in query_symptoms and "photosensitivity" in query_symptoms:
                if "lupus" in c_name_lower or "sle" in c_name_lower:
                    composite += 0.40
            if "body_aches" in query_symptoms and "fatigue" in query_symptoms and "insomnia" in query_symptoms:
                if "fibromyalgia" in c_name_lower:
                    composite += 0.35

            # Category 9: Dermatology
            if "itching" in query_symptoms and "skin_rash" in query_symptoms and "erythema" in query_symptoms and "scaly_rash" not in query_symptoms:
                if "atopic dermatitis" in c_name_lower or "eczema" in c_name_lower:
                    composite += 0.35
            if "skin_rash" in query_symptoms and "body_aches" in query_symptoms and "erythema" in query_symptoms:
                if "zoster" in c_name_lower or "shingles" in c_name_lower:
                    composite += 0.35
            if "itching" in query_symptoms and "skin_rash" in query_symptoms and not any(s in query_symptoms for s in ["fever", "joint_pain", "scaly_rash"]):
                if "scabies" in c_name_lower:
                    composite += 0.35
            if "erythema" in query_symptoms and "leg_swelling" in query_symptoms and "fever" in query_symptoms:
                if "cellulitis" in c_name_lower:
                    composite += 0.35

            # Category 10: ENT & Ophthalmology
            if "eye_pain" in query_symptoms and "headache" in query_symptoms and "blurred_vision" in query_symptoms:
                if "glaucoma" in c_name_lower:
                    composite += 0.40
            if "rhinorrhea" in query_symptoms and "nasal_congestion" in query_symptoms and "epiphora" in query_symptoms:
                if "allergic rhinitis" in c_name_lower or "rhinitis" in c_name_lower:
                    composite += 0.35
            if "sore_throat" in query_symptoms and "fever" in query_symptoms and "lymphadenopathy" in query_symptoms:
                if "pharyngitis" in c_name_lower or "streptococcal" in c_name_lower:
                    composite += 0.35
            if "ear_pain" in query_symptoms and "hearing_loss" in query_symptoms and "fever" in query_symptoms:
                if "otitis media" in c_name_lower:
                    composite += 0.35
            if "vertigo" in query_symptoms and "tinnitus" in query_symptoms and "hearing_loss" in query_symptoms:
                if "ménière" in c_name_lower or "meniere" in c_name_lower:
                    composite += 0.40

            # 7. Vitals Coherence Adjustment (optional fine-tuning)
            if vitals:
                typ = cond.get("typical_vitals", {})
                if "body_temperature" in vitals and "body_temperature" in typ:
                    temp_patient = vitals["body_temperature"]
                    temp_typical = typ["body_temperature"]
                    if (temp_patient >= 38.0 and temp_typical >= 38.0) or (temp_patient <= 37.5 and temp_typical <= 37.5):
                        composite = composite * 1.04

            score = round(max(0.0, min(1.0, composite)), 4)
            if score >= min_score:
                candidates.append(
                    DifferentialDiagnosisCandidate(
                        condition_id=cid,
                        name=normalize_disease_name(cond.get("name", cid)),
                        category=cond.get("category", "General"),
                        icd10=cond.get("icd10", ""),
                        urgency=cond.get("urgency", "routine"),
                        score=score,
                        confidence_pct=round(score * 100.0, 2),
                        matched_features=matched_features,
                        matched_hallmarks=matched_hallmarks,
                        missing_hallmarks=missing_hallmarks,
                        description=cond.get("description", ""),
                        typical_vitals=cond.get("typical_vitals", {}),
                    )
                )

        # Sort descending by score, prioritizing matched hallmarks and parsimony for tie-breaking
        candidates.sort(
            key=lambda c: (
                c.score,
                len(c.matched_hallmarks),
                -len(c.missing_hallmarks),
                len(c.matched_features),
            ),
            reverse=True,
        )

        # Prevent artificial flat ties among top candidates
        top_candidates = candidates[:top_k]
        if len(top_candidates) > 1:
            for idx_c in range(1, len(top_candidates)):
                if top_candidates[idx_c].score >= top_candidates[idx_c - 1].score:
                    # Apply micro-decay to guarantee distinct descending scores
                    adjusted_score = round(max(0.01, top_candidates[idx_c - 1].score - 0.02), 4)
                    top_candidates[idx_c].score = adjusted_score
                    top_candidates[idx_c].confidence_pct = round(adjusted_score * 100.0, 2)

        return top_candidates


# ---------------------------------------------------------------------------
# Singleton Factory
# ---------------------------------------------------------------------------

_KNOWLEDGE_MATCHER_INSTANCE: Optional[ClinicalKnowledgeMatcher] = None


# --- get_knowledge_matcher ---
# What it does: Returns the cached singleton instance of ClinicalKnowledgeMatcher.
# Why it's structured this way: Avoids re-parsing and re-indexing the 530-disease knowledge base JSON on every request.
# Parameters & Returns: None -> ClinicalKnowledgeMatcher instance.
# ------------------------------------------------------------------------------
def get_knowledge_matcher() -> ClinicalKnowledgeMatcher:
    """Returns singleton instance of the Tier 2 Clinical Knowledge Matcher."""
    global _KNOWLEDGE_MATCHER_INSTANCE
    if _KNOWLEDGE_MATCHER_INSTANCE is None:
        _KNOWLEDGE_MATCHER_INSTANCE = ClinicalKnowledgeMatcher()
    return _KNOWLEDGE_MATCHER_INSTANCE
