import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid 

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    </style>
""", unsafe_allow_html=True)

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"Erreur Config: {e}"); st.stop()

# --- 2. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- 3. FONCTIONS ---
def login_user(email):
    email = str(email).strip().lower()
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data: return res.data[0]
    new = {"email": email, "credits": 2, "access_code": str(uuid.uuid4())}        
    res = supabase.table("users").insert(new).execute()
    return res.data[0] if res.data else None

def consume_credit():
    if st.session_state.user:
        new_val = max(0, st.session_state.user['credits'] - 1)
        supabase.table("users").update({"credits": new_val}).eq("email", st.session_state.user['email']).execute()
        st.session_state.user['credits'] = new_val

# --- 4. SIDEBAR AVEC GUIDE ENRICHI ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.markdown(f"**👤 {st.session_state.user['email']}**")
        st.info(f"🎯 **{st.session_state.user['credits']} Crédits**")
        
        # --- LE NOUVEAU GUIDE INTERMÉDIAIRE ---
        with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
            st.markdown("### 🧭 Réussir votre stratégie")
            t_tech, t_meth, t_sauve = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
            
            with t_tech:
                st.markdown("""
                **Éviter les coupures :**
                * **⚠️ PAS DE F5** : N'actualisez jamais la page pendant une analyse, cela couperait la session et perdrait votre crédit.
                * **Écran mobile** : Désactivez la mise en veille auto. Si l'écran s'éteint, la connexion avec l'IA peut s'interrompre.
                * **VPN** : Coupez votre VPN si l'application semble "mouliner" sans fin.
                """)
            
            with t_meth:
                st.markdown("""
                **Résultat de haute qualité :**
                * **Le Carburant** : L'IA ne devine pas. Donnez 5 à 10 lignes sur votre cible et vos ressources réelles.
                * **Zéro Généralités** : Plus vous êtes spécifique (ex: 'agents immo à Lyon' plutôt que 'pros'), plus le GPS sera actionnable.
                """)
                
            with t_sauve:
                st.markdown("""
                **Ne rien perdre :**
                * **Export JSON** : C'est votre "disquette". Téléchargez-le après chaque étape validée.
                * **Gratuité** : Recharger un JSON ne consomme **aucun crédit** et restaure tout instantanément.
                * **Export PDF** : (Arrive demain matin !)
                """)
        
        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()
        with st.expander("📂 Gestion de Session", expanded=False):
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Sauver JSON", json_str, "projet.json", use_container_width=True)
            if st.button("✨ Nouveau Projet", use_container_width=True):
                st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
                st.rerun()

# --- 5. CORPS DE L'APPLI ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    email = st.text_input("Votre Email Professionnel")
    if st.button("Connexion"):
        st.session_state.user = login_user(email); st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")
tab1, tab2, tab3 = st.tabs(["🔍 1. Analyse Crash-Test", "💡 2. Pivots Stratégiques", "🗺️ 3. Plan d'Action GPS"])

with tab1:
    if st.session_state.project["analysis"]:
        st.success(f"📌 Sujet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
    else:
        st.info("👋 **Étape 1 : Évaluer les risques.** Précisez votre contexte pour une analyse sur-mesure.")
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée en quelques phrases :", height=150, placeholder="Décrivez votre concept...")
        ctx = c2.text_area("Votre contexte (Cible, budget, ressources) :", height=150, placeholder="Ex: Solo-preneur, 2000€ de budget, cible : France...")
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("🧠 Analyse stratégique en cours...", expanded=True):
                    full_prompt = f"Idée: {idea}\nContexte: {ctx}\nAnalyse critique business structurée (SWOT, Risques, Viabilité)."
                    res = model.generate_content(full_prompt).text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()
            elif st.session_state.user['credits'] <= 0: st.warning("Crédits insuffisants.")
            else: st.warning("Veuillez décrire votre idée.")

with tab2:
    if not st.session_state.project["analysis"]: st.warning("⚠️ Complétez l'étape 1 d'abord.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        if st.button("Passer au GPS ➡️", use_container_width=True): 
            st.session_state.project["choice"] = "Pivots validés"
            st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("💡 Recherche d'angles morts...", expanded=True):
                res = model.generate_content(f"3 Pivots business pour : {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()

with tab3:
    if not st.session_state.project["choice"]: st.warning("⚠️ Choisissez vos pivots à l'étape 2.")
    elif st.session_state.project["gps"]: st.markdown(st.session_state.project["gps"])
    else:
        if st.button("Générer le Plan d'Action GPS (1 crédit)", use_container_width=True):
            with st.status("🗺️ Séquençage des étapes...", expanded=True):
                res = model.generate_content(f"Plan d'action GPS détaillé pour : {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
