import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🎯", layout="wide")

try:
    # Récupération des secrets
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # --- VOS CODES GOOGLE FORM (INTEGRÉS) ---
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    # Connexions
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    
    # --- MOTEUR IA 2026 (RETOUR À LA VERSION QUI MARCHAIT) ---
    model = genai.GenerativeModel('gemini-2.5-pro')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- 2. INITIALISATION MÉMOIRE (SESSION STATE) ---
if "user" not in st.session_state: st.session_state.user = None
# Variable de navigation stricte (1, 2, 3)
if "current_page" not in st.session_state: st.session_state.current_page = 1
# Données du projet
if "project" not in st.session_state:
    st.session_state.project = {
        "idea": "", 
        "analysis": "", 
        "pivots": "", 
        "gps": "", 
        "choice": None
    }

# --- 3. FONCTIONS MÉTIER ---

def login_user(email):
    """Gère la connexion ou création"""
    email = str(email).strip().lower()
    try:
        # Recherche
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        # Création
        new = {"email": email, "credits": 3, "access_code": "NOUVEAU"}
        res = supabase.table("users").insert(new).execute()
        if res.data: return res.data[0]
    except: return None

def consume_credit():
    """Débite 1 crédit et met à jour TOUT de suite"""
    if st.session_state.user:
        email = st.session_state.user['email']
        current = st.session_state.user['credits']
        new_val = max(0, current - 1)
        
        # 1. Update DB
        try: supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
        except: pass
        
        # 2. Update Session
        st.session_state.user['credits'] = new_val

def generate_form_link():
    """Crée le lien pré-rempli avec VOS codes"""
    if not st.session_state.user: return BASE_FORM_URL
    
    email = st.session_state.user['email']
    idee = st.session_state.project.get("idea", "")
    audit = st.session_state.project.get("analysis", "")[:1500]
    if len(st.session_state.project.get("analysis", "")) > 1500: audit += "..."
    
    # Utilisation des codes entry.XXXX extraits de votre lien
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: audit}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    """Remise à zéro"""
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.current_page = 1
    st.rerun()

def load_json(uploaded_file):
    """Charge un fichier JSON"""
    try:
        data = json.load(uploaded_file)
        # On ne charge que les données, pas l'étape, pour éviter les bugs
        clean_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean_data.update(data.get("data", {})) # Merge intelligent
        st.session_state.project = clean_data
        st.session_state.current_page = 1
        st.success("Chargé !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Fichier invalide")

# --- 4. ÉCRAN DE CONNEXION ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        
        email_in = st.text_input("Email Professionnel")
        if st.button("Connexion", use_container_width=True):
            if "@" in email_in:
                u = login_user(email_in)
                if u:
                    st.session_state.user = u
                    st.rerun()
            else: st.warning("Email invalide")
    st.stop()

# --- 5. APPLICATION PRINCIPALE ---
user = st.session_state.user
credits = user.get("credits", 0)

# --- SIDEBAR (Barre latérale) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.write(f"👤 **{user['email']}**")
    
    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.error("0 Crédits")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")
    
    st.divider()
    st.info("💎 **Expert Humain**")
    st.link_button("Réserver Audit (Pré-rempli)", generate_form_link(), type="primary", use_container_width=True)
    
    st.divider()
    # Navigation Manuelle
    st.write("### 🧭 Navigation")
    if st.button("1. Analyse"): 
        st.session_state.current_page = 1
        st.rerun()
    if st.session_state.project["analysis"] and st.button("2. Pivots"): 
        st.session_state.current_page = 2
        st.rerun()
    if st.session_state.project["pivots"] and st.button("3. GPS"): 
        st.session_state.current_page = 3
        st.rerun()
        
    st.divider()
    if st.button("✨ Nouvelle Analyse"): reset_project()
    
    # Sauvegarde
    json_str = json.dumps({"data": st.session_state.project}, indent=4)
    st.download_button("💾 Sauver JSON", json_str, "projet.json")
    
    # Chargement
    up = st.file_uploader("📂 Charger JSON", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# --- CONTENU CENTRAL ---
st.title("🧠 Stratège IA")
st.progress(st.session_state.current_page / 3)

# PAGE 1 : ANALYSE
if st.session_state.current_page == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    
    # Si on a déjà une analyse
    if st.session_state.project["analysis"]:
        st.info(f"Sujet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Aller aux Pivots ➡️", type="primary"):
                st.
