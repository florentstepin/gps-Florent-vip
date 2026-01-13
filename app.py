import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="L'Architecte de Projet",
    page_icon="🏗️",
    layout="centered"
)

# --- 1. GESTION DES SECRETS & CONNEXIONS ---
# Assurez-vous d'avoir configuré .streamlit/secrets.toml sur Streamlit Cloud
try:
    GENAI_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GENAI_API_KEY)
except Exception as e:
    st.error("Erreur de configuration des secrets (API Key).")
    st.stop()

# --- 2. LES PROMPTS SYSTEME (Extrait de vos PDFs) ---

PROMPT_AUDIT_DUR = """
Rôle : Tu agis en tant qu'Ingénieur en Stratégie d'Entreprise spécialisé dans l'audit de viabilité (Stress-Test).
Ta posture est froide, clinique et bienveillante par ta rigueur.
Mission : Analyse cette idée impitoyablement à travers le Framework D.U.R.

Critères à noter sur 10 :
1. D - DOULOUREUX : À quel point le problème est-il une souffrance active ? Vitamine ou Aspirine ?
2. U - URGENT : Y a-t-il un coût immédiat à l'inaction ?
3. R - RECONNU : La cible cherche-t-elle activement une solution ?

Livrable attendu :
- Le Tableau des Scores D.U.R.
- 3 "Fractures Structurelles" (failles logiques).
- VERDICT : GO / NO-GO / PIVOT.
- Justification technique courte.

IDÉE À TESTER : {user_idea}
"""

PROMPT_EXPLORATEUR = """
Rôle : Tu es un Stratège en Innovation de Rupture.
Mission : Génère 10 angles d'attaque radicalement différents pour ce projet.
Pour chaque angle, fais varier une variable clé (Cible, Enjeu, Mécanisme, Opposé).

Format de sortie pour chaque angle :
1. Titre accrocheur
2. La Cible précise
3. Pourquoi c'est une opportunité (La différence)

PROJET D'ORIGINE : {user_idea}
CONTEXTE : L'idée a besoin de divergence pour éviter la vision tunnel.
"""

PROMPT_PLAN_BACKCASTING = """
Rôle : Agis comme un Chef de Projet expert en méthode Agile.
Objectif : Avoir une version 1 (MVP) prête à être testée dans 7 jours.
Méthode : Utilise le "Backcasting". Pars du jour 7 (Lancement) et remonte jusqu'à aujourd'hui.

Contrainte : Donne UNIQUEMENT une action majeure par jour. Pas de bruit.
Format de sortie : Markdown clair, prêt à être copié dans Obsidian.

STRATÉGIE VALIDÉE : {selected_angle}
"""

# --- 3. FONCTIONS UTILITAIRES ---

def check_license(key):
    """Vérifie la licence dans Google Sheets."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read()
        
        # On nettoie les espaces éventuels
        key = key.strip()
        
        # Vérification si la clé existe
        if key in df['Licence_Key'].values:
            user_row = df[df['Licence_Key'] == key].iloc[0]
            credits_used = user_row['Audits_Consommes']
            
            if credits_used < 20: # Limite de 20 audits
                return True, credits_used
            else:
                return False, "Quota épuisé (20/20)."
        else:
            return False, "Clé inconnue."
    except Exception as e:
        return False, f"Erreur de connexion BDD: {str(e)}"

def increment_credit(key):
    """Incrémente le compteur de crédits (Simulation pour l'instant)"""
    # Note : Pour l'écriture réelle dans GSheets, il faut configurer les permissions d'écriture
    # ou utiliser une API tierce plus simple pour le MVP.
    # Ici, pour le MVP Streamlit Cloud gratuit, on simule l'incrément en session
    # ou on
