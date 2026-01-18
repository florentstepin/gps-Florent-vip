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
    
    # --- CONFIGURATION FORMULAIRE (Vos codes) ---
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    
    # CONFIGURATION IA BLINDÉE (Anti-Blocage)
    generation_config = {"temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 8192}
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", # Utilisation du modèle le plus stable
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)

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

def login_secure(email):
    email = str(email).strip().lower()
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        
        new_user = {"email": email, "credits": 3, "access_code": "NOUVEAU"}
        res = supabase.table("users").insert(new_user).execute()
        if res.data: return res.data[0]
    except Exception as e:
        # Fallback
        try:
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data: return res.data[0]
        except: st.error(f"Erreur Login: {e}")
    return None

def debit_credit_atomic():
    """Débite VISUELLEMENT et en BASE DE DONNÉES"""
    if not st.session_state.user: return
    
    email = st.session_state.user['email']
    current = st.session_state.user.get('credits', 0)
    
    # 1. Calcul
    new_val = max(0, current - 1)
    
    # 2. Mise à jour Session (Immédiat pour l'utilisateur)
    st.session_state.user['credits'] = new_val
    
    # 3. Mise à jour DB (Arrière-plan)
    try:
        supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
    except Exception as e:
        print(f"Erreur DB update: {e}") # Log console seulement

def generate_content_safe(prompt):
    """Appel IA sécurisé qui ne plante pas l'appli"""
    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text
        else:
            return "⚠️ L'IA a généré une réponse vide (Filtre de sécurité). Essayez de reformuler."
    except Exception as e:
        return f"⚠️ Erreur technique IA : {str(e)}"

def generate_google_link():
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.data.get("idea", "")
    audit = st.session_state.data.get("analysis", "")[:1500]
    if len(st.session_state.data.get("analysis", "")) > 1500: audit += "..."
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: audit}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_all():
    st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.step = 1
    st.session_state.view = "1. Analyse"
    st.session_state.widget_key = str(uuid.uuid4())
    st.rerun()

def load_from_json(file):
    try:
        d = json.load(file)
        st.session_state.step = d.get("step", 1)
        # Fusion pour éviter les clés manquantes
        clean = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean.update(d.get("data", {}))
        st.session_state.data = clean
        st.session_state.view = "1. Analyse"
        st.session_state.widget_key = str(uuid.uuid4())
        st.success("Dossier chargé !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Erreur lecture fichier")

def save_json():
    return json.dumps({"step": st.session_state.step, "data": st.session_state.data}, indent=4)

# --- INTERFACE ---

# LOGIN
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
                        st.rerun()
            else: st.warning("Email invalide")
    st.stop()

# APP
user = st.session_state.user
credits = user.get("credits", 0)

# SIDEBAR
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.caption(f"👤 {user['email']}")
    
    # Affichage Crédits
    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.error("0 Crédits")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")

    st.divider()
    
    # BOUTON AUDIT
    st.info("💎 **Expert Humain**")
    st.link_button("Réserver Audit (Pré-rempli)", generate_google_link(), type="primary", use_container_width=True)

    st.divider()
    
    # NAV
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

# MAIN
st.title("🧠 Stratège IA")
curr_step = int(st.session_state.view.split(".")[0])
st.progress(curr_step / 3)

# VUE 1
if curr_step == 1:
    st.subheader("1️⃣ Analyse")
    
    # Resultat existant
    if st.session_state.data.get("analysis"):
        st.info(f"Sujet : {st.session_state.data.get('idea')}")
        st.markdown(st.session_state.data["analysis"])
        
        if st.button("Suite (Pivots) ➡️", type="primary"):
            st.session_state.step = max(st.session_state.step, 2)
            st.session_state.view = "2. Pivots"
            st.rerun()
            
        with st.expander("Relancer (1 crédit)"):
            n_txt = st.text_area("Correction", value=st.session_state.data.get("idea", ""), key=f"edit_{st.session_state.widget_key}")
            if st.button("Relancer"):
                if credits > 0:
                    st.session_state.data["idea"] = n_txt
                    with st.status("Analyse V2...", expanded=True):
                        # Appel SAFE
                        res = generate_content_safe(f"Analyse critique business: {n_txt}")
                        st.session_state.data["analysis"] = res
                    
                    st.session_state.data["pivots"] = ""
                    st.session_state.data["gps"] = ""
                    debit_credit_atomic() # Débit ICI
                    st.rerun()
                else: st.error("Pas de crédit")

    # Nouveau formulaire
    else:
        if credits > 0:
            u_txt = st.text_area("Votre idée :", height=150, key=f"new_{st.session_state.widget_key}")
            if st.button("Analyser (1 crédit)", type="primary"):
                if u_txt:
                    st.session_state.data["idea"] = u_txt
                    with st.status("Analyse en cours...", expanded=True):
                        # Appel SAFE
                        res = generate_content_safe(f"Analyse critique business: {u_txt}")
                        st.session_state.data["analysis"] = res
                    
                    st.session_state.step = 2
                    debit_credit_atomic() # Débit ICI
                    st.rerun()
        else: st.warning("Rechargez vos crédits")

# VUE 2
elif curr_step == 2:
    st.subheader("2️⃣ Pivots")
    st.caption(f"Projet : {st.session_state.data.get('idea')}")
    
    if not st.session_state.data.get("pivots"):
        with st.status("Recherche Pivots...", expanded=True):
            res = generate_content_safe(f"3 Pivots business pour: {st.session_state.data.get('idea')}")
            st.session_state.data["pivots"] = res
        st.rerun()

    st.markdown(st.session_state.data["pivots"])
    st.divider()
    
    ops = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    try: i = ops.index(st.session_state.data.get("choice"))
    except: i = 0
    c = st.radio("Choix :", ops, index=i)
    if st.button("Valider"):
        st.session_state.data["choice"] = c
        st.session_state.data["gps"] = ""
        st.session_state.step = 3
        st.session_state.view = "3. GPS"
        st.rerun()

# VUE 3
elif curr_step == 3:
    st.subheader("3️⃣ GPS")
    target = f"{st.session_state.data.get('idea')} ({st.session_state.data.get('choice')})"
    st.info(f"Cible : {target}")
    
    if not st.session_state.data.get("gps"):
        with st.status("Calcul GPS...", expanded=True):
            res = generate_content_safe(f"Plan d'action COO pour: {target}")
            st.session_state.data["gps"] = res
        st.rerun()

    st.markdown(st
