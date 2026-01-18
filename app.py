import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid

# --- CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🧠", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] 
    
    # --- VOS CODES FORMULAIRE (Ceux qui marchent) ---
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    # Connexions (Version Standard stable)
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-1.5-flash') # Modèle rapide et stable

except Exception as e:
    st.error(f"❌ Erreur Config : {e}")
    st.stop()

# --- GESTION ÉTAT ---
def init_state():
    if "user" not in st.session_state: st.session_state.user = None
    if "step" not in st.session_state: st.session_state.step = 1
    if "view" not in st.session_state: st.session_state.view = "1. Analyse"
    if "widget_key" not in st.session_state: st.session_state.widget_key = str(uuid.uuid4())
    if "data" not in st.session_state: 
        st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

init_state()

# --- FONCTIONS ---

def force_refresh_credits():
    """Relit la DB pour afficher le vrai solde immédiatement"""
    if st.session_state.user:
        try:
            email = st.session_state.user['email']
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data: st.session_state.user = res.data[0]
        except: pass

def login_secure(email):
    email = str(email).strip().lower()
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        
        new_user = {"email": email, "credits": 3, "access_code": "NOUVEAU"}
        res = supabase.table("users").insert(new_user).execute()
        if res.data: return res.data[0]
    except:
        # Fallback si erreur de création (ex: doublon rapide)
        try:
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data: return res.data[0]
        except: pass
    return None

def debit_credit_atomic():
    """Débite le crédit et met à jour l'affichage AVANT le rerun"""
    if not st.session_state.user: return
    
    email = st.session_state.user['email']
    current = st.session_state.user.get('credits', 0)
    new_val = max(0, current - 1)
    
    # 1. Mise à jour DB
    try:
        supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
    except: pass
    
    # 2. Mise à jour Locale Immédiate
    st.session_state.user['credits'] = new_val
    force_refresh_credits()

def generate_google_link():
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.data.get("idea", "")
    audit = st.session_state.data.get("analysis", "")[:1800]
    if len(st.session_state.data.get("analysis", "")) > 1800: audit += "..."
    
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: audit}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_all():
    """Réinitialise tout pour une nouvelle analyse"""
    st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.step = 1
    st.session_state.view = "1. Analyse"
    st.session_state.widget_key = str(uuid.uuid4())
    st.rerun()

def load_from_json(file):
    try:
        d = json.load(file)
        st.session_state.step = d.get("step", 1)
        clean = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean.update(d.get("data", {}))
        st.session_state.data = clean
        st.session_state.view = "1. Analyse"
        st.session_state.widget_key = str(uuid.uuid4())
        st.success("Chargé !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Fichier invalide")

def save_json():
    return json.dumps({"step": st.session_state.step, "data": st.session_state.data}, indent=4)

# --- INTERFACE ---

# 1. LOGIN
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        st.write("Email Pro :")
        email_in = st.text_input("Email", label_visibility="collapsed")
        if st.button("Connexion", use_container_width=True):
            if "@" in email_in:
                with st.spinner("..."):
                    u = login_secure(email_in)
                    if u:
                        st.session_state.user = u
                        force_refresh_credits()
                        st.rerun()
            else: st.warning("Email invalide")
    st.stop()

# 2. APP
user = st.session_state.user
credits = user.get("credits", 0)

# SIDEBAR
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.caption(f"👤 {user['email']}")
    
    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.error("Épuisé")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")

    st.divider()
    
    st.info("💎 **Expert Humain**")
    st.link_button("Réserver Audit (
