import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🎯", layout="wide")

# Récupération des secrets
try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Vos codes Google Form (Ne pas toucher)
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    # Clients
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-1.5-flash')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- 2. INITIALISATION MÉMOIRE (SESSION STATE) ---
if "user" not in st.session_state: st.session_state.user = None
# On utilise 'current_page' pour savoir où on est. Par défaut : 1
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
    """Crée le lien pré-rempli"""
    if not st.session_state.user: return BASE_FORM_URL
    
    email = st.session_state.user['email']
    idee = st.session_state.project.get("idea", "")
    audit = st.session_state.project.get("analysis", "")[:1500]
    if len(st.session_state.project.get("analysis", "")) > 1500: audit += "..."
    
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
        clean_data.update(data.get("data", {}))
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
                st.session_state.current_page = 2
                st.rerun()
        with c2:
            with st.expander("Modifier et Relancer (1 crédit)"):
                new_txt = st.text_area("Correction", value=st.session_state.project["idea"])
                if st.button("Relancer"):
                    if credits > 0:
                        st.session_state.project["idea"] = new_txt
                        with st.spinner("Analyse V2..."):
                            res = model.generate_content(f"Analyse critique business: {new_txt}").text
                            st.session_state.project["analysis"] = res
                            # Reset suite
                            st.session_state.project["pivots"] = ""
                            st.session_state.project["gps"] = ""
                            consume_credit()
                            st.rerun()
                    else: st.error("Pas de crédit")
    
    # Sinon, formulaire vide
    else:
        if credits > 0:
            idea_input = st.text_area("Votre idée de business :", height=150)
            if st.button("Lancer l'Analyse (1 crédit)", type="primary"):
                if idea_input:
                    st.session_state.project["idea"] = idea_input
                    with st.spinner("Analyse en cours..."):
                        res = model.generate_content(f"Analyse critique business: {idea_input}").text
                        st.session_state.project["analysis"] = res
                        consume_credit()
                        st.session_state.current_page = 2
                        st.rerun()
        else: st.warning("Veuillez recharger vos crédits")

# PAGE 2 : PIVOTS
elif st.session_state.current_page == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    
    # Génération automatique si vide
    if not st.session_state.project["pivots"]:
        with st.spinner("Recherche de pivots..."):
            try:
                res = model.generate_content(f"3 Pivots business pour: {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                st.rerun()
            except: 
                st.error("Erreur IA")
                st.stop()
    
    st.markdown(st.session_state.project["pivots"])
    st.divider()
    
    opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    # Récupération sécurisée index
    current_choice = st.session_state.project.get("choice")
    idx = 0
    if current_choice in opts: idx = opts.index(current_choice)
    
    choice = st.radio("Choix Stratégique :", opts, index=idx)
    
    if st.button("Valider et Voir le Plan ➡️", type="primary"):
        st.session_state.project["choice"] = choice
        st.session_state.project["gps"] = "" # Reset du GPS pour forcer le recalcul
        st.session_state.current_page = 3
        st.rerun()

# PAGE 3 : GPS
elif st.session_state.current_page == 3:
    st.subheader("3️⃣ GPS : Plan d'Action")
    
    final_target = f"{st.session_state.project['idea']} (Option: {st.session_state.project['choice']})"
    st.info(f"Objectif : {final_target}")
    
    # Génération automatique si vide
    if not st.session_state.project["gps"]:
        with st.spinner("Calcul de l'itinéraire..."):
            res = model.generate_content(f"Plan d'action COO pour: {final_target}").text
            st.session_state.project["gps"] = res
            st.rerun()
            
    st.markdown(st.session_state.project["gps"])
    st.divider()
    st.success("Plan Terminé.")
    st.link_button("💎 Réserver Audit (Pré-rempli)", generate_form_link(), type="primary")
