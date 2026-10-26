# ==============================================================================
# FILE: backend/ml/train.py
# PURPOSE: Machine learning training pipeline for Tier 1 100-disease multi-class XGBoost model.
# VIVA EXPLANATION: This script trains the primary diagnostic classifier. It compiles clinical profiles across 100 conditions and 163 features, handles sparsity-aware split routing for missing vitals, computes multi-class log loss and F1-metrics, and serializes the model weights, label encoders, and schema artifacts.
# ==============================================================================

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

# Ensure backend root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from ai.preprocessing import get_preprocessor, get_preprocessor_v2
except ImportError:
    from backend.ai.preprocessing import get_preprocessor, get_preprocessor_v2


# ---------------------------------------------------------------------------
# Target Disease Classes (100 Classes for Tier 1 v2.0.0)
# ---------------------------------------------------------------------------

DISEASE_CLASSES_100: List[str] = [
    # 1. Infectious & Tropical (10)
    "Malaria",
    "Dengue Fever",
    "Typhoid Fever",
    "Pulmonary Tuberculosis",
    "Leptospirosis",
    "Chickenpox",
    "Cholera",
    "Influenza",
    "Community-Acquired Pneumonia",
    "Acute Viral Hepatitis",

    # 2. Cardiovascular (10)
    "Acute Myocardial Infarction",
    "Congestive Heart Failure",
    "Essential Hypertension",
    "Infective Endocarditis",
    "Atrial Fibrillation",
    "Deep Vein Thrombosis",
    "Angina Pectoris",
    "Acute Pericarditis",
    "Peripheral Artery Disease",
    "Aortic Stenosis",

    # 3. Respiratory (10)
    "Bronchial Asthma",
    "Chronic Obstructive Pulmonary Disease",
    "Acute Bronchitis",
    "Pulmonary Embolism",
    "Bronchiectasis",
    "Pleurisy",
    "Spontaneous Pneumothorax",
    "Idiopathic Pulmonary Fibrosis",
    "Obstructive Sleep Apnea",
    "Croup",

    # 4. Gastrointestinal & Hepatic (10)
    "Gastroesophageal Reflux Disease",
    "Peptic Ulcer Disease",
    "Acute Pancreatitis",
    "Acute Cholecystitis",
    "Acute Appendicitis",
    "Liver Cirrhosis",
    "Ulcerative Colitis",
    "Crohn's Disease",
    "Acute Diverticulitis",
    "Celiac Disease",

    # 5. Neurological (10)
    "Migraine",
    "Cluster Headache",
    "Tension Headache",
    "Ischemic Stroke",
    "Transient Ischemic Attack",
    "Benign Paroxysmal Positional Vertigo",
    "Parkinson's Disease",
    "Bell's Palsy",
    "Acute Bacterial Meningitis",
    "Sciatica",

    # 6. Endocrine & Metabolic (10)
    "Type 1 Diabetes",
    "Type 2 Diabetes",
    "Hypothyroidism",
    "Hyperthyroidism",
    "Cushing's Syndrome",
    "Addison's Disease",
    "Acute Gout",
    "Hypoglycemia",
    "Diabetic Ketoacidosis",
    "Primary Hyperparathyroidism",

    # 7. Renal & Urological (10)
    "Acute Cystitis",
    "Acute Pyelonephritis",
    "Nephrolithiasis",
    "Acute Kidney Injury",
    "Chronic Kidney Disease",
    "Benign Prostatic Hyperplasia",
    "Nephrotic Syndrome",
    "Acute Glomerulonephritis",
    "Urethritis",
    "Interstitial Cystitis",

    # 8. Rheumatology & Musculoskeletal (10)
    "Osteoarthritis",
    "Rheumatoid Arthritis",
    "Systemic Lupus Erythematosus",
    "Ankylosing Spondylitis",
    "Fibromyalgia",
    "Polymyalgia Rheumatica",
    "Systemic Sclerosis",
    "Sjögren's Syndrome",
    "Psoriatic Arthritis",
    "Dermatomyositis",

    # 9. Dermatology (10)
    "Plaque Psoriasis",
    "Atopic Dermatitis",
    "Herpes Zoster",
    "Cellulitis",
    "Scabies",
    "Acute Urticaria",
    "Contact Dermatitis",
    "Impetigo",
    "Alopecia Areata",
    "Erythema Multiforme",

    # 10. ENT & Ophthalmology (10)
    "Acute Otitis Media",
    "Acute Sinusitis",
    "Streptococcal Pharyngitis",
    "Acute Angle-Closure Glaucoma",
    "Infectious Conjunctivitis",
    "Allergic Rhinitis",
    "Peritonsillar Abscess",
    "Ménière's Disease",
    "Otitis Externa",
    "Bacterial Keratitis",
]

# Legacy 8 classes for v1.0.0 backward compatibility
DEFAULT_DISEASE_CLASSES: List[str] = [
    "Influenza",
    "Common Cold",
    "Pneumonia",
    "Type 2 Diabetes",
    "Hypertension",
    "Migraine",
    "Acute Gastroenteritis",
    "Bronchial Asthma",
]

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_DATA_PATH_V1 = os.path.join(DEFAULT_DATA_DIR, "dev_dataset_v1.csv")
DEFAULT_DATA_PATH_V2 = os.path.join(DEFAULT_DATA_DIR, "dev_dataset_v2.csv")
DEFAULT_DATA_PATH = DEFAULT_DATA_PATH_V1

DEFAULT_ARTIFACT_DIR_V1 = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "ai", "artifacts", "v1.0.0"
)
DEFAULT_ARTIFACT_DIR_V2 = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "ai", "artifacts", "v2.0.0"
)
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR_V1

SCHEMA_SOURCE_PATH_V1 = os.path.join(DEFAULT_ARTIFACT_DIR_V1, "schema.json")
SCHEMA_SOURCE_PATH_V2 = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "ai", "schema.json"
)
SCHEMA_SOURCE_PATH = SCHEMA_SOURCE_PATH_V2


# ---------------------------------------------------------------------------
# Clinical Pathophysiology Profiles for 100 Disease Classes
# ---------------------------------------------------------------------------

CLINICAL_PROFILES_100: Dict[str, Dict[str, Any]] = {
    # 1. Infectious & Tropical
    "Malaria": {
        "hallmarks": {"fever": 0.96, "chills": 0.92, "rigors": 0.94, "jaundice": 0.55, "headache": 0.70},
        "secondary": {"sweating": 0.85, "fatigue": 0.88, "nausea": 0.60, "myalgia": 0.75, "pallor": 0.50},
        "vitals": {"body_temperature": (39.8, 0.5), "heart_rate": (106.0, 10.0)},
    },
    "Dengue Fever": {
        "hallmarks": {"fever": 0.96, "joint_pain": 0.92, "skin_rash": 0.88, "petechiae": 0.82, "bone_pain": 0.80},
        "secondary": {"headache": 0.85, "eye_pain": 0.75, "fatigue": 0.90, "nausea": 0.65, "vomiting": 0.55},
        "vitals": {"body_temperature": (39.5, 0.6), "heart_rate": (102.0, 10.0), "systolic_bp": (105.0, 12.0)},
    },
    "Typhoid Fever": {
        "hallmarks": {"fever": 0.95, "abdominal_pain": 0.85, "bloating": 0.75, "headache": 0.80},
        "secondary": {"chills": 0.70, "constipation": 0.60, "diarrhea": 0.35, "malaise": 0.85, "anorexia": 0.80},
        "vitals": {"body_temperature": (39.4, 0.5), "heart_rate": (74.0, 8.0)},  # Sphygmothermic dissociation
    },
    "Pulmonary Tuberculosis": {
        "hallmarks": {"cough": 0.96, "hemoptysis": 0.85, "night_sweats": 0.92, "weight_loss": 0.90},
        "secondary": {"fever_low_grade": 0.85, "purulent_sputum": 0.80, "pleuritic_chest_pain": 0.65, "fatigue": 0.90, "anorexia": 0.80},
        "vitals": {"body_temperature": (37.8, 0.4), "bmi": (18.5, 2.0), "oxygen_saturation": (94.0, 2.5)},
    },
    "Leptospirosis": {
        "hallmarks": {"fever": 0.95, "jaundice": 0.86, "hematuria": 0.78, "myalgia": 0.92, "eye_redness": 0.80},
        "secondary": {"chills": 0.85, "rigors": 0.78, "headache": 0.80, "oliguria": 0.60, "vomiting": 0.55},
        "vitals": {"body_temperature": (39.2, 0.6), "heart_rate": (108.0, 12.0)},
    },
    "Chickenpox": {
        "hallmarks": {"skin_rash": 0.98, "bullae": 0.94, "itching": 0.95, "fever": 0.85},
        "secondary": {"fatigue": 0.80, "headache": 0.65, "anorexia": 0.60, "malaise": 0.80},
        "vitals": {"body_temperature": (38.5, 0.5)},
    },
    "Cholera": {
        "hallmarks": {"diarrhea": 0.99, "vomiting": 0.90, "muscle_cramps": 0.85, "generalized_weakness": 0.90},
        "secondary": {"oliguria": 0.80, "fatigue": 0.92, "presyncope": 0.70},
        "vitals": {"systolic_bp": (84.0, 8.0), "diastolic_bp": (52.0, 6.0), "heart_rate": (118.0, 12.0)},
    },
    "Influenza": {
        "hallmarks": {"fever": 0.96, "myalgia": 0.92, "chills": 0.90, "fatigue": 0.94, "cough": 0.80},
        "secondary": {"headache": 0.82, "sore_throat": 0.65, "rhinorrhea": 0.50, "malaise": 0.90},
        "vitals": {"body_temperature": (38.9, 0.5), "heart_rate": (94.0, 9.0)},
    },
    "Community-Acquired Pneumonia": {
        "hallmarks": {"purulent_sputum": 0.94, "fever": 0.92, "pleuritic_chest_pain": 0.86, "dyspnea": 0.90},
        "secondary": {"cough": 0.92, "chills": 0.80, "rigors": 0.70, "tachypnea": 0.85, "fatigue": 0.85},
        "vitals": {"body_temperature": (38.8, 0.5), "heart_rate": (104.0, 10.0), "oxygen_saturation": (91.5, 2.5)},
    },
    "Acute Viral Hepatitis": {
        "hallmarks": {"jaundice": 0.96, "dark_urine": 0.94, "clay_colored_stools": 0.88, "anorexia": 0.85},
        "secondary": {"fatigue": 0.90, "nausea": 0.80, "vomiting": 0.65, "abdominal_pain": 0.70, "fever_low_grade": 0.65},
        "vitals": {"body_temperature": (37.7, 0.4)},
    },

    # 2. Cardiovascular
    "Acute Myocardial Infarction": {
        "hallmarks": {"chest_pain": 0.98, "dyspnea": 0.85, "excessive_sweating": 0.80, "palpitations": 0.70},
        "secondary": {"nausea": 0.60, "vomiting": 0.45, "presyncope": 0.55, "chest_tightness": 0.85},
        "vitals": {"systolic_bp": (148.0, 18.0), "heart_rate": (102.0, 12.0), "oxygen_saturation": (93.5, 2.0)},
    },
    "Congestive Heart Failure": {
        "hallmarks": {"orthopnea": 0.94, "paroxysmal_nocturnal_dyspnea": 0.90, "leg_swelling": 0.96, "dyspnea": 0.94},
        "secondary": {"fatigue": 0.90, "cough": 0.65, "weight_gain": 0.75, "tachypnea": 0.80},
        "vitals": {"systolic_bp": (152.0, 16.0), "heart_rate": (94.0, 10.0), "oxygen_saturation": (90.5, 2.5)},
    },
    "Essential Hypertension": {
        "hallmarks": {"headache": 0.65, "dizziness": 0.55, "palpitations": 0.48},
        "secondary": {"fatigue": 0.50, "blurred_vision": 0.40, "chest_tightness": 0.35},
        "vitals": {"systolic_bp": (168.0, 12.0), "diastolic_bp": (102.0, 8.0)},
    },
    "Infective Endocarditis": {
        "hallmarks": {"fever": 0.92, "chills": 0.88, "purpura": 0.78, "night_sweats": 0.75},
        "secondary": {"dyspnea": 0.70, "fatigue": 0.85, "malaise": 0.85, "weight_loss": 0.65, "palpitations": 0.60},
        "vitals": {"body_temperature": (38.9, 0.5), "heart_rate": (98.0, 10.0)},
    },
    "Atrial Fibrillation": {
        "hallmarks": {"palpitations": 0.98, "presyncope": 0.78, "dyspnea": 0.75, "chest_tightness": 0.65},
        "secondary": {"fatigue": 0.80, "dizziness": 0.75, "syncope": 0.40},
        "vitals": {"heart_rate": (138.0, 16.0), "systolic_bp": (118.0, 14.0)},
    },
    "Deep Vein Thrombosis": {
        "hallmarks": {"leg_swelling": 0.98, "erythema": 0.84},
        "secondary": {"fever_low_grade": 0.60, "claudication": 0.65},
        "vitals": {"heart_rate": (84.0, 8.0)},
    },
    "Angina Pectoris": {
        "hallmarks": {"chest_pain": 0.96, "chest_tightness": 0.88, "dyspnea": 0.70},
        "secondary": {"palpitations": 0.55, "fatigue": 0.60, "nausea": 0.40},
        "vitals": {"systolic_bp": (140.0, 12.0), "heart_rate": (86.0, 8.0)},
    },
    "Acute Pericarditis": {
        "hallmarks": {"pleuritic_chest_pain": 0.96, "fever_low_grade": 0.78, "palpitations": 0.65},
        "secondary": {"dyspnea": 0.65, "cough": 0.50, "fatigue": 0.70},
        "vitals": {"body_temperature": (37.8, 0.4), "heart_rate": (92.0, 9.0)},
    },
    "Peripheral Artery Disease": {
        "hallmarks": {"claudication": 0.96, "pallor": 0.80, "numbness": 0.72},
        "secondary": {"tingling": 0.65, "muscle_cramps": 0.70},
        "vitals": {"systolic_bp": (145.0, 12.0)},
    },
    "Aortic Stenosis": {
        "hallmarks": {"syncope": 0.86, "dyspnea": 0.92, "chest_pain": 0.84},
        "secondary": {"fatigue": 0.80, "palpitations": 0.60, "presyncope": 0.70},
        "vitals": {"systolic_bp": (112.0, 10.0), "heart_rate": (76.0, 8.0)},
    },

    # 3. Respiratory
    "Bronchial Asthma": {
        "hallmarks": {"wheezing": 0.98, "dyspnea": 0.94, "chest_tightness": 0.90},
        "secondary": {"cough": 0.80, "tachypnea": 0.82, "sputum_production": 0.55},
        "vitals": {"oxygen_saturation": (91.0, 2.5), "heart_rate": (108.0, 10.0)},
    },
    "Chronic Obstructive Pulmonary Disease": {
        "hallmarks": {"dyspnea": 0.96, "purulent_sputum": 0.88, "cough": 0.92, "wheezing": 0.80},
        "secondary": {"cyanosis": 0.70, "tachypnea": 0.85, "fatigue": 0.85, "leg_swelling": 0.50},
        "vitals": {"oxygen_saturation": (87.5, 3.0), "heart_rate": (96.0, 9.0)},
    },
    "Acute Bronchitis": {
        "hallmarks": {"cough": 0.98, "sputum_production": 0.90, "sore_throat": 0.65},
        "secondary": {"fever_low_grade": 0.70, "malaise": 0.75, "chest_tightness": 0.55},
        "vitals": {"body_temperature": (37.5, 0.4)},
    },
    "Pulmonary Embolism": {
        "hallmarks": {"pleuritic_chest_pain": 0.94, "hemoptysis": 0.82, "dyspnea": 0.96, "tachypnea": 0.92},
        "secondary": {"syncope": 0.65, "palpitations": 0.70, "cyanosis": 0.60, "leg_swelling": 0.55},
        "vitals": {"oxygen_saturation": (88.0, 3.0), "heart_rate": (122.0, 12.0), "systolic_bp": (96.0, 12.0)},
    },
    "Bronchiectasis": {
        "hallmarks": {"purulent_sputum": 0.96, "hemoptysis": 0.84, "cough": 0.94},
        "secondary": {"wheezing": 0.75, "dyspnea": 0.80, "fever_low_grade": 0.65, "nail_clubbing": 0.60},
        "vitals": {"oxygen_saturation": (92.5, 2.5)},
    },
    "Pleurisy": {
        "hallmarks": {"pleuritic_chest_pain": 0.98, "tachypnea": 0.85, "dyspnea": 0.80},
        "secondary": {"cough": 0.65, "fever_low_grade": 0.65},
        "vitals": {"body_temperature": (37.6, 0.3)},
    },
    "Spontaneous Pneumothorax": {
        "hallmarks": {"pleuritic_chest_pain": 0.96, "dyspnea": 0.94, "tachypnea": 0.85},
        "secondary": {"cyanosis": 0.65, "presyncope": 0.50},
        "vitals": {"oxygen_saturation": (90.0, 3.0), "heart_rate": (112.0, 10.0)},
    },
    "Idiopathic Pulmonary Fibrosis": {
        "hallmarks": {"dyspnea": 0.98, "cough": 0.92, "nail_clubbing": 0.86},
        "secondary": {"fatigue": 0.85, "cyanosis": 0.65, "weight_loss": 0.60},
        "vitals": {"oxygen_saturation": (90.5, 2.5)},
    },
    "Obstructive Sleep Apnea": {
        "hallmarks": {"snoring": 0.99, "excessive_daytime_sleepiness": 0.96},
        "secondary": {"headache": 0.70, "fatigue": 0.85, "insomnia": 0.65},
        "vitals": {"bmi": (34.5, 4.0), "systolic_bp": (142.0, 12.0)},
    },
    "Croup": {
        "hallmarks": {"stridor": 0.96, "hoarseness": 0.92, "cough": 0.90},
        "secondary": {"fever_low_grade": 0.75, "dyspnea": 0.70},
        "vitals": {"body_temperature": (38.2, 0.5)},
    },

    # 4. Gastrointestinal & Hepatic
    "Gastroesophageal Reflux Disease": {
        "hallmarks": {"heartburn": 0.98, "dysphagia": 0.60, "chest_tightness": 0.65},
        "secondary": {"bloating": 0.65, "early_satiety": 0.55, "cough": 0.45},
        "vitals": {"bmi": (29.0, 3.5)},
    },
    "Peptic Ulcer Disease": {
        "hallmarks": {"abdominal_pain": 0.96, "heartburn": 0.82, "nausea": 0.75},
        "secondary": {"bloating": 0.70, "early_satiety": 0.65, "vomiting": 0.50, "melena": 0.40},
        "vitals": {"heart_rate": (76.0, 8.0)},
    },
    "Acute Pancreatitis": {
        "hallmarks": {"abdominal_pain": 0.99, "vomiting": 0.94, "nausea": 0.92},
        "secondary": {"fever": 0.78, "bloating": 0.75, "tachypnea": 0.65},
        "vitals": {"body_temperature": (38.3, 0.5), "heart_rate": (112.0, 10.0), "systolic_bp": (108.0, 12.0)},
    },
    "Acute Cholecystitis": {
        "hallmarks": {"abdominal_pain": 0.98, "fever": 0.90, "nausea": 0.88, "vomiting": 0.80},
        "secondary": {"chills": 0.75, "anorexia": 0.75, "jaundice": 0.35},
        "vitals": {"body_temperature": (38.6, 0.5), "heart_rate": (96.0, 8.0)},
    },
    "Acute Appendicitis": {
        "hallmarks": {"abdominal_pain": 0.99, "vomiting": 0.90, "fever": 0.86, "anorexia": 0.85},
        "secondary": {"nausea": 0.85, "constipation": 0.55, "chills": 0.60},
        "vitals": {"body_temperature": (38.4, 0.5), "heart_rate": (98.0, 9.0)},
    },
    "Liver Cirrhosis": {
        "hallmarks": {"ascites": 0.96, "jaundice": 0.92, "leg_swelling": 0.94},
        "secondary": {"dark_urine": 0.82, "clay_colored_stools": 0.78, "itching": 0.70, "confusion": 0.55, "cachexia": 0.60},
        "vitals": {"systolic_bp": (104.0, 10.0), "diastolic_bp": (64.0, 7.0)},
    },
    "Ulcerative Colitis": {
        "hallmarks": {"hematochezia": 0.96, "diarrhea": 0.94, "tenesmus": 0.90},
        "secondary": {"abdominal_pain": 0.85, "weight_loss": 0.75, "fever_low_grade": 0.65, "fatigue": 0.80},
        "vitals": {"heart_rate": (92.0, 9.0)},
    },
    "Crohn's Disease": {
        "hallmarks": {"abdominal_pain": 0.94, "diarrhea": 0.92, "weight_loss": 0.88, "ulcers_oral": 0.78},
        "secondary": {"fever_low_grade": 0.70, "fatigue": 0.85, "joint_pain": 0.60, "anorexia": 0.70},
        "vitals": {"body_temperature": (37.6, 0.4), "bmi": (19.5, 2.0)},
    },
    "Acute Diverticulitis": {
        "hallmarks": {"abdominal_pain": 0.96, "fever": 0.90, "constipation": 0.78},
        "secondary": {"nausea": 0.70, "bloating": 0.72, "chills": 0.65},
        "vitals": {"body_temperature": (38.5, 0.5), "heart_rate": (92.0, 8.0)},
    },
    "Celiac Disease": {
        "hallmarks": {"steatorrhea": 0.94, "diarrhea": 0.92, "weight_loss": 0.88, "bloating": 0.85},
        "secondary": {"flatulence": 0.80, "abdominal_pain": 0.75, "fatigue": 0.85, "pallor": 0.65},
        "vitals": {"bmi": (18.8, 2.0)},
    },

    # 5. Neurological
    "Migraine": {
        "hallmarks": {"visual_aura": 0.86, "photophobia": 0.94, "phonophobia": 0.92, "headache": 0.99},
        "secondary": {"nausea": 0.82, "vomiting": 0.65, "dizziness": 0.60},
        "vitals": {"heart_rate": (74.0, 8.0)},
    },
    "Cluster Headache": {
        "hallmarks": {"eye_pain": 0.98, "epiphora": 0.92, "nasal_congestion": 0.88, "headache": 0.99},
        "secondary": {"photophobia": 0.75, "flushing": 0.65},
        "vitals": {"systolic_bp": (132.0, 10.0)},
    },
    "Tension Headache": {
        "hallmarks": {"headache": 0.99, "stiff_neck": 0.78},
        "secondary": {"fatigue": 0.75, "insomnia": 0.60},
        "vitals": {"systolic_bp": (122.0, 8.0)},
    },
    "Ischemic Stroke": {
        "hallmarks": {"facial_droop": 0.96, "focal_weakness": 0.95, "dysarthria": 0.92},
        "secondary": {"aphasia": 0.80, "ataxia": 0.75, "numbness": 0.78, "vision_loss": 0.65},
        "vitals": {"systolic_bp": (178.0, 16.0), "diastolic_bp": (104.0, 10.0)},
    },
    "Transient Ischemic Attack": {
        "hallmarks": {"focal_weakness": 0.92, "dysarthria": 0.88, "facial_droop": 0.85},
        "secondary": {"vision_loss": 0.72, "numbness": 0.75, "ataxia": 0.65},
        "vitals": {"systolic_bp": (165.0, 14.0)},
    },
    "Benign Paroxysmal Positional Vertigo": {
        "hallmarks": {"vertigo": 0.99, "nausea": 0.88, "gait_unsteadiness": 0.84},
        "secondary": {"vomiting": 0.65, "dizziness": 0.90},
        "vitals": {"heart_rate": (76.0, 7.0)},
    },
    "Parkinson's Disease": {
        "hallmarks": {"tremor": 0.98, "gait_unsteadiness": 0.92, "ataxia": 0.86},
        "secondary": {"fatigue": 0.80, "dysarthria": 0.65, "constipation": 0.60},
        "vitals": {"heart_rate": (72.0, 7.0)},
    },
    "Bell's Palsy": {
        "hallmarks": {"facial_droop": 0.99, "epiphora": 0.88, "loss_of_taste": 0.78},
        "secondary": {"ear_pain": 0.70, "headache": 0.50},
        "vitals": {"systolic_bp": (124.0, 8.0)},
    },
    "Acute Bacterial Meningitis": {
        "hallmarks": {"stiff_neck": 0.98, "fever": 0.96, "photophobia": 0.92, "headache": 0.94},
        "secondary": {"confusion": 0.88, "altered_mental_status": 0.85, "vomiting": 0.75, "purpura": 0.55},
        "vitals": {"body_temperature": (39.5, 0.5), "heart_rate": (115.0, 10.0)},
    },
    "Sciatica": {
        "hallmarks": {"sciatica": 0.99, "numbness": 0.88, "tingling": 0.84},
        "secondary": {"focal_weakness": 0.68, "gait_unsteadiness": 0.60},
        "vitals": {"heart_rate": (72.0, 6.0)},
    },

    # 6. Endocrine & Metabolic
    "Type 1 Diabetes": {
        "hallmarks": {"polyuria": 0.98, "polydipsia": 0.96, "weight_loss": 0.92, "hyperphagia": 0.82},
        "secondary": {"fatigue": 0.85, "blurred_vision": 0.75, "nausea": 0.60},
        "vitals": {"glucose": (285.0, 40.0), "bmi": (19.5, 2.5)},
    },
    "Type 2 Diabetes": {
        "hallmarks": {"polyuria": 0.94, "polydipsia": 0.92, "fatigue": 0.88},
        "secondary": {"blurred_vision": 0.78, "numbness": 0.65, "tingling": 0.60},
        "vitals": {"glucose": (215.0, 30.0), "bmi": (32.5, 4.0)},
    },
    "Hypothyroidism": {
        "hallmarks": {"cold_intolerance": 0.96, "weight_gain": 0.94, "constipation": 0.88},
        "secondary": {"fatigue": 0.92, "dry_mouth": 0.78, "hair_loss": 0.75, "muscle_cramps": 0.70},
        "vitals": {"heart_rate": (56.0, 6.0), "body_temperature": (36.2, 0.3)},
    },
    "Hyperthyroidism": {
        "hallmarks": {"heat_intolerance": 0.96, "tremor": 0.92, "goiter": 0.88, "palpitations": 0.92},
        "secondary": {"excessive_sweating": 0.88, "weight_loss": 0.85, "insomnia": 0.75, "diarrhea": 0.60},
        "vitals": {"heart_rate": (112.0, 10.0), "systolic_bp": (144.0, 10.0)},
    },
    "Cushing's Syndrome": {
        "hallmarks": {"weight_gain": 0.96, "hirsutism": 0.90, "skin_peeling": 0.78},
        "secondary": {"muscle_cramps": 0.75, "generalized_weakness": 0.80, "insomnia": 0.65},
        "vitals": {"systolic_bp": (160.0, 12.0), "bmi": (33.0, 3.5), "glucose": (145.0, 20.0)},
    },
    "Addison's Disease": {
        "hallmarks": {"generalized_weakness": 0.96, "weight_loss": 0.92, "anorexia": 0.90},
        "secondary": {"syncope": 0.78, "presyncope": 0.82, "nausea": 0.75, "vomiting": 0.65, "abdominal_pain": 0.60},
        "vitals": {"systolic_bp": (86.0, 8.0), "diastolic_bp": (54.0, 6.0), "glucose": (65.0, 10.0)},
    },
    "Acute Gout": {
        "hallmarks": {"joint_pain": 0.99, "joint_swelling": 0.96, "erythema": 0.92},
        "secondary": {"fever_low_grade": 0.68, "malaise": 0.60},
        "vitals": {"body_temperature": (37.8, 0.4)},
    },
    "Hypoglycemia": {
        "hallmarks": {"hypoglycemia_symptoms": 0.99, "excessive_sweating": 0.94, "tremor": 0.92, "palpitations": 0.88},
        "secondary": {"confusion": 0.84, "presyncope": 0.80, "seizures": 0.40},
        "vitals": {"glucose": (42.0, 8.0), "heart_rate": (115.0, 10.0)},
    },
    "Diabetic Ketoacidosis": {
        "hallmarks": {"polyuria": 0.96, "vomiting": 0.92, "tachypnea": 0.90, "altered_mental_status": 0.84},
        "secondary": {"polydipsia": 0.90, "abdominal_pain": 0.80, "fatigue": 0.90},
        "vitals": {"glucose": (440.0, 50.0), "systolic_bp": (94.0, 10.0), "heart_rate": (122.0, 10.0)},
    },
    "Primary Hyperparathyroidism": {
        "hallmarks": {"bone_pain": 0.92, "hematuria": 0.82, "constipation": 0.88},
        "secondary": {"abdominal_pain": 0.78, "fatigue": 0.85, "confusion": 0.65},
        "vitals": {"systolic_bp": (138.0, 10.0)},
    },

    # 7. Renal & Urological
    "Acute Cystitis": {
        "hallmarks": {"dysuria": 0.99, "suprapubic_pain": 0.92, "urinary_urgency": 0.94, "urinary_frequency": 0.92},
        "secondary": {"nocturia": 0.75, "hematuria": 0.50},
        "vitals": {"body_temperature": (37.1, 0.3)},
    },
    "Acute Pyelonephritis": {
        "hallmarks": {"flank_pain": 0.96, "fever": 0.94, "chills": 0.92, "dysuria": 0.82},
        "secondary": {"urinary_urgency": 0.78, "nausea": 0.70, "vomiting": 0.65, "urinary_frequency": 0.75},
        "vitals": {"body_temperature": (39.1, 0.5), "heart_rate": (106.0, 10.0)},
    },
    "Nephrolithiasis": {
        "hallmarks": {"flank_pain": 0.99, "hematuria": 0.96},
        "secondary": {"dysuria": 0.68, "urinary_frequency": 0.62, "nausea": 0.70, "vomiting": 0.60},
        "vitals": {"heart_rate": (92.0, 8.0), "systolic_bp": (136.0, 10.0)},
    },
    "Acute Kidney Injury": {
        "hallmarks": {"oliguria": 0.96, "leg_swelling": 0.92},
        "secondary": {"confusion": 0.78, "fatigue": 0.88, "frothy_urine": 0.72, "nausea": 0.70},
        "vitals": {"systolic_bp": (152.0, 14.0), "diastolic_bp": (96.0, 8.0)},
    },
    "Chronic Kidney Disease": {
        "hallmarks": {"frothy_urine": 0.92, "leg_swelling": 0.94, "pallor": 0.88},
        "secondary": {"fatigue": 0.92, "nocturia": 0.85, "pruritus": 0.70, "anorexia": 0.75},
        "vitals": {"systolic_bp": (155.0, 12.0), "diastolic_bp": (95.0, 8.0)},
    },
    "Benign Prostatic Hyperplasia": {
        "hallmarks": {"urinary_hesitancy": 0.99, "nocturia": 0.94, "urinary_frequency": 0.92},
        "secondary": {"urinary_urgency": 0.75, "urinary_incontinence": 0.60, "dysuria": 0.45},
        "vitals": {"age": (68.0, 7.0), "sex": (1.0, 0.0)},
    },
    "Nephrotic Syndrome": {
        "hallmarks": {"frothy_urine": 0.98, "leg_swelling": 0.96, "ascites": 0.90},
        "secondary": {"weight_gain": 0.85, "fatigue": 0.85, "anorexia": 0.70},
        "vitals": {"systolic_bp": (132.0, 10.0)},
    },
    "Acute Glomerulonephritis": {
        "hallmarks": {"hematuria": 0.96, "dark_urine": 0.94, "leg_swelling": 0.90},
        "secondary": {"oliguria": 0.75, "headache": 0.70, "fatigue": 0.80},
        "vitals": {"systolic_bp": (158.0, 12.0), "diastolic_bp": (98.0, 8.0)},
    },
    "Urethritis": {
        "hallmarks": {"dysuria": 0.98, "penile_discharge": 0.92, "urinary_urgency": 0.88},
        "secondary": {"urinary_frequency": 0.82, "itching": 0.65},
        "vitals": {"heart_rate": (74.0, 7.0)},
    },
    "Interstitial Cystitis": {
        "hallmarks": {"suprapubic_pain": 0.98, "urinary_urgency": 0.94, "urinary_frequency": 0.96},
        "secondary": {"nocturia": 0.88, "dysuria": 0.75},
        "vitals": {"heart_rate": (76.0, 7.0)},
    },

    # 8. Rheumatology & Musculoskeletal
    "Osteoarthritis": {
        "hallmarks": {"joint_pain": 0.98, "morning_stiffness": 0.78, "joint_swelling": 0.72},
        "secondary": {"gait_unsteadiness": 0.65, "fatigue": 0.50},
        "vitals": {"age": (65.0, 8.0)},
    },
    "Rheumatoid Arthritis": {
        "hallmarks": {"joint_swelling": 0.98, "morning_stiffness": 0.96, "joint_pain": 0.96},
        "secondary": {"fatigue": 0.88, "fever_low_grade": 0.70, "malaise": 0.80, "weight_loss": 0.60},
        "vitals": {"body_temperature": (37.4, 0.3)},
    },
    "Systemic Lupus Erythematosus": {
        "hallmarks": {"butterfly_rash": 0.96, "joint_swelling": 0.92, "photosensitivity": 0.90},
        "secondary": {"fatigue": 0.92, "fever_low_grade": 0.78, "hair_loss": 0.70, "ulcers_oral": 0.65, "raynaud_phenomenon": 0.60},
        "vitals": {"body_temperature": (37.6, 0.4), "systolic_bp": (125.0, 10.0)},
    },
    "Ankylosing Spondylitis": {
        "hallmarks": {"morning_stiffness": 0.98, "joint_pain": 0.95, "eye_redness": 0.78},
        "secondary": {"fatigue": 0.82, "pleuritic_chest_pain": 0.65, "eye_pain": 0.70},
        "vitals": {"age": (32.0, 6.0), "sex": (1.0, 0.0)},
    },
    "Fibromyalgia": {
        "hallmarks": {"generalized_weakness": 0.96, "insomnia": 0.94, "fatigue": 0.98, "myalgia": 0.90},
        "secondary": {"headache": 0.80, "morning_stiffness": 0.70, "depression": 0.75},
        "vitals": {"heart_rate": (74.0, 8.0)},
    },
    "Polymyalgia Rheumatica": {
        "hallmarks": {"morning_stiffness": 0.98, "joint_pain": 0.92, "generalized_weakness": 0.88},
        "secondary": {"fever_low_grade": 0.75, "fatigue": 0.85, "weight_loss": 0.65},
        "vitals": {"age": (70.0, 6.0), "body_temperature": (37.5, 0.3)},
    },
    "Systemic Sclerosis": {
        "hallmarks": {"skin_thickening": 0.98, "raynaud_phenomenon": 0.94, "dysphagia": 0.88},
        "secondary": {"heartburn": 0.80, "joint_pain": 0.75, "fatigue": 0.80},
        "vitals": {"systolic_bp": (138.0, 12.0)},
    },
    "Sjögren's Syndrome": {
        "hallmarks": {"dry_eyes": 0.99, "dry_mouth": 0.98, "joint_pain": 0.82},
        "secondary": {"fatigue": 0.88, "lymphadenopathy": 0.60, "dysphagia": 0.65},
        "vitals": {"age": (54.0, 8.0)},
    },
    "Psoriatic Arthritis": {
        "hallmarks": {"skin_rash": 0.94, "joint_swelling": 0.92, "joint_pain": 0.92, "nail_clubbing": 0.78},
        "secondary": {"morning_stiffness": 0.82, "fatigue": 0.75},
        "vitals": {"heart_rate": (76.0, 7.0)},
    },
    "Dermatomyositis": {
        "hallmarks": {"focal_weakness": 0.96, "skin_rash": 0.92, "erythema": 0.88},
        "secondary": {"dysphagia": 0.78, "joint_pain": 0.75, "fatigue": 0.85},
        "vitals": {"heart_rate": (78.0, 8.0)},
    },

    # 9. Dermatology
    "Plaque Psoriasis": {
        "hallmarks": {"skin_rash": 0.98, "skin_peeling": 0.94, "erythema": 0.85},
        "secondary": {"itching": 0.80, "nail_clubbing": 0.65},
        "vitals": {"heart_rate": (74.0, 7.0)},
    },
    "Atopic Dermatitis": {
        "hallmarks": {"skin_rash": 0.98, "itching": 0.99, "skin_peeling": 0.88},
        "secondary": {"erythema": 0.85, "insomnia": 0.60},
        "vitals": {"heart_rate": (74.0, 7.0)},
    },
    "Herpes Zoster": {
        "hallmarks": {"bullae": 0.98, "skin_rash": 0.95, "tingling": 0.92},
        "secondary": {"fever_low_grade": 0.70, "headache": 0.60, "fatigue": 0.70},
        "vitals": {"body_temperature": (37.5, 0.4)},
    },
    "Cellulitis": {
        "hallmarks": {"erythema": 0.99, "fever": 0.88, "chills": 0.80},
        "secondary": {"leg_swelling": 0.85, "fatigue": 0.75},
        "vitals": {"body_temperature": (38.6, 0.5), "heart_rate": (94.0, 9.0)},
    },
    "Scabies": {
        "hallmarks": {"itching": 0.99, "skin_rash": 0.95, "skin_peeling": 0.82},
        "secondary": {"insomnia": 0.75, "erythema": 0.70},
        "vitals": {"heart_rate": (72.0, 6.0)},
    },
    "Acute Urticaria": {
        "hallmarks": {"hives": 0.99, "itching": 0.98, "erythema": 0.88},
        "secondary": {"flushing": 0.75, "angioedema": 0.50},
        "vitals": {"heart_rate": (78.0, 8.0)},
    },
    "Contact Dermatitis": {
        "hallmarks": {"skin_rash": 0.98, "itching": 0.94, "erythema": 0.92},
        "secondary": {"bullae": 0.70, "skin_peeling": 0.65},
        "vitals": {"heart_rate": (72.0, 6.0)},
    },
    "Impetigo": {
        "hallmarks": {"skin_rash": 0.98, "bullae": 0.92, "itching": 0.82},
        "secondary": {"erythema": 0.80, "lymphadenopathy": 0.65},
        "vitals": {"body_temperature": (37.4, 0.3)},
    },
    "Alopecia Areata": {
        "hallmarks": {"hair_loss": 0.99},
        "secondary": {"itching": 0.40},
        "vitals": {"heart_rate": (72.0, 6.0)},
    },
    "Erythema Multiforme": {
        "hallmarks": {"skin_rash": 0.98, "erythema": 0.95, "ulcers_oral": 0.84},
        "secondary": {"fever_low_grade": 0.70, "joint_pain": 0.60},
        "vitals": {"body_temperature": (37.6, 0.4)},
    },

    # 10. ENT & Ophthalmology
    "Acute Otitis Media": {
        "hallmarks": {"ear_pain": 0.99, "fever": 0.92, "hearing_loss": 0.88},
        "secondary": {"ear_discharge": 0.80, "tinnitus": 0.65, "headache": 0.70},
        "vitals": {"body_temperature": (38.7, 0.5), "heart_rate": (94.0, 8.0)},
    },
    "Acute Sinusitis": {
        "hallmarks": {"nasal_congestion": 0.98, "purulent_sputum": 0.90, "headache": 0.92},
        "secondary": {"fever_low_grade": 0.75, "facial_pain": 0.85, "halitosis": 0.60},
        "vitals": {"body_temperature": (37.8, 0.4)},
    },
    "Streptococcal Pharyngitis": {
        "hallmarks": {"sore_throat": 0.99, "fever": 0.94, "odynophagia": 0.92, "lymphadenopathy": 0.88},
        "secondary": {"headache": 0.75, "malaise": 0.80, "chills": 0.70},
        "vitals": {"body_temperature": (38.9, 0.5), "heart_rate": (96.0, 8.0)},
    },
    "Acute Angle-Closure Glaucoma": {
        "hallmarks": {"eye_pain": 0.99, "vision_loss": 0.94, "eye_redness": 0.92},
        "secondary": {"photophobia": 0.85, "headache": 0.90, "nausea": 0.80, "vomiting": 0.70},
        "vitals": {"systolic_bp": (148.0, 12.0), "heart_rate": (88.0, 8.0)},
    },
    "Infectious Conjunctivitis": {
        "hallmarks": {"eye_redness": 0.99, "epiphora": 0.92, "foreign_body_sensation": 0.88},
        "secondary": {"photophobia": 0.75, "itching": 0.70},
        "vitals": {"body_temperature": (37.2, 0.3)},
    },
    "Allergic Rhinitis": {
        "hallmarks": {"rhinorrhea": 0.98, "nasal_congestion": 0.95, "itching": 0.88},
        "secondary": {"epiphora": 0.85, "headache": 0.60},
        "vitals": {"heart_rate": (72.0, 6.0)},
    },
    "Peritonsillar Abscess": {
        "hallmarks": {"sore_throat": 0.99, "dysphagia": 0.96, "fever": 0.92, "ear_pain": 0.84},
        "secondary": {"hoarseness": 0.80, "chills": 0.75, "trismus": 0.80},
        "vitals": {"body_temperature": (39.1, 0.5), "heart_rate": (102.0, 10.0)},
    },
    "Ménière's Disease": {
        "hallmarks": {"vertigo": 0.99, "tinnitus": 0.96, "hearing_loss": 0.94},
        "secondary": {"nausea": 0.88, "vomiting": 0.75, "gait_unsteadiness": 0.80},
        "vitals": {"heart_rate": (76.0, 7.0)},
    },
    "Otitis Externa": {
        "hallmarks": {"ear_pain": 0.99, "ear_discharge": 0.92, "itching": 0.88},
        "secondary": {"hearing_loss": 0.72, "fever_low_grade": 0.50},
        "vitals": {"heart_rate": (74.0, 6.0)},
    },
    "Bacterial Keratitis": {
        "hallmarks": {"eye_pain": 0.99, "eye_redness": 0.96, "foreign_body_sensation": 0.92, "vision_loss": 0.84},
        "secondary": {"photophobia": 0.88, "epiphora": 0.85},
        "vitals": {"body_temperature": (37.1, 0.2)},
    },
}


# ---------------------------------------------------------------------------
# Clinically Realistic Synthetic Development Generator
# ---------------------------------------------------------------------------

# --- generate_synthetic_dev_data ---
# What it does: Synthesizes clinically realistic patient cases with symptom distributions and vital sign noise.
# Why it's structured this way: Allows deterministic offline model development and unit testing without accessing protected health information (PHI).
# Parameters & Returns: n_samples_per_class (int), random_state (int), schema_version (str) -> pd.DataFrame.
# ------------------------------------------------------------------------------
def generate_synthetic_dev_data(
    n_samples_per_class: int = 150,
    random_state: int = 42,
    output_path: Optional[str] = None,
    schema_version: str = "1.0.0",
    target_classes: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Generates clinically realistic development dataset.
    - If schema_version == '2.0.0' or target_classes == DISEASE_CLASSES_100:
      Uses 163 features (154 symptoms + 9 vitals) and 100 disease classes.
    - Else (schema_version == '1.0.0'):
      Uses 27 features (18 symptoms + 9 vitals) and 8 disease classes (backward compatible).
    """
    rng = np.random.default_rng(random_state)

    if schema_version in ("2.0.0", "v2") or (target_classes and len(target_classes) == 100):
        preprocessor = get_preprocessor_v2()
        feature_order = list(preprocessor.feature_order)
        classes = target_classes or DISEASE_CLASSES_100
        n_symptoms = len(feature_order) - 9
        symptom_features = feature_order[:n_symptoms]

        records: List[Dict[str, Any]] = []

        for disease in classes:
            prof = CLINICAL_PROFILES_100.get(disease, {})
            hallmarks = prof.get("hallmarks", {})
            secondary = prof.get("secondary", {})
            vitals_dist = prof.get("vitals", {})

            for _ in range(n_samples_per_class):
                # Initialize symptoms with low background noise (0.01 - 0.03)
                row: Dict[str, Any] = {
                    feat: (1.0 if rng.random() < 0.015 else 0.0)
                    for feat in symptom_features
                }

                # Apply hallmarks and secondary symptoms
                for sym, prob in hallmarks.items():
                    if sym in row:
                        row[sym] = 1.0 if rng.random() < prob else 0.0
                for sym, prob in secondary.items():
                    if sym in row:
                        row[sym] = 1.0 if rng.random() < prob else 0.0

                # Base vitals baseline
                age = float(rng.integers(18, 85))
                sex = float(rng.choice([1.0, 0.0], p=[0.48, 0.52]))
                systolic_bp = float(rng.normal(122.0, 10.0))
                diastolic_bp = float(rng.normal(80.0, 7.0))
                heart_rate = float(rng.normal(74.0, 9.0))
                glucose = float(rng.normal(95.0, 12.0))
                body_temperature = float(rng.normal(36.8, 0.4))
                oxygen_saturation = float(rng.normal(98.2, 1.0))
                bmi = float(rng.normal(25.0, 3.5))

                # Override with condition-specific vitals distribution
                for v_name, (v_mean, v_std) in vitals_dist.items():
                    if v_name == "systolic_bp":
                        systolic_bp = float(rng.normal(v_mean, v_std))
                    elif v_name == "diastolic_bp":
                        diastolic_bp = float(rng.normal(v_mean, v_std))
                    elif v_name == "heart_rate":
                        heart_rate = float(rng.normal(v_mean, v_std))
                    elif v_name == "glucose":
                        glucose = float(rng.normal(v_mean, v_std))
                    elif v_name == "body_temperature":
                        body_temperature = float(rng.normal(v_mean, v_std))
                    elif v_name == "oxygen_saturation":
                        oxygen_saturation = float(rng.normal(v_mean, v_std))
                    elif v_name == "bmi":
                        bmi = float(rng.normal(v_mean, v_std))
                    elif v_name == "age":
                        age = float(rng.normal(v_mean, v_std))
                    elif v_name == "sex":
                        sex = float(v_mean)

                # Realistic Outpatient Missingness (40-70% in non-essential vitals)
                # Keep vital intact if it is a primary diagnostic biomarker
                p_miss = rng.uniform(0.40, 0.70)
                if "glucose" not in vitals_dist and rng.random() < p_miss:
                    glucose = np.nan
                if "oxygen_saturation" not in vitals_dist and rng.random() < p_miss:
                    oxygen_saturation = np.nan
                if "bmi" not in vitals_dist and rng.random() < p_miss:
                    bmi = np.nan
                if "systolic_bp" not in vitals_dist and rng.random() < (p_miss * 0.8):
                    systolic_bp = np.nan
                    diastolic_bp = np.nan
                if "body_temperature" not in vitals_dist and rng.random() < 0.25:
                    body_temperature = np.nan
                if "heart_rate" not in vitals_dist and rng.random() < 0.25:
                    heart_rate = np.nan

                row["age"] = age
                row["sex"] = sex
                row["systolic_bp"] = systolic_bp
                row["diastolic_bp"] = diastolic_bp
                row["heart_rate"] = heart_rate
                row["glucose"] = glucose
                row["body_temperature"] = body_temperature
                row["oxygen_saturation"] = oxygen_saturation
                row["bmi"] = bmi

                row["target_disease"] = disease
                records.append(row)

        df = pd.DataFrame(records)

    else:
        # v1.0.0 (27 features, 8 classes)
        preprocessor = get_preprocessor(version="1.0.0")
        feature_order = list(preprocessor.feature_order)
        classes = target_classes or DEFAULT_DISEASE_CLASSES

        records = []
        for disease in classes:
            for _ in range(n_samples_per_class):
                row = {feat: 0.0 for feat in feature_order[:18]}

                age = float(rng.integers(18, 85))
                sex = float(rng.choice([1.0, 0.0], p=[0.48, 0.52]))
                systolic_bp = float(rng.normal(122, 10))
                diastolic_bp = float(rng.normal(80, 7))
                heart_rate = float(rng.normal(74, 9))
                glucose = float(rng.normal(95, 12))
                body_temperature = float(rng.normal(36.8, 0.4))
                oxygen_saturation = float(rng.normal(98.2, 1.0))
                bmi = float(rng.normal(25.0, 3.5))

                if disease == "Influenza":
                    row["fever"] = 1.0 if rng.random() < 0.94 else 0.0
                    row["body_aches"] = 1.0 if rng.random() < 0.90 else 0.0
                    row["chills"] = 1.0 if rng.random() < 0.88 else 0.0
                    row["fatigue"] = 1.0 if rng.random() < 0.92 else 0.0
                    row["headache"] = 1.0 if rng.random() < 0.78 else 0.0
                    row["cough"] = 1.0 if rng.random() < 0.72 else 0.0
                    body_temperature = float(rng.normal(38.9, 0.5))
                    heart_rate = float(rng.normal(92, 10))
                elif disease == "Common Cold":
                    row["rhinorrhea"] = 1.0 if rng.random() < 0.96 else 0.0
                    row["sore_throat"] = 1.0 if rng.random() < 0.90 else 0.0
                    row["cough"] = 1.0 if rng.random() < 0.75 else 0.0
                    body_temperature = float(rng.normal(37.1, 0.3))
                elif disease == "Pneumonia":
                    row["dyspnea"] = 1.0 if rng.random() < 0.94 else 0.0
                    row["cough"] = 1.0 if rng.random() < 0.95 else 0.0
                    row["fever"] = 1.0 if rng.random() < 0.90 else 0.0
                    body_temperature = float(rng.normal(38.8, 0.6))
                    oxygen_saturation = float(rng.normal(91.5, 2.5))
                elif disease == "Type 2 Diabetes":
                    row["polyuria"] = 1.0 if rng.random() < 0.95 else 0.0
                    row["polydipsia"] = 1.0 if rng.random() < 0.92 else 0.0
                    row["fatigue"] = 1.0 if rng.random() < 0.85 else 0.0
                    glucose = float(rng.normal(215, 30))
                    bmi = float(rng.normal(32.5, 4.0))
                elif disease == "Hypertension":
                    row["headache"] = 1.0 if rng.random() < 0.60 else 0.0
                    row["dizziness"] = 1.0 if rng.random() < 0.55 else 0.0
                    systolic_bp = float(rng.normal(168, 12))
                    diastolic_bp = float(rng.normal(102, 8))
                elif disease == "Migraine":
                    row["headache"] = 1.0 if rng.random() < 0.99 else 0.0
                    row["photophobia"] = 1.0 if rng.random() < 0.92 else 0.0
                    row["nausea"] = 1.0 if rng.random() < 0.78 else 0.0
                elif disease == "Acute Gastroenteritis":
                    row["diarrhea"] = 1.0 if rng.random() < 0.98 else 0.0
                    row["nausea"] = 1.0 if rng.random() < 0.88 else 0.0
                    row["body_temperature"] = float(rng.normal(37.8, 0.5))
                elif disease == "Bronchial Asthma":
                    row["dyspnea"] = 1.0 if rng.random() < 0.96 else 0.0
                    row["cough"] = 1.0 if rng.random() < 0.80 else 0.0
                    oxygen_saturation = float(rng.normal(91.0, 2.5))

                p_miss = rng.uniform(0.40, 0.70)
                if disease != "Type 2 Diabetes" and rng.random() < p_miss:
                    glucose = np.nan
                if disease not in ["Pneumonia", "Bronchial Asthma"] and rng.random() < p_miss:
                    oxygen_saturation = np.nan
                if disease != "Type 2 Diabetes" and rng.random() < p_miss:
                    bmi = np.nan
                if disease != "Hypertension" and rng.random() < (p_miss * 0.8):
                    systolic_bp = np.nan
                    diastolic_bp = np.nan

                row["age"] = age
                row["sex"] = sex
                row["systolic_bp"] = systolic_bp
                row["diastolic_bp"] = diastolic_bp
                row["heart_rate"] = heart_rate
                row["glucose"] = glucose
                row["body_temperature"] = body_temperature
                row["oxygen_saturation"] = oxygen_saturation
                row["bmi"] = bmi

                row["target_disease"] = disease
                records.append(row)

        df = pd.DataFrame(records)

    # Ensure output directory and save
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"[+] Saved synthetic dataset ({len(df)} rows, {len(df.columns)} cols) to: {output_path}")

    return df


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------

# --- train_model ---
# What it does: Trains multi-class XGBoost model, computes cross-entropy log loss and F1-scores, and saves serializations.
# Why it's structured this way: Enforces strict data splits, class weight balancing, and atomic artifact export for reproducible ML pipelines.
# Parameters & Returns: data_path, output_dir, test_size, schema_version -> training metadata dictionary.
# ------------------------------------------------------------------------------
def train_model(
    data_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    generate_dev: bool = False,
    n_samples_per_class: int = 150,
    schema_version: str = "1.0.0",
    target_classes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Executes training pipeline for multi-class XGBoost classifier.
    Supports version="1.0.0" (8 classes) and version="2.0.0" (100 classes).
    Saves xgboost_model.joblib, synced schema.json, and metadata.json.
    """
    is_v2 = schema_version in ("2.0.0", "v2") or (target_classes and len(target_classes) == 100)
    actual_version = "2.0.0" if is_v2 else "1.0.0"

    output_dir = output_dir or (DEFAULT_ARTIFACT_DIR_V2 if is_v2 else DEFAULT_ARTIFACT_DIR_V1)
    os.makedirs(output_dir, exist_ok=True)

    preprocessor = get_preprocessor_v2() if is_v2 else get_preprocessor(version="1.0.0")
    feature_order = list(preprocessor.feature_order)

    # 1. Dataset Acquisition
    df: Optional[pd.DataFrame] = None
    dataset_provenance = "synthetic-dev-fallback"

    if data_path and os.path.exists(data_path) and not generate_dev:
        print(f"[*] Loading training dataset from: {data_path}")
        df = pd.read_csv(data_path)
        dataset_provenance = os.path.basename(data_path)
    else:
        print(f"[*] Generating synthetic dev dataset (version={actual_version}, n_samples={n_samples_per_class}/class)...")
        df = generate_synthetic_dev_data(
            n_samples_per_class=n_samples_per_class,
            random_state=random_state,
            output_path=data_path,
            schema_version=actual_version,
            target_classes=target_classes,
        )

    # Validate schema features
    missing_cols = [f for f in feature_order if f not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required schema features: {missing_cols[:10]}")

    X = df[feature_order].copy()
    y_raw = df["target_disease"].copy()

    # 2. Label Encoding
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    classes = list(label_encoder.classes_)

    # 3. Stratified Train / Validation Split
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )

    # 4. Balanced Sample Weighting
    sample_weights = compute_sample_weight("balanced", y_train)

    # 5. XGBoost Classifier Configuration (Native NaN support)
    n_estimators = 120 if is_v2 else 100
    max_depth = 6 if is_v2 else 5
    learning_rate = 0.08

    print(f"[*] Training multi-class XGBoost model on {len(X_train)} samples across {len(classes)} classes...")
    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.85,
        colsample_bytree=0.85,
        missing=np.nan,  # Native directional split routing for unmeasured vitals
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # 6. Evaluation
    y_pred = model.predict(X_val)
    y_prob = model.predict_proba(X_val)

    macro_f1 = float(f1_score(y_val, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_val, y_pred, average="weighted"))
    acc = float(accuracy_score(y_val, y_pred))
    loss = float(log_loss(y_val, y_prob))
    report = classification_report(y_val, y_pred, target_names=classes, output_dict=True)

    print(f"[*] Training complete. Validation Metrics:")
    print(f"    - Macro F1-Score: {macro_f1:.4f}")
    print(f"    - Weighted F1:    {weighted_f1:.4f}")
    print(f"    - Accuracy:       {acc:.4f}")
    print(f"    - Log-Loss:       {loss:.4f}")

    # 7. Artifact Serialization
    # A. xgboost_model.joblib
    model_artifact_path = os.path.join(output_dir, "xgboost_model.joblib")
    artifact_payload = {
        "model": model,
        "label_encoder": label_encoder,
        "classes": classes,
        "feature_order": feature_order,
        "schema_version": actual_version,
    }
    joblib.dump(artifact_payload, model_artifact_path)
    print(f"[+] Serialized model artifact to: {model_artifact_path}")

    # B. schema.json (Synced contract copy)
    schema_source = SCHEMA_SOURCE_PATH_V2 if is_v2 else SCHEMA_SOURCE_PATH_V1
    artifact_schema_path = os.path.join(output_dir, "schema.json")
    if os.path.exists(schema_source):
        shutil.copy2(schema_source, artifact_schema_path)
        print(f"[+] Synced schema contract to: {artifact_schema_path}")

    # C. metadata.json
    metadata_payload = {
        "model_name": "MediCare-MultiDisease-XGBoost",
        "version": actual_version,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_provenance": dataset_provenance,
        "target_classes": classes,
        "total_classes": len(classes),
        "total_features": len(feature_order),
        "feature_order": feature_order,
        "metrics": {
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "accuracy": round(acc, 4),
            "log_loss": round(loss, 4),
            "per_class_metrics": {
                c: {
                    "precision": round(report[c]["precision"], 4),
                    "recall": round(report[c]["recall"], 4),
                    "f1_score": round(report[c]["f1-score"], 4),
                    "support": int(report[c]["support"]),
                }
                for c in classes
                if c in report
            },
        },
        "training_config": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "missing_value_handling": "native_directional_split_np_nan",
            "objective": "multi:softprob",
        },
    }

    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2)
    print(f"[+] Serialized metadata manifest to: {metadata_path}")

    return {
        "model_path": model_artifact_path,
        "schema_path": artifact_schema_path,
        "metadata_path": metadata_path,
        "metrics": metadata_payload["metrics"],
        "classes": classes,
        "dataset_provenance": dataset_provenance,
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

# --- main ---
# What it does: Command-line entrypoint parsing arguments (--version, --data, --output-dir) and executing model training.
# Why it's structured this way: Enables automated MLOps retraining from terminal or continuous integration scripts.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="MediCare Multi-Disease Model Training & Artifact Serialization"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="2.0.0",
        choices=["1.0.0", "2.0.0"],
        help="Model / schema version to train (default: 2.0.0 for 100 diseases)",
    )
    parser.add_argument(
        "--generate-dev-data",
        action="store_true",
        help="Generate synthetic clinical development dataset in backend/ml/data/",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to training data CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to output artifacts directory",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=150,
        help="Samples per class for development generator (default: 150 -> 15,000 total for v2)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Hold-out validation split ratio (default: 0.2)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    train_model(
        data_path=args.data_path,
        output_dir=args.output_dir,
        test_size=args.test_size,
        random_state=args.random_state,
        generate_dev=args.generate_dev_data,
        n_samples_per_class=args.n_samples,
        schema_version=args.version,
    )


if __name__ == "__main__":
    main()
