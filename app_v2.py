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
    
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.570709531"

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

def generate_form_link():
    if not st.session_state.user: return BASE_FORM_URL
    p = st.session_state.project
    resume = f"IDÉE: {p['idea']}\nANALYSE: {p['analysis'][:300]}...\nGPS: {p['gps'][:300]}..."
    params = {ENTRY_EMAIL: st.session_state.user['email'], ENTRY_IDEE: p['idea'], ENTRY_AUDIT: resume}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.markdown(f"**👤 {st.session_state.user['email']}**")
        st.info(f"🎯 **{st.session_state.user['credits']} Crédits**")
        
        with st.popover("❓ Guide de Survie", use_container_width=True):
            t_tech, t_meth = st.tabs(["💻 Tech", "🧠 Méthode"])
            with t_tech: st.markdown("**PAS DE F5** : N'actualisez pas.\n**Veille** : Écran actif sur mobile.")
            with t_meth: st.markdown("**Détails** : Donnez 5-10 lignes.\n**Cible** : Soyez précis.")

        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()

        with st.expander("📂 Gestion de Session", expanded=False):
            # EXPORT
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Sauver JSON", json_str, "projet.json", use_container_width=True)
            
            # IMPORT (Fixé avec bouton de confirmation)
            up = st.file_uploader("📥 Charger JSON", type="json")
            if up:
                if st.button("✅ Confirmer le chargement", use_container_width=True):
                    data = json.load(up)
                    st.session_state.project.update(data.get("data", {}))
                    st.success("Chargé !")
                    time.sleep(1)
                    st.rerun()
            
            if st.button("✨ Nouveau Projet", use_container_width=True):
                st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
                st.rerun()

        with st.expander("💎 Expertise Humaine", expanded=True):
            st.link_button("🚀 Réserver mon Audit", generate_form_link(), use_container_width=True)

# --- 5. AUTH / CORPS ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    email_in = st.text_input("Email Pro")
    if st.button("Connexion"):
        st.session_state.user = login_user(email_in); st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")
tab1, tab2, tab3 = st.tabs(["🔍 1. Analyse", "💡 2. Pivots", "🗺️ 3. GPS"])

with tab1:
    if st.session_state.project["analysis"]:
        st.success(f"📌 Sujet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
        st.divider()
        st.info("💡 **Analyse terminée !** Cliquez sur l'onglet **'2. Pivots'** en haut ou utilisez le bouton ci-dessous.")
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", height=150, placeholder="Décrivez votre concept...")
        ctx = c2.text_area("Contexte :", height=150, placeholder="Cible, budget...")
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Analyse en cours..."):
                    res = model.generate_content(f"Critique business: {idea}\nCtx: {ctx}").text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

with tab2:
    if not st.session_state.project["analysis"]:
        st.warning("⚠️ Faites d'abord l'étape 1 (Analyse).")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        if st.button("Valider et passer au GPS ➡️", use_container_width=True): 
            st.session_state.project["choice"] = "Validé"; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("Brainstorming..."):
                res = model.generate_content(f"3 pivots pour : {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()

with tab3:
    if not st.session_state.project["choice"]:
        st.warning("⚠️ Choisissez vos pivots à l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.success("✅ GPS prêt. N'oubliez pas de sauvegarder votre JSON.")
    else:
        if st.button("Générer le Plan GPS (1 crédit)", use_container_width=True):
            with st.status("Planification..."):
                res = model.generate_content(f"Plan GPS pour : {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
