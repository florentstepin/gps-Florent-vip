import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🎯", layout="wide")

try:
    # Récupération des secrets
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] 
    LINK_AUDIT = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    
    # Connexions
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"❌ Erreur de configuration : {e}")
    st.stop()

# --- SESSION ---
if "user" not in st.session_state: st.session_state.user = None
if "step_unlocked" not in st.session_state: st.session_state.step_unlocked = 1
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"
if "project_data" not in st.session_state: 
    st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- FONCTIONS ---

def verifier_et_connecter(email_saisi):
    """
    Vérifie si l'email existe DÉJÀ dans Supabase.
    - Si OUI : Connecte l'utilisateur (pas de cadeau).
    - Si NON : Crée le compte avec 3 crédits.
    """
    # 1. Nettoyage de l'email (minuscules, sans espaces)
    email_propre = str(email_saisi).strip().lower()
    
    # 2. Recherche d'antériorité
    try:
        # On cherche une ligne où la colonne 'email' est égale à notre variable 'email_propre'
        recherche = supabase.table("users").select("*").eq("email", email_propre).execute()
        
        if recherche.data and len(recherche.data) > 0:
            # TROUVÉ ! On retourne le compte existant
            return recherche.data[0]
            
        else:
            # PAS TROUVÉ -> C'est un nouveau
            # On prépare les données CORRECTEMENT cette fois
            nouveau_compte = {
                "email": email_propre,          # <-- La variable, pas le texte 'email'
                "credits": 3,                   # Le cadeau de bienvenue
                "access_code": "WAITING_MAKE"   # Le signal pour Make
            }
            
            creation = supabase.table("users").insert(nouveau_compte).execute()
            if creation.data:
                return creation.data[0]
                
    except Exception as e:
        st.error(f"Erreur de base de données : {e}")
        
    return None

def debiter_1_credit(utilisateur):
    """Débite 1 crédit et met à jour l'affichage"""
    email_cible = utilisateur["email"]
    
    # Mise à jour locale (Session)
    credits_actuels = st.session_state.user.get("credits", 0)
    nouveau_solde = max(0, credits_actuels - 1)
    st.session_state.user["credits"] = nouveau_solde
    
    # Mise à jour Supabase
    try:
        supabase.table("users").update({"credits": nouveau_solde}).eq("email", email_cible).execute()
    except: pass

def save_json():
    return json.dumps({"step": st.session_state.step_unlocked, "data": st.session_state.project_data})

def load_json(f):
    try:
        d = json.load(f)
        st.session_state.step_unlocked = d.get("step", 1)
        st.session_state.project_data = d.get("data", {})
        st.session_state.current_view = "1. Analyse"
        st.rerun()
    except: pass

# --- LOGIN ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    st.write("Entrez votre email professionnel pour accéder à l'outil.")
    
    c1, c2 = st.columns([3, 1])
    with c1:
        # Champ de saisie
        saisie_email = st.text_input("Votre Email :", placeholder="exemple@gmail.com")
    with c2:
        st.write("")
        st.write("")
        if st.button("Accéder", use_container_width=True):
            if saisie_email and "@" in saisie_email:
                with st.spinner("Vérification..."):
                    # On appelle la fonction avec ce que l'utilisateur a tapé
                    compte = verifier_et_connecter(saisie_email)
                    
                    if compte:
                        st.session_state.user = compte
                        st.rerun()
            else:
                st.warning("Email invalide.")
    st.stop()

# --- APPLICATION ---
user = st.session_state.user
credits = user.get("credits", 0)

with st.sidebar:
    st.header("Compte")
    # Affiche l'email pour être sûr que ce n'est pas le mot "email"
    st.code(user.get('email')) 
    
    if credits > 0:
        st.metric("Crédits", credits)
        st.success("Actif")
    else:
        st.metric("Crédits", 0)
        st.error("Terminé")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")
    
    st.divider()
    # Menu
    opts = ["1. Analyse"]
    if st.session_state.step_unlocked >= 2: opts.append("2. Pivots")
    if st.session_state.step_unlocked >= 3: opts.append("3. GPS")
    
    try: idx = opts.index(st.session_state.current_view)
    except: idx = 0
    nav = st.radio("Menu", opts, index=idx)
    
    if nav != st.session_state.current_view:
        st.session_state.current_view = nav
        st.rerun()
        
    st.divider()
    st.download_button("Sauver", save_json(), "projet.json")
    up = st.file_uploader("Charger", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# --- CONTENU ---
st.title("🧠 Stratège IA")
step_n = int(st.session_state.current_view.split(".")[0])
st.progress(step_n / 3)

# PHASE 1
if step_n == 1:
    st.subheader("1️⃣ Analyse")
    if st.session_state.project_data["analysis"]:
        st.info(f"Sujet : {st.session_state.project_data['idea']}")
        st.markdown(st.session_state.project_data["analysis"])
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Suite ➡️"):
                st.session_state.step_unlocked = max(st.session_state.step_unlocked, 2)
                st.session_state.current_view = "2. Pivots"
                st.rerun()
        with c2:
            with st.expander("Relancer (1 crédit)"):
                n = st.text_area("Edit:", value=st.session_state.project_data["idea"])
                if st.button("Go"):
                    if credits > 0:
                        st.session_state.project_data["idea"] = n
                        st.session_state.project_data["analysis"] = model.generate_content(f"Analyse: {n}").text
                        st.session_state.project_data["pivots"] = ""
                        st.session_state.project_data["gps"] = ""
                        debiter_1_credit(user)
                        st.rerun()
                    else: st.error("Solde nul")
    else:
        if credits > 0:
            t = st.text_area("Votre idée :")
            if st.button("Analyser (1 crédit)"):
                if t:
                    st.session_state.project_data["idea"] = t
                    with st.spinner("..."):
                        st.session_state.project_data["analysis"] = model.generate_content(f"Analyse: {t}").text
                        st.session_state.step_unlocked = 2
                        debiter_1_credit(user)
                        st.rerun()
        else: st.warning("Rechargez vos crédits.")

# PHASE 2
elif step_n == 2:
    st.subheader("2️⃣ Pivots")
    if not st.session_state.project_data["pivots"]:
        with st.spinner("..."):
            st.session_state.project_data["pivots"] = model.generate_content(f"3 Pivots pour: {st.session_state.project_data['idea']}").text
            st.rerun()
    st.markdown(st.session_state.project_data["pivots"])
    st.divider()
    ops = ["Initial", "Pivot 1", "Pivot 2", "Pivot 3"]
    try: i = ops.index(st.session_state.project_data["choice"])
    except: i = 0
    c = st.radio("Choix :", ops, index=i)
    if st.button("Valider"):
        st.session_state.project_data["choice"] = c
        st.session_state.project_data["gps"] = ""
        st.session_state.step_unlocked = 3
        st.session_state.current_view = "3. GPS"
        st.rerun()

# PHASE 3
elif step_n == 3:
    st.subheader("3️⃣ GPS")
    f_sub = f"{st.session_state.project_data['idea']} ({st.session_state.project_data['choice']})"
    st.info(f"Cible: {f_sub}")
    if not st.session_state.project_data["gps"]:
        if st.button("Calculer Plan"):
            with st.spinner("..."):
                st.session_state.project_data["gps"] = model.generate_content(f"Plan d'action: {f_sub}").text
                st.rerun()
    if st.session_state.project_data["gps"]:
        st.markdown(st.session_state.project_data["gps"])
        st.divider()
        st.link_button("💎 Audit", LINK_AUDIT, type="primary")
        if st.button("Nouveau"):
            st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
            st.session_state.step_unlocked = 1
            st.session_state.current_view = "1. Analyse"
            st.rerun()
