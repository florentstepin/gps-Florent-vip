import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Stratège IA V9", page_icon="🎯", layout="wide")

# ==============================================================================
# 🔐 1. RÉCUPÉRATION DES CLÉS
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    LIEN_RECHARGE = st.secrets["LIEN_RECHARGE"]
    LIEN_ARCHITECTE = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    MODEL_NAME = 'gemini-2.5-pro'
except Exception as e:
    st.error(f"❌ Erreur critique Secrets : {e}")
    st.stop()

# ==============================================================================
# 🔌 2. CONNEXIONS SERVICES
# ==============================================================================
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"❌ Erreur connexion API : {e}")
    st.stop()

# ==============================================================================
# 🧠 3. GESTION DE L'ÉTAT (STATE MACHINE)
# ==============================================================================
# Initialisation des variables de session si elles n'existent pas
if "max_step" not in st.session_state: st.session_state.max_step = 1
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"
if "analysis_data" not in st.session_state: st.session_state.analysis_data = {}
if "selected_pivot" not in st.session_state: st.session_state.selected_pivot = None
if "initial_idea" not in st.session_state: st.session_state.initial_idea = ""

# ==============================================================================
# 🛠️ 4. FONCTIONS UTILITAIRES
# ==============================================================================

def get_user(code):
    """Récupère l'utilisateur via son code d'accès"""
    try:
        code = str(code).strip()
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data: return res.data[0]
    except: pass
    return None

def debit_credit_immediate(user_obj, current):
    """
    Débite le crédit et met à jour l'affichage INSTANTANÉMENT.
    Ne bloque pas l'interface si la DB est lente.
    """
    new_balance = max(0, current - 1)
    
    # 1. Mise à jour visuelle immédiate (Session)
    if "user" in st.session_state:
        st.session_state["user"]["credits"] = new_balance
        
    # 2. Mise à jour Base de Données (En arrière-plan)
    try:
        user_id = user_obj.get("uuid") or user_obj.get("id")
        col = "uuid" if user_obj.get("uuid") else "id"
        if user_id:
            supabase.table("users").update({"credits": new_balance}).eq(col, user_id).execute()
    except Exception as e:
        print(f"Erreur DB (non bloquante) : {e}")
        
    return new_balance

def save_json():
    """Prépare le fichier JSON de sauvegarde"""
    data = {
        "max_step": st.session_state.max_step,
        "idea": st.session_state.initial_idea,
        "analysis": st.session_state.analysis_data,
        "pivot": st.session_state.selected_pivot
    }
    return json.dumps(data, indent=4)

def load_json(uploaded_file):
    """Charge un fichier JSON et restaure l'état complet"""
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.session_state.initial_idea = data.get("idea", "")
            st.session_state.analysis_data = data.get("analysis", {})
            st.session_state.selected_pivot = data.get("pivot", None)
            
            # Restauration du niveau débloqué
            saved_step = data.get("max_step", 1)
            # Sécurité : on vérifie que les données sont bien là
            if "step3" in st.session_state.analysis_data: saved_step = max(saved_step, 3)
            elif "step2" in st.session_state.analysis_data: saved_step = max(saved_step, 2)
            
            st.session_state.max_step = saved_step
            # On remet la vue au début pour lecture
            st.session_state.current_view = "1. Analyse"
            
            st.success("📂 Dossier chargé avec succès !")
            time.sleep(0.5)
            st.rerun()
        except: st.error("Fichier invalide ou corrompu.")

# ==============================================================================
# 🚪 5. ÉCRAN DE CONNEXION
# ==============================================================================
if "user" not in st.session_state:
    qp = st.query_params
    c_url = qp.get("code") or qp.get("access_code")
    if c_url:
        u = get_user(c_url)
        if u:
            st.session_state["user"] = u
            st.rerun()
            
    st.title("🔐 Accès Stratège 2026")
    c_input = st.text_input("Entrez votre code d'accès :")
    if st.button("Valider"):
        u = get_user(c_input)
        if u:
            st.session_state["user"] = u
            st.rerun()
        else: st.error("Code inconnu.")
    st.stop()

# ==============================================================================
# 📱 6. APPLICATION PRINCIPALE
# ==============================================================================

user = st.session_state["user"]
credits = user.get("credits", 0)

# --- SIDEBAR (Navigation & Menu) ---
with st.sidebar:
    st.header("Mon Compte")
    if credits > 0:
        st.metric("Crédits Dispo", credits)
    else:
        st.error("Solde épuisé")
        st.markdown(f"👉 **[Recharger]({LIEN_RECHARGE})**")

    st.divider()
    
    st.markdown("### 📂 Navigation Dossier")
    
    # Construction dynamique du menu selon le niveau débloqué
    options_nav = ["1. Analyse"]
    
    # Si niveau 2 débloqué
    if st.session_state.max_step >= 2 or "step2" in st.session_state.analysis_data:
        options_nav.append("2. Pivots")
        st.session_state.max_step = max(st.session_state.max_step, 2)
        
    # Si niveau 3 débloqué
    if st.session_state.max_step >= 3 or "step3" in st.session_state.analysis_data:
        options_nav.append("3. GPS")
        st.session_state.max_step = max(st.session_state.max_step, 3)
    
    # Trouver l'index actuel pour le widget radio
    try:
        idx = options_nav.index(st.session_state.current_view)
    except:
        idx = 0
        st.session_state.current_view = "1. Analyse"
        
    # Navigation
    choix_nav = st.radio("Aller à :", options_nav, index=idx)
    
    # Mise à jour de la vue si changement
    if choix_nav != st.session_state.current_view:
        st.session_state.current_view = choix_nav
        st.rerun()

    # Extraction du numéro pour la barre de progression
    try:
        step_number = int(st.session_state.current_view.split(".")[0])
    except: step_number = 1

    st.divider()
    st.info("💎 **Expertise Humaine**")
    st.link_button("Réserver un Audit", LIEN_ARCHITECTE, type="primary")
    
    st.divider()
    st.download_button("💾 Sauvegarder JSON", save_json(), "projet_strategie.json", "application/json")
    up = st.file_uploader("📤 Charger JSON", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

# --- CONTENU CENTRAL ---
st.title(f"🧠 Stratège IA")
st.progress(step_number / 3)

# ------------------------------------------------------------------------------
# PHASE 1 : ANALYSE CRITIQUE
# ------------------------------------------------------------------------------
if step_number == 1:
    st.subheader("1️⃣ L'Avocat du Diable")
    
    # CAS A : Déjà analysé
    if "step1" in st.session_state.analysis_data:
        st.info(f"**Projet analysé :** {st.session_state.initial_idea}")
        st.markdown(st.session_state.analysis_data["step1"])
        
        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            # Bouton pour avancer explicitement
            if
