import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
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

# --- 2. INITIALISATION & PARRAINAGE ---
if "user" not in st.session_state: st.session_state.user = None
if "current_page" not in st.session_state: st.session_state.current_page = 1
if "user_note" not in st.session_state: st.session_state.user_note = ""
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# Gestion des paramètres URL (Parrainage & Retour Email)
# On capture le parrain AVANT tout le reste
qp = st.query_params
if "ref" in qp:
    st.session_state["referral_code"] = qp["ref"]

# --- 3. FONCTIONS ---

def get_or_create_user(email):
    """Vérifie l'utilisateur dans la DB publique après le clic email"""
    email = str(email).strip().lower()
    try:
        # 1. On cherche l'utilisateur
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data:
            return res.data[0] # Il existe déjà
        
        # 2. Il n'existe pas : CRÉATION (C'est ici qu'on applique le parrainage)
        new_credits = 2 # Crédits de base
        
        # Si un code parrain est en mémoire
        if "referral_code" in st.session_state:
            parrain_email = st.session_state["referral_code"]
            # On crédite le PARRAIN (+2 crédits)
            try:
                # Récupère crédits actuels du parrain
                p_data = supabase.table("users").select("credits").eq("email", parrain_email).execute()
                if p_data.data:
                    current_p_credits = p_data.data[0]['credits']
                    supabase.table("users").update({"credits": current_p_credits + 2}).eq("email", parrain_email).execute()
            except:
                pass # Ne pas bloquer si erreur parrain
        
        # On crée le FILLEUL
        new_user = {
            "email": email, 
            "credits": new_credits
        }
        res = supabase.table("users").insert(new_user).execute()
        if res.data: return res.data[0]

    except Exception as e:
        st.error(f"Erreur DB: {e}")
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

# --- 4. SYSTEME DE LOGIN (Magic Link) ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        
        # A. Gestion du RETOUR EMAIL (Token dans l'URL)
        # Streamlit capture le token automatiquement dans l'URL après le clic email
        # On tente de récupérer la session
        session = supabase.auth.get_session()
        
        if session:
            # L'utilisateur a cliqué sur le lien email !
            user_email = session.user.email
            # On synchronise avec notre table 'users' publique pour les crédits
            db_user = get_or_create_user(user_email)
            if db_user:
                st.session_state.user = db_user
                st.success("Connexion réussie !")
                time.sleep(1)
                st.rerun()
        
        # B. Formulaire de Connexion Classique
        st.write("Connectez-vous pour accéder à vos crédits.")
        email_in = st.text_input("Votre Email")
        
        if st.button("Recevoir mon lien magique ✨", use_container_width=True):
            if "@" in email_in:
                try:
                    # C'EST ICI LA CLÉ : On utilise l'auth Supabase, pas l'insert direct
                    # Le redirect_to est crucial pour revenir sur l'app
                    APP_URL = "https://stratege-ia.streamlit.app" # REMPLACER PAR VOTRE URL EXACTE
                    res = supabase.auth.sign_in_with_otp({
                        "email": email_in,
                        "options": {"email_redirect_to": APP_URL}
                    })
                    st.success("Checkez vos emails ! Un lien magique arrive.")
                    st.info("Pensez à vérifier les Spams.")
                except Exception as e:
                    st.error(f"Erreur envoi : {e}")
            else:
                st.warning("Email invalide")
                
    st.stop()

# --- 5. APPLICATION PRINCIPALE ---
# (Le reste du code reste identique, l'utilisateur est connecté)
user = st.session_state.user
credits = user.get("credits", 0)

with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.write(f"👤 **{user['email']}**")
    
    # --- AJOUT PARRAINAGE ---
    st.divider()
    my_ref_link = f"https://stratege-ia.streamlit.app?ref={user['email']}"
    st.write("🎁 **Gagnez des crédits !**")
    st.write("Invitez un ami : vous recevez +2 crédits chacun.")
    st.text_input("Votre lien parrain :", value=my_ref_link, disabled=True)
    # ------------------------

    if credits > 0: st.metric("Crédits", credits)
    else: 
        st.error("0 Crédits")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")
    
    st.divider()
    # ... (Le reste de votre sidebar identique)
    # Copiez-collez la suite de votre code original ici à partir de "st.info('💎 **Expert Humain**')"
    # Jusqu'à la fin du fichier.
    
    # ... Pour éviter de rendre la réponse trop longue, je vous laisse recoller la partie "APP" (Ligne 155 à la fin)
    # car elle n'avait pas d'erreur.
    
    # NOTE IMPORTANTE :
    # Assurez-vous juste de bien indenter le reste du code sous le "else" ou hors du "if not user".
    # Dans ma structure ci-dessus, le "st.stop()" ligne 185 arrête le script si pas connecté.
    # Donc tout le code de l'app (Page 1, 2, 3) peut être collé directement à la suite sans indentation supplémentaire.
