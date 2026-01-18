import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🧠", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] # Lien Lemon Squeezy pour acheter
    LINK_AUDIT = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"Erreur Config : {e}")
    st.stop()

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "step_unlocked" not in st.session_state: st.session_state.step_unlocked = 1
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"
if "project_data" not in st.session_state: 
    st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- 3. FONCTIONS CRITIQUES (ANTI-ABUS) ---

def get_or_create_user(email):
    """
    C'est ICI que se joue la sécurité anti-triche.
    """
    email = str(email).strip().lower()
    
    try:
        # 1. On vérifie si l'email existe DÉJÀ
        # On ne demande pas de code, juste l'email pour l'essai gratuit
        existing = supabase.table("users").select("*").eq("email", email).execute()
        
        if existing.data and len(existing.data) > 0:
            # L'utilisateur existe -> ON LE RETOURNE TEL QUEL (Avec 0 crédit s'il a tout consommé)
            # On ne réinitialise PAS ses crédits.
            return existing.data[0]
        
        else:
            # L'utilisateur est nouveau -> On lui offre les 3 crédits de bienvenue
            new_user_data = {"email": email, "credits": 3}
            # On insère et on récupère la ligne créée
            created = supabase.table("users").insert(new_user_data).execute()
            if created.data:
                return created.data[0]
                
    except Exception as e:
        st.error(f"Erreur Base de Données : {e}")
    return None

def debit_credits(current_user):
    """Débite 1 crédit sur l'email spécifié"""
    email = current_user["email"]
    # On recalcule depuis la session pour être à jour
    current_val = st.session_state.user["credits"]
    new_val = max(0, current_val - 1)
    
    # Update Local
    st.session_state.user["credits"] = new_val
    
    # Update DB
    try:
        supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
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

# --- 4. LOGIN (JUSTE L'EMAIL) ---
if not st.session_state.user:
    st.title("🚀 Stratège IA : Essai Gratuit")
    st.markdown("Entrez votre email pour démarrer. **3 crédits offerts aux nouveaux arrivants.**")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        email_input = st.text_input("Votre Email professionnel :")
    with col2:
        st.write("")
        st.write("")
        if st.button("Démarrer / Continuer"):
            if email_input and "@" in email_input:
                with st.spinner("Vérification du compte..."):
                    # C'est ici qu'on bloque les tricheurs (voir fonction plus haut)
                    u = get_or_create_user(email_input)
                    if u:
                        st.session_state.user = u
                        st.rerun()
            else:
                st.warning("Email invalide.")
    st.stop()

# --- 5. APPLICATION ---
user = st.session_state.user
credits = user.get("credits", 0)

# SIDEBAR
with st.sidebar:
    st.header("Compte")
    st.caption(f"👤 {user['email']}")
    
    if credits > 0:
        st.metric("Crédits restants", credits)
        st.success("✅ Mode Essai Actif")
    else:
        st.metric("Crédits", 0)
        st.error("❌ Essai terminé")
        st.markdown("Pour continuer à utiliser l'IA, vous devez recharger.")
        st.link_button("💳 Acheter des crédits", LINK_RECHARGE, type="primary")
    
    st.divider()
    # Navigation
    opts = ["1. Analyse"]
    if st.session_state.step_unlocked >= 2: opts.append("2. Pivots")
    if st.session_state.step_unlocked >= 3: opts.append("3. GPS")
    
    try: idx = opts.index(st.session_state.current_view)
    except: idx = 0
    nav = st.radio("Menu :", opts, index=idx)
    if nav != st.session_state.current_view:
        st.session_state.current_view = nav
        st.rerun()
        
    st.divider()
    st.download_button("💾 Sauver Dossier", save_json(), "dossier.json")
    up = st.file_uploader("📂 Charger Dossier", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# MAIN
st.title("🧠 Stratège IA")
step_n = int(st.session_state.current_view.split(".")[0])
st.progress(step_n / 3)

# VUE 1
if step_n == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    if st.session_state.project_data["analysis"]:
        st.info(f"Projet : {st.session_state.project_data['idea']}")
        st.markdown(st.session_state.project_data["analysis"])
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Passer à l'étape suivante ➡️"):
                st.session_state.step_unlocked = max(st.session_state.step_unlocked, 2)
                st.session_state.current_view = "2. Pivots"
                st.rerun()
        with c2:
            with st.expander("Relancer (1 crédit)"):
                new_i = st.text_area("Correction:", value=st.session_state.project_data["idea"])
                if st.button("Relancer"):
                    if credits > 0:
                        st.session_state.project_data["idea"] = new_i
                        res = model.generate_content(f"Analyse critique: {new_i}")
                        st.session_state.project_data["analysis"] = res.text
                        st.session_state.project_data["pivots"] = "" # Reset suite
                        st.session_state.project_data["gps"] = ""
                        debit_credits(user)
                        st.rerun()
                    else: st.error("Crédit épuisé. Veuillez acheter.")
    else:
        if credits > 0:
            txt = st.text_area("Votre idée :")
            if st.button("Analyser (1 crédit)"):
                if txt:
                    st.session_state.project_data["idea"] = txt
                    with st.spinner("Analyse..."):
                        res = model.generate_content(f"Analyse critique business de : {txt}")
                        st.session_state.project_data["analysis"] = res.text
                        st.session_state.step_unlocked = 2
                        debit_credits(user)
                        st.rerun()
        else:
            st.warning("⚠️ Vos 3 essais gratuits sont terminés.")
            st.markdown(f"👉 **[Cliquez ici pour obtenir un accès illimité]({LINK_RECHARGE})**")

# VUE 2
elif step_n == 2:
    st.subheader("2️⃣ Pivots")
    if not st.session_state.project_data["pivots"]:
        with st.spinner("Génération..."):
            res = model.generate_content(f"3 Pivots pour {st.session_state.project_data['idea']}")
            st.session_state.project_data["pivots"] = res.text
            st.rerun()
            
    st.markdown(st.session_state.project_data["pivots"])
    st.divider()
    opts_p = ["Initial", "Pivot 1", "Pivot 2", "Pivot 3"]
    try: i = opts_p.index(st.session_state.project_data["choice"])
    except: i = 0
    ch = st.radio("Choix :", opts_p, index=i)
    if st.button("Valider"):
        st.session_state.project_data["choice"] = ch
        st.session_state.project_data["gps"] = ""
        st.session_state.step_unlocked = 3
        st.session_state.current_view = "3. GPS"
        st.rerun()

# VUE 3
elif step_n == 3:
    st.subheader("3️⃣ GPS")
    fin = f"{st.session_state.project_data['idea']} ({st.session_state.project_data['choice']})"
    st.info(f"Cible : {fin}")
    
    if not st.session_state.project_data["gps"]:
        if st.button("Générer Plan"):
            with st.spinner("Calcul..."):
                res = model.generate_content(f"Plan d'action pour {fin}")
                st.session_state.project_data["gps"] = res.text
                st.rerun()
                
    if st.session_state.project_data["gps"]:
        st.markdown(st.session_state.project_data["gps"])
        st.divider()
        st.link_button("💎 Audit Expert", LINK_AUDIT, type="primary")
        if st.button("Nouveau Projet"):
            st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
            st.session_state.step_unlocked = 1
            st.session_state.current_view = "1. Analyse"
            st.rerun()
