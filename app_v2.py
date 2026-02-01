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
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

# Custom CSS pour remplacer le rouge par le violet de la marque
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
if "user_note" not in st.session_state: st.session_state.user_note = "" 
if "project" not in st.session_state:
    st.session_state.project = {
        "idea": "", "context": "", "analysis": "", 
        "pivots": "", "gps": "", "choice": None
    }

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

def generate_report():
    p = st.session_state.project
    report = f"# 🧠 RAPPORT STRATÈGE IA\n\n## 📝 IDÉE INITIALE\n{p['idea']}\n\n"
    report += f"## 🎯 CONTEXTE\n{p.get('context', 'Non précisé')}\n\n"
    report += f"## 🔍 ANALYSE CRASH-TEST\n{p['analysis']}\n\n"
    report += f"## 💡 PIVOTS STRATÉGIQUES\n{p['pivots']}\n\n"
    report += f"## 🗺️ PLAN D'ACTION GPS (Choix : {p['choice']})\n{p['gps']}"
    return report

def generate_form_link():
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.project.get("idea", "")
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: f"ID Session V2. Joindre le rapport PDF/MD."}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.user_note = ""
    st.rerun()

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

# --- 5. SIDEBAR V2 (CORRIGÉE) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    
    st.markdown(f"""
    <div style='background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 10px;'>
        <div style='font-size: 0.8em; opacity: 0.7;'>Utilisateur :</div>
        <div style='font-weight: bold; font-size: 0.9em;'>{user['email']}</div>
        <div style='margin-top: 10px; font-weight: bold; color: #7f5af0; font-size: 1.2em;'>🎯 {credits} Crédits</div>
    </div>
    """, unsafe_allow_html=True)

    with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
        st.markdown("### 🧭 Réussir votre stratégie")
        gt1, gt2, gt3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
        with gt1:
            st.markdown("* **Écran mobile** : Gardez-le actif pendant l'analyse (pas de veille).\n* **VPN** : Coupez-le si l'app semble bloquée.")
        with gt2:
            st.markdown("* **Carburant** : Donnez 5-10 lignes de détails.\n* **Spécificité** : Précisez votre cible réelle.")
        with gt3:
            st.markdown("* **JSON** : Exportez après chaque étape.\n* **Rapport** : Utilisez l'export .md pour Notion.")

    st.link_button("⚡ Recharger mes crédits", LINK_RECHARGE, type="primary", use_container_width=True)
    
    st.divider()
    
    with st.expander("📂 Sauvegarde & Export", expanded=False):
        if st.session_state.project["analysis"]:
            st.download_button("📄 Rapport (.md)", generate_report(), "Rapport_Stratege.md", use_container_width=True)
        json_str = json.dumps({"data": st.session_state.project}, indent=4)
        st.download_button("💾 Sauver JSON", json_str, "projet_ia.json", use_container_width=True)
        if st.button("✨ Nouvelle Analyse", use_container_width=True): reset_project()

    with st.expander("💎 Expert Humain", expanded=False):
        st.session_state.user_note = st.text_area("Note pour l'expert", value=st.session_state.user_note, placeholder="Précisez budget, délais...")
        st.link_button("Réserver mon Audit", generate_form_link(), use_container_width=True)

    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 6. CORPS DE L'APPLICATION ---
st.title("🧠 Stratège IA")

tab1, tab2, tab3 = st.tabs(["🔍 1. Analyse Crash-Test", "💡 2. Pivots Stratégiques", "🗺️ 3. Plan d'Action GPS"])

with tab1:
    if st.session_state.project["analysis"]:
        st.success(f"📌 Sujet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
    else:
        st.info("👋 **Étape 1 : Évaluer les risques.** Précisez votre contexte pour une analyse sur-mesure.")
        c1, c2 = st.columns(2)
        with c1:
            idea_input = st.text_area("Votre idée en quelques phrases :", height=150, placeholder="Ex: Créer un SaaS pour les agents immobiliers...")
        with c2:
            context_input = st.text_area("Votre contexte (Cible, Budget, Ressources) :", height=150, placeholder="Ex: Solo-preneur, 2000€ de budget, cible : France...")
        
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea_input and credits > 0:
                with st.status("🧠 Analyse en cours...", expanded=True):
                    full_prompt = f"Idée: {idea_input}\nContexte: {context_input}\nAnalyse critique SWOT, Risques et Viabilité."
                    res = model.generate_content(full_prompt).text
                    st.session_state.project.update({"idea": idea_input, "context": context_input, "analysis": res})
                    consume_credit()
                    st.rerun()

with tab2:
    if not st.session_state.project["analysis"]:
        st.warning("⚠️ Complétez l'étape 1 d'abord.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
        choice = st.radio("Quel angle choisissez-vous pour le GPS ?", opts)
        if st.button("Valider ce choix 🗺️", use_container_width=True):
            st.session_state.project.update({"choice": choice, "gps": ""})
            st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("💡 Recherche d'angles morts...", expanded=True):
                res = model.generate_content(f"3 Pivots pour : {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit()
                st.rerun()

with tab3:
    if not st.session_state.project["choice"]:
        st.warning("⚠️ Choisissez un pivot à l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.success("✅ GPS prêt. Téléchargez votre rapport dans la sidebar !")
    else:
        if st.button("Générer le Plan d'Action (1 crédit)", use_container_width=True):
            with st.status("🗺️ Séquençage des étapes...", expanded=True):
                res = model.generate_content(f"Plan d'action GPS détaillé pour : {st.session_state.project['idea']} (Angle : {st.session_state.project['choice']})").text
                st.session_state.project["gps"] = res
                consume_credit()
                st.rerun()
