import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid 
import re   
import requests 

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- 2. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
if "user_note" not in st.session_state: st.session_state.user_note = "" 

# --- 3. FONCTIONS ---
def login_user(email):
    email = str(email).strip().lower()
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        unique_code = str(uuid.uuid4())
        new = {"email": email, "credits": 2, "access_code": unique_code}        
        res = supabase.table("users").insert(new).execute()
        if res.data: return res.data[0]
    except Exception as e:
        st.error(f"Erreur Login: {e}")
    return None

def consume_credit():
    if st.session_state.user:
        email = st.session_state.user['email']
        new_val = max(0, st.session_state.user['credits'] - 1)
        try: 
            supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
            st.session_state.user['credits'] = new_val
        except: pass

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
    raw_audit = st.session_state.project.get("analysis", "")
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: f"ID de session V2 - Audit complet à joindre en PDF."}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.user_note = ""
    st.rerun()

def load_json(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.project.update(data.get("data", {}))
        st.success("Dossier chargé ! Cliquez sur l'onglet correspondant.")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Erreur JSON : {e}")

# --- 4. AUTHENTIFICATION ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        st.title("🚀 Stratège IA")
        email_in = st.text_input("Email Professionnel")
        if st.button("Connexion", use_container_width=True):
            if "@" in email_in:
                u = login_user(email_in)
                if u: 
                    st.session_state.user = u
                    st.rerun()
            else: st.warning("Email invalide")
    st.stop()

user = st.session_state.user
credits = user.get("credits", 0)

# --- 5. SIDEBAR V2 ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    
    st.markdown(f"""
    <div style='background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>
        <div style='font-size: 0.8em; opacity: 0.7;'>Utilisateur :</div>
        <div style='font-weight: bold; font-size: 0.9em;'>{user['email']}</div>
        <div style='margin-top: 10px; font-weight: bold; color: #7f5af0; font-size: 1.2em;'>🎯 {credits} Crédits</div>
    </div>
    """, unsafe_allow_html=True)

    with st.popover("❓ Guide de Survie", use_container_width=True):
        st.markdown("""
        **Conseils pour une analyse réussie :**
        * **Détails** : Donnez 5-10 lignes de contexte (Cible, but, ressources). [cite: 525, 621]
        * **Écran** : Ne laissez pas votre mobile se mettre en veille pendant l'analyse. [cite: 634]
        * **VPN** : Coupez votre VPN si l'application semble bloquée. [cite: 433, 451]
        * **Sauvegarde** : Exportez votre JSON après chaque étape ! [cite: 316, 559]
        """)

    st.link_button("⚡ Recharger mes crédits", LINK_RECHARGE, type="primary", use_container_width=True)
    
    st.divider()
    
    with st.expander("📂 Sauvegarde & Import", expanded=False):
        json_str = json.dumps({"data": st.session_state.project}, indent=4)
        st.download_button("💾 Sauver JSON", json_str, "projet_ia.json", use_container_width=True, help="Sauvegarde locale gratuite")
        up = st.file_uploader("Charger JSON", type="json")
        if up: load_json(up)
        if st.button("✨ Nouvelle Analyse", use_container_width=True): reset_project()

    with st.expander("💎 Expert Humain", expanded=False):
        st.session_state.user_note = st.text_area("Note pour l'expert", value=st.session_state.user_note, placeholder="Précisez votre budget, vos outils...") [cite: 66, 277]
        st.link_button("Réserver Audit", generate_form_link(), use_container_width=True)

    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 6. CORPS DE L'APPLICATION ---
st.title("🧠 Stratège IA")

# Onboarding Message
if not st.session_state.project["analysis"]:
    st.info("👋 **Bienvenue !** Transformez votre idée en plan d'action en 3 étapes : **1. Analyse** (Évaluer les risques) → **2. Pivots** (Choisir l'angle) → **3. GPS** (Exécuter).") [cite: 19, 486]

# Système d'onglets
tab1, tab2, tab3 = st.tabs(["🔍 1. Analyse Crash-Test", "💡 2. Pivots Stratégiques", "🗺️ 3. Plan d'Action GPS"]) [cite: 43, 683, 734]

with tab1:
    if st.session_state.project["analysis"]:
        st.success(f"Projet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
        if st.button("Passer aux Pivots ➡️", type="primary"):
            st.info("Cliquez sur l'onglet '2. Pivots Stratégiques' en haut de l'écran.")
    else:
        idea_input = st.text_area("Décrivez votre projet (3-5 phrases pour un meilleur résultat) :", height=150, placeholder="Ex: Je veux lancer une formation pour...") [cite: 23, 721]
        if st.button("Lancer l'Analyse (1 crédit)", type="primary"):
            if idea_input and credits > 0:
                with st.status("🕵️‍♂️ L'Avocat du Diable analyse votre idée...", expanded=True):
                    try:
                        res = model.generate_content(f"Analyse critique business: {idea_input}").text
                        st.session_state.project["idea"] = idea_input
                        st.session_state.project["analysis"] = res
                        consume_credit()
                        st.rerun()
                    except Exception as e: st.error(f"Erreur : {e}")
            elif credits <= 0: st.error("Crédits insuffisants.")
            else: st.warning("Veuillez saisir votre idée.")

with tab2:
    if not st.session_state.project["analysis"]:
        st.warning("⚠️ Veuillez d'abord compléter l'étape 1 (Analyse).")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
        choice = st.radio("Sur quel angle voulez-vous construire votre GPS ?", opts)
        if st.button("Valider et Créer le GPS 🗺️", type="primary"):
            st.session_state.project["choice"] = choice
            st.session_state.project["gps"] = ""
            st.info("Direction l'onglet '3. Plan d'Action GPS' !")
    else:
        if st.button("Générer les 3 Pivots Stratégiques (1 crédit)", type="primary"):
            with st.status("💡 Brainstorming des angles d'attaque...", expanded=True):
                try:
                    res = model.generate_content(f"3 Pivots business pour: {st.session_state.project['idea']}").text
                    st.session_state.project["pivots"] = res
                    consume_credit()
                    st.rerun()
                except Exception as e: st.error(f"Erreur : {e}")

with tab3:
    if not st.session_state.project["choice"]:
        st.warning("⚠️ Veuillez choisir un pivot à l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.success("✅ Votre feuille de route est prête. N'oubliez pas d'exporter le JSON dans la sidebar.")
    else:
        tgt = f"{st.session_state.project['idea']} (Angle : {st.session_state.project['choice']})"
        if st.button("Générer le Plan GPS (1 crédit)", type="primary"):
            with st.status("🗺️ Séquençage des étapes opérationnelles...", expanded=True):
                try:
                    res = model.generate_content(f"Plan d'action opérationnel (GPS) détaillé pour: {tgt}").text
                    st.session_state.project["gps"] = res
                    consume_credit()
                    st.rerun()
                except Exception as e: st.error(f"Erreur : {e}")
