import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time
import os
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="Stratège IA - V2.5 Pro", page_icon="🧠", layout="wide")

# --- 2. CONNEXIONS OPTIMISÉES (CACHE RESOURCE) ---
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def get_ai_model():
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    return genai.GenerativeModel('gemini-2.5-pro')

try:
    supabase = get_supabase_client()
    model = get_ai_model()
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    SENDER_EMAIL = st.secrets["EMAIL_SENDER"]
    SENDER_PASS = st.secrets["EMAIL_PASSWORD"]
    RECEIVER_EMAIL = st.secrets["EMAIL_RECEIVER"]
except Exception as e:
    st.error(f"⚠️ Erreur d'initialisation : {e}")
    st.stop()

# --- 3. STYLE CSS ---
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; border-radius: 8px; font-weight: bold; height: 3em; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    .intro-box { background-color: rgba(127, 90, 240, 0.15); padding: 20px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 25px; color: #1a1a1a !important; font-weight: 500; }
    .variant-divider { color: #7f5af0; font-weight: bold; border-top: 2px dashed #7f5af0; margin-top: 30px; padding-top: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. INITIALISATION DU SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 5. FONCTIONS UTILES ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DOSSIER STRATEGIQUE - IA BRAINSTORMER", ln=True, align="C")
    pdf.ln(10)
    sections = [
        ("IDEE DU PROJET", data['idea']),
        ("CONTEXTE", data['context']),
        ("1. ANALYSE CRASH-TEST", data['analysis']),
        ("2. PIVOTS STRATEGIQUES", data['pivots']),
        ("3. PLAN D'ACTION GPS", data['gps'])
    ]
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(127, 90, 240)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Helvetica", size=10); pdf.set_text_color(0, 0, 0)
        text = content if content else "Etape non effectuee"
        pdf.multi_cell(0, 5, text.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
    return bytes(pdf.output())

def consume_credit():
    if st.session_state.user:
        new_val = max(0, st.session_state.user['credits'] - 1)
        supabase.table("users").update({"credits": new_val}).eq("email", st.session_state.user['email']).execute()
        st.session_state.user['credits'] = new_val
        if 'total_runs' in st.session_state.user:
            st.session_state.user['total_runs'] += 1

# --- 6. ACCÈS & CRÉATION DE COMPTE (FIXÉ UUID) ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro", placeholder="votre@email.com")
    
    if st.button("Accéder à mon espace", use_container_width=True):
        email_clean = em.strip().lower()
        if email_clean:
            try:
                res = supabase.table("users").select("*").eq("email", email_clean).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.success("Connexion réussie...")
                    st.rerun()
                else:
                    # CRÉATION AVEC CODE UNIQUE (UUID)
                    new_user_data = {
                        "access_code": str(uuid.uuid4()), 
                        "email": email_clean,
                        "credits": 2,
                        "total_runs": 0
                    }
                    insert_res = supabase.table("users").insert(new_user_data).execute()
                    if insert_res.data:
                        st.session_state.user = insert_res.data[0]
                        st.success("Bienvenue ! Compte créé (2 crédits offerts).")
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur base de données : {e}")
        else:
            st.warning("Email requis.")
    st.stop()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
    st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
    
    with st.expander("📂 Export & Import", expanded=False):
        if st.session_state.project["analysis"]:
            st.download_button("📄 Telecharger PDF", create_pdf_bytes(st.session_state.project), "Rapport.pdf", "application/pdf", use_container_width=True)
        up = st.file_uploader("📥 Importer JSON", type="json")
        if up and st.button("✅ Valider l'Import"):
            st.session_state.project.update(json.load(up).get("data", {}))
            st.rerun()

# --- 8. CORPS DE L'APPLI ---
st.title("🧠 Stratège IA V2.5")
st.markdown("<div class='intro-box'><b>Usine à Stratégie</b> : Suivez les 3 étapes.</div>", unsafe_allow_html=True)

# NAVIGATION
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("🔍 1. Analyse", use_container_width=True, type="primary" if st.session_state.current_step == 1 else "secondary"):
        st.session_state.current_step = 1; st.rerun()
with nav2:
    if st.button("💡 2. Pivots", use_container_width=True, type="primary" if st.session_state.current_step == 2 else "secondary"):
        st.session_state.current_step = 2; st.rerun()
with nav3:
    if st.button("🗺️ 3. GPS", use_container_width=True, type="primary" if st.session_state.current_step == 3 else "secondary"):
        st.session_state.current_step = 3; st.rerun()

# ÉTAPE 1 : ANALYSE
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        with st.popover("🌀 Relancer (1 crédit)"):
            refine = st.text_area("Ajustements...")
            if st.button("Regénérer"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Analyse..."):
                        p = f"Analyse D.U.R. de {st.session_state.project['idea']}. Ajustement: {refine}. Verdict: GO/NO-GO."
                        st.session_state.project["analysis"] = model.generate_content(p).text
                        st.session_state.project["pivots"], st.session_state.project["gps"] = "", ""
                        consume_credit(); st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("L'idée :")
        ctx = c2.text_area("Le contexte :")
        if st.button("Lancer l'Audit (1 crédit)"):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Audit..."):
                    p = f"Audit D.U.R. complet pour : {idea}. Contexte : {ctx}."
                    res = model.generate_content(p).text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# ÉTAPE 2 : PIVOTS
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]:
        st.warning("Faites l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Plus de pivots (1 crédit)"):
            refine = st.text_area("Orientation...")
            if st.button("Variantes 4-6"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Calcul..."):
                        p = f"Pivots 4-6 pour {st.session_state.project['idea']}. Orientation: {refine}. Tableau requis."
                        st.session_state.project["pivots"] += f"\n\n{model.generate_content(p).text}"
                        consume_credit(); st.rerun()
    else:
        if st.button("Générer 3 Pivots (1 crédit)"):
            with st.status("Calcul..."):
                p = f"3 pivots stratégiques pour {st.session_state.project['idea']}. Tableau comparatif requis."
                st.session_state.project["pivots"] = model.generate_content(p).text
                consume_credit(); st.rerun()

# ÉTAPE 3 : GPS
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan GPS")
    if not st.session_state.project["pivots"]:
        st.warning("Faites l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer"):
            st.session_state.project["gps"] = ""; st.rerun()
    else:
        with st.expander("Revoir les pivots"): st.markdown(st.session_state.project["pivots"])
        sel = st.text_area("Copiez le pivot choisi :")
        if st.button("Tracer le GPS (1 crédit)"):
            if sel:
                with st.status("Tracé..."):
                    p = f"Plan GPS pour le pivot : {sel}. Vision, Mois 1, Mois 3, Alerte rouge."
                    st.session_state.project["gps"] = model.generate_content(p).text
                    consume_credit(); st.rerun()
