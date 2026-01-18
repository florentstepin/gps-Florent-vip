import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Stratège IA : De l'Idée à l'Action", page_icon="🎯", layout="wide")

# ==============================================================================
# 🛑 ZONE DE CONFIGURATION (VOS CLÉS)
# ==============================================================================
# 1. Vos clés SUPABASE 
SUPABASE_URL = "https://idvkrilkrfpzdmmmxgnj.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkdmtyaWxrcmZwemRtbW14Z25qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzNjY4NTIsImV4cCI6MjA4Mzk0Mjg1Mn0.pmjlyfNbe_4V4j26KeiFgUkNzI9tz9zPY3DwJho_RRU"
# 2. Votre clé GOOGLE GEMINI 
GOOGLE_API_KEY = "AIzaSyDsYZxJmLnLtfeA60IDDLnRv9Sm8cMdYdw"
# 3. Votre lien de paiement 
LIEN_PAIEMENT = "https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67"
# 4. Modèle IA
MODEL_NAME = 'gemini-2.5-flash'
# 5. Lien "Besoin d'un regard humain" (Architecte) - Votre Google Form
LIEN_ARCHITECTE = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform?usp=dialog"

# ==============================================================================

# --- INITIALISATION & CONNEXIONS ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"❌ Erreur config : {e}")
    st.stop()

# --- GESTION ÉTAT (SESSION STATE) ---
# On initialise les variables pour mémoriser l'avancement dans le tunnel
if "step" not in st.session_state: st.session_state.step = 1
if "analysis_data" not in st.session_state: st.session_state.analysis_data = {}
if "selected_pivot" not in st.session_state: st.session_state.selected_pivot = None
if "initial_idea" not in st.session_state: st.session_state.initial_idea = ""

# --- FONCTIONS UTILITAIRES ---

def get_user(code):
    try:
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        return res.data[0] if res.data else None
    except: return None

def debit_credit(user_id, current):
    try:
        new = max(0, current - 1)
        supabase.table("users").update({"credits": new}).eq("id", user_id).execute()
        return new
    except: return current

def save_json():
    """Génère le fichier JSON de sauvegarde"""
    data = {
        "step": st.session_state.step,
        "idea": st.session_state.initial_idea,
        "analysis": st.session_state.analysis_data,
        "pivot": st.session_state.selected_pivot
    }
    return json.dumps(data, indent=4)

def load_json(uploaded_file):
    """Charge un état depuis un JSON"""
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.step = data.get("step", 1)
            st.session_state.initial_idea = data.get("idea", "")
            st.session_state.analysis_data = data.get("analysis", {})
            st.session_state.selected_pivot = data.get("pivot", None)
            st.success("Projet chargé avec succès !")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Erreur de lecture JSON : {e}")

# --- LOGIN ---
if "user" not in st.session_state:
    qp = st.query_params
    code_url = qp.get("code") or qp.get("access_code")
    if code_url:
        u = get_user(code_url)
        if u:
            st.session_state["user"] = u
            st.rerun()

# --- INTERFACE ---
if "user" not in st.session_state:
    st.title("🔐 Espace Stratégique")
    c = st.text_input("Code d'accès :")
    if st.button("Entrer"):
        u = get_user(c)
        if u:
            st.session_state["user"] = u
            st.rerun()
        else: st.error("Code invalide")
    st.stop()

user = st.session_state["user"]
credits = user["credits"]

# --- SIDEBAR (Compte & Outils) ---
with st.sidebar:
    st.header("🎛️ Tableau de bord")
    st.write(f"👤 {user['email']}")
    
    if credits > 0:
        st.metric("Crédits", credits, delta="Actif")
    else:
        st.error("Crédits épuisés")
        st.markdown(f"[👉 **Recharger**]({LIEN_RECHARGE})")
    
    st.divider()
    st.markdown("### 💾 Sauvegarde / Reprise")
    
    # Bouton Sauvegarder
    json_str = save_json()
    st.download_button("📥 Télécharger mon projet (.json)", json_str, "mon_projet_ia.json", "application/json")
    
    # Bouton Charger
    uploaded = st.file_uploader("📤 Reprendre un projet", type="json")
    if uploaded: load_json(uploaded)

    st.divider()
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

# --- MAIN FLOW ---

st.title("🚀 Accélérateur de Projets IA")

# Barre de progression visuelle
steps = ["1. Analyse & Verdict", "2. Pivot (Optionnel)", "3. Plan d'Action (GPS)"]
curr_step_idx = st.session_state.step - 1
st.progress(st.session_state.step / 3)
st.caption(f"Étape actuelle : {steps[min(curr_step_idx, 2)]}")

# --- ÉTAPE 1 : L'AVOCAT DU DIABLE + VERDICT ---
if st.session_state.step == 1:
    st.subheader("1️⃣ Le Crash Test (Avocat du Diable)")
    
    if credits > 0:
        user_input = st.text_area("Votre idée brute :", value=st.session_state.initial_idea, height=150)
        
        if st.button("Lancer l'analyse (1 crédit)"):
            if not user_input:
                st.warning("Décrivez votre idée.")
            else:
                st.session_state.initial_idea = user_input
                with st.spinner("Analyse critique en cours..."):
                    # Prompt Verdict
                    prompt = f"""
                    Agis comme un investisseur exigeant. Analyse : "{user_input}".
                    
                    1. CRITIQUE : 3 failles mortelles et 1 biais cognitif.
                    2. VERDICT : Choisis UN seul parmi : [GO], [NOGO], ou [PIVOT].
                    Justifie le verdict en une phrase choc.
                    
                    Formate en Markdown.
                    """
                    res = model.generate_content(prompt)
                    st.session_state.analysis_data["step1"] = res.text
                    
                    # Débit crédit
                    new_c = debit_credit(user["id"], credits)
                    user["credits"] = new_c
                    st.session_state["user"] = user
                    st.rerun()
    else:
        st.warning("Rechargez vos crédits pour commencer.")

    # Affichage Résultat Étape 1
    if "step1" in st.session_state.analysis_data:
        st.divider()
        st.markdown(st.session_state.analysis_data["step1"])
        
        st.info("💡 Besoin d'un regard humain expert pour trancher ?")
        st.markdown(f"👉 **[Demander un Audit Architecte (Optionnel)]({LIEN_ARCHITECTE})**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➡️ Continuer vers le Plan d'Action (GO)"):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("🔄 Explorer des Alternatives (PIVOT)"):
                st.session_state.step = 2
                st.rerun()

# --- ÉTAPE 2 : LE PIVOT (Génération d'alternatives) ---
elif st.session_state.step == 2:
    st.subheader("2️⃣ Le Laboratoire à Pivots")
    st.write("Votre idée initiale a du potentiel, mais nécessite un ajustement. Voici des pistes.")
    
    if "step2" not in st.session_state.analysis_data:
        with st.spinner("Génération des pivots..."):
            prompt_pivot = f"""
            L'idée de base est : "{st.session_state.initial_idea}".
            Le verdict précédent suggérait un pivot.
            Propose 3 variations radicales (Pivots) pour rendre ce projet viable et rentable.
            Pour chaque pivot : Titre, Concept en 1 phrase, Pourquoi ça marche.
            """
            res = model.generate_content(prompt_pivot)
            st.session_state.analysis_data["step2"] = res.text
    
    st.markdown(st.session_state.analysis_data["step2"])
    
    st.divider()
    st.write("Quelle version choisissez-vous pour le plan d'action ?")
    
    options = ["Je garde mon idée initiale (têtue)", "Pivot 1", "Pivot 2", "Pivot 3"]
    choice = st.radio("Votre choix :", options)
    
    if st.button("Valider et passer au Plan d'Action"):
        st.session_state.selected_pivot = choice
        st.session_state.step = 3
        st.rerun()

# --- ÉTAPE 3 : LE SYSTÈME GPS (Plan d'Action) ---
elif st.session_state.step == 3:
    st.subheader("3️⃣ Le Système GPS (Exécution)")
    
    # On détermine quelle idée on traite (Initiale ou Pivot)
    final_concept = st.session_state.initial_idea
    if st.session_state.selected_pivot and "initiale" not in st.session_state.selected_pivot:
        final_concept = f"Version pivotée ({st.session_state.selected_pivot}) basée sur : {st.session_state.initial_idea}"
    
    st.info(f"📍 Création de la feuille de route pour : **{final_concept}**")
    
    if "step3" not in st.session_state.analysis_data:
        if st.button("Générer la feuille de route"):
            with st.spinner("Calcul de l'itinéraire vers le succès..."):
                prompt_gps = f"""
                Agis comme un Stratège Opérationnel.
                Projet validé : "{final_concept}".
                
                Donne-moi le plan GPS :
                1. GOAL (Objectif SMART à 90 jours).
                2. PLAN (3 grandes phases de 30 jours).
                3. STEP (La liste des 3 actions immédiates à faire aujourd'hui).
                
                Sois très concret, pas de blabla.
                """
                res = model.generate_content(prompt_gps)
                st.session_state.analysis_data["step3"] = res.text
                st.rerun()
    
    if "step3" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step3"])
        
        st.divider()
        st.success("🏁 Parcours terminé. N'oubliez pas de sauvegarder votre projet (Menu JSON à gauche).")
        if st.button("Recommencer une nouvelle analyse"):
            st.session_state.step = 1
            st.session_state.analysis_data = {}
            st.session_state.initial_idea = ""
            st.rerun()
