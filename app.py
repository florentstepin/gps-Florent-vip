import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid 
import re   

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🎯", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Vos codes Google Form
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    
    # MOTEUR (Thinking)
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-1219')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- 2. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_page" not in st.session_state: st.session_state.current_page = 1
if "user_note" not in st.session_state: st.session_state.user_note = ""
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# Gestion du lien de retour (?access_code=...) pour les emails
qp = st.query_params
if "access_code" in qp:
    code = qp["access_code"]
    try:
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data:
            st.session_state.user = res.data[0]
            st.success("Connexion réussie !")
            time.sleep(1)
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")

# --- 3. FONCTIONS CRITIQUES (RESTAURÉES) ---

def login_user(email_input):
    """
    Version stable. 
    Vérifie l'existence. Si non, crée.
    Retourne l'utilisateur.
    """
    # Nettoyage impératif pour éviter les bugs
    clean_email = str(email_input).strip().lower()
    
    try:
        # 1. D'ABORD ON VÉRIFIE SI L'UTILISATEUR EXISTE (Sauve les anciens comptes)
        res = supabase.table("users").select("*").eq("email", clean_email).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        
        # 2. SINON, ON CRÉE LE NOUVEAU
        unique_code = str(uuid.uuid4())
        
        # Objet de création propre
        new_user_data = {
            "email": clean_email,  # Variable propre, pas de confusion possible
            "credits": 2, 
            "access_code": unique_code 
        }
        
        insert_res = supabase.table("users").insert(new_user_data).execute()
        if insert_res.data: 
            return insert_res.data[0]
            
    except Exception as e:
        st.error(f"Erreur Login/DB : {e}")
        # Tentative ultime de récupération si l'insert a échoué mais que le user existe
        try:
            res = supabase.table("users").select("*").eq("email", clean_email).execute()
            if res.data: return res.data[0]
        except: pass
        
    return None

def consume_credit():
    if st.session_state.user:
        email = st.session_state.user['email']
        new_val = max(0, st.session_state.user['credits'] - 1)
        try: supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
        except: pass
        st.session_state.user['credits'] = new_val

def clean_markdown(text):
    if not text: return ""
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'^\s*[\-\*]\s+', '- ', text, flags=re.MULTILINE)
    return text.strip()

def generate_form_link():
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.project.get("idea", "")
    note_client = st.session_state.user_note
    raw_audit = st.session_state.project.get("analysis", "")
    clean_audit = clean_markdown(raw_audit)
    
    final_content = f"--- PROJET ---\n{idee}\n\n"
    if note_client: final_content += f"--- NOTE ---\n{note_client}\n\n"
    final_content += f"--- AUDIT ---\n{clean_audit[:1200]}..."
    
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: final_content}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.user_note = ""
    st.session_state.current_page = 1
    st.rerun()

def load_json(uploaded_file):
    try:
        uploaded_file.seek(0)
        data = json.load(uploaded_file)
        clean_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean_data.update(data.get("data", {}))
        st.session_state.project = clean_data
        st.session_state.current_page = 1
        st.session_state.last_loaded_signature = f"{uploaded_file.name}_{uploaded_file.size}"
        st.success("Chargé !")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        st.error(f"Erreur JSON : {e}")

# --- 4. ÉCRAN DE CONNEXION (SIMPLIFIÉ) ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        
        st.write("Connexion / Inscription")
        email_saisie = st.text_input("Email Professionnel")
        
        if st.button("Entrer", use_container_width=True):
            if "@" in email_saisie:
                # Appel direct et simple
                user_found = login_user(email_saisie)
                
                if user_found:
                    st.session_state.user = user_found
                    st.success("Connexion...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Erreur de connexion. Réessayez.")
            else:
                st.warning("Format d'email invalide")
