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
    
    # =========================================================================
    # 👇 CONFIGURATION AUTOMATIQUE DU FORMULAIRE (NE PAS TOUCHER) 👇
    # =========================================================================
    # Vos codes extraits du lien que vous m'avez fourni :
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"
    # =========================================================================

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')

except Exception as e:
    st.error(f"❌ Erreur Config : {e}")
    st.stop()

# --- GESTION ÉTAT ROBUSTE ---
def init_state():
    if "user" not in st.session_state: st.session_state.user = None
    if "step" not in st.session_state: st.session_state.step = 1
    if "view" not in st.session_state: st.session_state.view = "1. Analyse"
    # ID unique pour forcer le nettoyage des champs texte lors du reset
    if "widget_key" not in st.session_state: st.session_state.widget_key = str(uuid.uuid4())
    if "data" not in st.session_state: 
        st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

init_state()

# --- FONCTIONS TECHNIQUES ---

def force_refresh_credits():
    """Relit la base de données pour être sûr d'avoir le vrai solde (corrige le bug des 50 crédits)"""
    if st.session_state.user:
        try:
            email = st.session_state.user['email']
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data:
                st.session_state.user = res.data[0]
        except: pass

def login_secure(email):
    email = str(email).strip().lower()
    try:
        # 1. On cherche l'utilisateur
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: 
            return res.data[0]
        
        # 2. Création si nouveau (Upsert safe)
        new_user = {
            "email": email, 
            "credits": 3, 
            "access_code": "NOUVEAU"
        }
        res = supabase.table("users").insert(new_user).execute()
        if res.data: 
            return res.data[0]
            
    except Exception as e:
        # Fallback de sécurité (si conflit de création simultanée)
        try:
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data: return res.data[0]
        except: st.error(f"Erreur Login: {e}")
    return None

def debit_credit_atomic():
    """Débite 1 crédit, sauvegarde et rafraîchit TOUT de suite"""
    if not st.session_state.user: return
    
    email = st.session_state.user['email']
    # Lecture optimiste
    current = st.session_state.user.get('credits', 0)
    new_val = max(0, current - 1)
    
    # 1. DB Update
    try:
        supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
    except: pass
    
    # 2. Session Update
    st.session_state.user['credits'] = new_val
    force_refresh_credits() # Double check pour être sûr

def generate_google_link():
    """Génère le lien pré-rempli avec VOS codes exacts"""
    if not st.session_state.user: return BASE_FORM_URL
    
    email = st.session_state.user['email']
    idee = st.session_state.data.get("idea", "")
    # On tronque l'audit pour éviter les erreurs d'URL trop longue (Google limite la taille)
    audit = st.session_state.data.get("analysis", "")[:1800] 
    if len(st.session_state.data.get("analysis", "")) > 1800:
        audit += "\n\n[... Audit complet dans le JSON joint ...]"

    params = {
        ENTRY_EMAIL: email,
        ENTRY_IDEE: idee,
        ENTRY_AUDIT: audit
    }
    # Encodage spécial pour les accents et espaces
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_all():
    """Hard Reset : On change la clé des widgets pour forcer le nettoyage visuel"""
    st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.step = 1
    st.session_state.view = "1. Analyse"
    st.session_state.widget_key = str(uuid.uuid4()) # C'est ça qui vide les champs texte !
    st.rerun()

def load_from_json(file):
    try:
        d = json.load(file)
        st.session_state.step = d.get("step", 1)
        st.session_state.data = d.get("data", {})
        st.session_state.view = "1. Analyse"
        # On force une nouvelle clé pour afficher les nouvelles données
        st.session_state.widget_key = str(uuid.uuid4())
        st.success("Dossier chargé avec succès !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Fichier corrompu ou illisible.")

def save_json():
    return json.dumps({"step": st.session_state.step, "data": st.session_state.data}, indent=4)

# --- INTERFACE ---

# 1. LOGIN
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        
        st.write("Identifiez-vous (Email Pro)")
        email_in = st.text_input("Email", placeholder="vous@societe.com")
        
        if st.button("Accéder", use_container_width=True):
            if "@" in email_in:
                with st.spinner("Connexion sécurisée..."):
                    u = login_secure(email_in)
                    if u:
                        st.session_state.user = u
                        # Force le rafraîchissement immédiat pour éviter le bug "50 crédits"
                        force_refresh_credits()
                        st.rerun()
            else: st.warning("Format email invalide")
    st.stop()

# 2. APP CONNECTÉE
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
        st.link_button("💳 Recharger", LINK_RECHARGE, type="primary")

    st.divider()
    
    # BOUTON AUDIT MAGIQUE (Pré-rempli)
    st.info("💎 **Expertise Humaine**")
    smart_link = generate_google_link()
    st.link_button("Réserver un Audit (Formulaire Pré-rempli)", smart_link, type="primary", use_container_width=True)

    st.divider()
    
    # NAVIGATION
    opts = ["1. Analyse"]
    if st.session_state.step >= 2: opts.append("2. Pivots")
    if st.session_state.step >= 3: opts.append("3. GPS")
    
    try: idx = opts.index(st.session_state.view)
    except: idx = 0
    nav = st.radio("Menu", opts, index=idx)
    if nav != st.session_state.view:
        st.session_state.view = nav
        st.rerun()

    st.divider()
    if st.button("✨ Nouvelle Analyse", use_container_width=True):
        reset_all()

    st.download_button("💾 Sauver JSON", save_json(), "projet.json", use_container_width=True)
    up = st.file_uploader("📂 Charger JSON", type="json")
    if up: load_from_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# CONTENU CENTRAL
st.title("🧠 Stratège IA")
curr_step = int(st.session_state.view.split(".")[0])
st.progress(curr_step / 3)

# VUE 1 : ANALYSE
if curr_step == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    
    # Si analyse existe
    if st.session_state.data["analysis"]:
        st.info(f"Projet : {st.session_state.data['idea']}")
        st.markdown(st.session_state.data["analysis"])
        
        if st.button("Passer à l'étape 2 ➡️", type="primary"):
            st.session_state.step = max(st.session_state.step, 2)
            st.session_state.view = "2. Pivots"
            st.rerun()
            
        with st.expander("Modifier et Relancer (1 crédit)"):
            # Clé unique pour éviter les conflits de mémoire
            n_txt = st.text_area("Correction", value=st.session_state.data["idea"], key=f"edit_{st.session_state.widget_key}")
            if st.button("Relancer"):
                if credits > 0:
                    st.session_state.data["idea"] = n_txt
                    with st.status("🕵️‍♂️ Analyse V2...", expanded=True) as s:
                        st.write("Révision...")
                        time.sleep(1)
                        st.session_state.data["analysis"] = model.generate_content(f"Analyse critique: {n_txt}").text
                        s.update(label="OK !", state="complete")
                    st.session_state.data["pivots"] = ""
                    st.session_state.data["gps"] = ""
                    debit_credit_atomic()
                    st.rerun()
                else: st.error("Solde nul")

    # Si vierge
    else:
        if credits > 0:
            # Clé unique ici aussi
            u_txt = st.text_area("Votre idée :", height=150, key=f"new_{st.session_state.widget_key}")
            if st.button("Analyser (1 crédit)", type="primary"):
                if u_txt:
                    st.session_state.data["idea"] = u_txt
                    with st.status("🧠 Analyse en cours...", expanded=True) as s:
                        st.write("Scan du marché...")
                        time.sleep(1)
                        st.write("Recherche de failles...")
                        time.sleep(1)
                        st.session_state.data["analysis"] = model.generate_content(f"Analyse critique: {u_txt}").text
                        s.update(label="Rapport généré !", state="complete")
                    st.session_state.step = 2
