import streamlit as st
from supabase import create_client
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

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; border-radius: 8px; font-weight: bold; height: 3em; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    .nav-active { background-color: #7f5af0 !important; color: white !important; }
    .intro-box { background-color: rgba(127, 90, 240, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 20px; }
    .variant-header { color: #7f5af0; font-weight: bold; border-top: 1px dashed #7f5af0; margin-top: 20px; padding-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXIONS ---
try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    SENDER_EMAIL = st.secrets["EMAIL_SENDER"]
    SENDER_PASS = st.secrets["EMAIL_PASSWORD"]
    RECEIVER_EMAIL = st.secrets["EMAIL_RECEIVER"]

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error("⚠️ Configuration incomplète dans les Secrets Streamlit.")
    st.stop()

# --- 3. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 4. FONCTIONS TECHNIQUES ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "VOTRE DOSSIER STRATEGIQUE - IA BRAINSTORMER", ln=True, align="C")
    pdf.ln(10)
    
    sections = [
        ("IDEE INITIALE", data['idea']),
        ("CONTEXTE", data['context']),
        ("1. ANALYSE CRASH-TEST", data['analysis']),
        ("2. PIVOTS STRATEGIQUES", data['pivots']),
        ("3. PLAN D'ACTION GPS", data['gps'])
    ]
    
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(127, 90, 240)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        text = content if content else "Non genere"
        pdf.multi_cell(0, 5, text.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
    return bytes(pdf.output())

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 DEMANDE AUDIT : {st.session_state.user['email']}"
        body = f"Nouvel audit soumis.\n\nClient : {st.session_state.user['email']}\nMessage : {user_msg}"
        msg.attach(MIMEText(body, 'plain'))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= Audit_{st.session_state.user['email'].split('@')[0]}.pdf")
        msg.attach(part)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

def consume_credit():
    if st.session_state.user:
        new_val = max(0, st.session_state.user['credits'] - 1)
        supabase.table("users").update({"credits": new_val}).eq("email", st.session_state.user['email']).execute()
        st.session_state.user['credits'] = new_val

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.info(f"👤 {st.session_state.user['email']}\n\n🎯 **{st.session_state.user['credits']} Crédits**")
        
        with st.popover("❓ Guide & Méthode", use_container_width=True):
            t1, t2, t3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
            with t1: st.markdown("**PAS DE F5** : N'actualisez jamais.\n**VEILLE** : Gardez l'écran allumé.")
            with t2: st.markdown("**DÉTAILS** : Plus vous êtes précis, plus l'IA est pertinente.")
            with t3: st.markdown("**JSON** : Sauvegardez pour reprendre gratuitement.\n**PDF** : Le rapport pour Florent.")

        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()

        with st.expander("📂 Gestion de Session", expanded=False):
            if st.session_state.project["analysis"]:
                pdf_data = create_pdf_bytes(st.session_state.project)
                st.download_button("📄 Rapport PDF", pdf_data, "Rapport.pdf", "application/pdf", use_container_width=True)
            
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Sauver JSON", json_str, "projet.json", use_container_width=True)
            
            up = st.file_uploader("📥 Importer JSON", type="json")
            if up:
                if st.button("✅ Valider l'Import"):
                    data = json.load(up).get("data", {})
                    st.session_state.project.update(data)
                    st.rerun()

        with st.expander("💎 Expertise Humaine", expanded=True):
            if st.session_state.project["analysis"]:
                msg_exp = st.text_area("Votre mot pour Florent :", placeholder="Questions, demande de coaching...")
                if st.button("🚀 Réserver mon Audit PDF"):
                    with st.spinner("Envoi..."):
                        pdf_data = create_pdf_bytes(st.session_state.project)
                        if send_audit_email(msg_exp, pdf_data): st.success("Dossier envoyé !")
                        else: st.error("Erreur d'envoi.")
            else: st.warning("Faites l'analyse pour débloquer l'audit.")

# --- 6. CORPS DE L'APPLI ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Connexion"):
        res = supabase.table("users").select("*").eq("email", em.strip().lower()).execute()
        if res.data: st.session_state.user = res.data[0]; st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")

# BANDEAU DE NAVIGATION
nav_c1, nav_c2, nav_c3 = st.columns(3)
with nav_c1:
    if st.button("🔍 1. Analyse", use_container_width=True, type="primary" if st.session_state.current_step == 1 else "secondary"):
        st.session_state.current_step = 1; st.rerun()
with nav_c2:
   if st.button("💡 2. Pivots", use_container_width=True, type="primary" if st.session_state.current_step == 2 else "secondary"):
