import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF # Nécessite fpdf2 dans requirements.txt

# --- 1. CONFIGURATION & THÈME ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; border-radius: 8px; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    .step-label { color: #7f5af0; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SECRETS & CONNEXIONS ---
try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Paramètres Email
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = st.secrets["EMAIL_SENDER"]
    SENDER_PASS = st.secrets["EMAIL_PASSWORD"]
    RECEIVER_EMAIL = st.secrets["EMAIL_RECEIVER"]

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error("⚠️ Configuration incomplète. Vérifiez vos Secrets Streamlit (Clés Google, Supabase et Email).")
    st.stop()

# --- 3. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 4. FONCTIONS TECHNIQUES ---
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

# --- 5. GÉNÉRATION PDF & ENVOI EMAIL ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RAPPORT STRATEGIQUE - STRATEGE IA", ln=True, align="C")
    pdf.ln(10)
    
    sections = [
        ("IDEE DU PROJET", data['idea']),
        ("CONTEXTE & RESSOURCES", data['context']),
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
        pdf.multi_cell(0, 5, content.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
    
    return pdf.output()

def send_audit_email(user_message, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 NOUVEL AUDIT : {st.session_state.user['email']}"

        body = f"Bonjour Florent,\n\nUn client vient de soumettre son dossier.\n\n"
        body += f"Client : {st.session_state.user['email']}\n"
        body += f"Message : {user_message}\n\n"
        body += "Le rapport complet est attache en PDF."
        msg.attach(MIMEText(body, 'plain'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= Audit_{st.session_state.user['email'].split('@')[0]}.pdf")
        msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi : {e}")
        return False

# --- 6. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.info(f"👤 {st.session_state.user['email']}\n\n🎯 **{st.session_state.user['credits']} Crédits**")
        
        with st.popover("❓ Guide de Survie", use_container_width=True):
            st.markdown("**PAS DE F5** : N'actualisez jamais pendant une analyse.\n**DÉTAILS** : Plus vous donnez d'infos (5-10 lignes), plus l'IA est précise.")
        
        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()
        
        with st.expander("📂 Sauvegarde JSON", expanded=False):
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Exporter JSON", json_str, "projet.json", use_container_width=True)
            up = st.file_uploader("📥 Importer JSON", type="json")
            if up:
                if st.button("Confirmer l'import"):
                    st.session_state.project.update(json.load(up).get("data", {}))
                    st.rerun()

# --- 7. CORPS DE L'APPLICATION ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    email_in = st.text_input("Votre Email")
    if st.button("Connexion"):
        st.session_state.user = login_user(email_in); st.rerun()
    st.stop()

# Barre de progression
labels = ["Analyse", "Pivots", "GPS"]
st.write(f"<p class='step-label'>Étape {st.session_state.current_step} : {labels[st.session_state.current_step-1]}</p>", unsafe_allow_html=True)
st.progress(st.session_state.current_step / 3)

# --- ÉTAPE 1 : ANALYSE ---
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        st.divider()
        if st.button("➡️ Étape suivante : Les Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", height=150, placeholder="Décrivez votre concept...")
        ctx = c2.text_area("Contexte (Cible, budget) :", height=150, placeholder="Solo, 2000€, France...")
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Analyse stratégique..."):
                    res = model.generate_content(f"Critique business: {idea}\nContexte: {ctx}").text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# --- ÉTAPE 2 : PIVOTS ---
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        st.divider()
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Retour à l'Analyse", use_container_width=True):
            st.session_state.current_step = 1; st.rerun()
        if col2.button("➡️ Étape suivante : Le GPS", use_container_width=True):
            st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("Recherche d'angles morts..."):
                res = model.generate_content(f"3 pivots pour : {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.current_step = 1; st.rerun()

# --- ÉTAPE 3 : GPS & AUDIT ---
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.divider()
        
        st.subheader("💎 Expertise Humaine")
        msg_expert = st.text_area("Un mot pour Florent ?", placeholder="Précisez vos besoins pour l'audit...")
        
        if st.button("🚀 Envoyer mon dossier PDF à Florent", use_container_width=True):
            with st.spinner("Génération du rapport et envoi..."):
                pdf_report = create_pdf_bytes(st.session_state.project)
                if send_audit_email(msg_expert, pdf_report):
                    st.success("✅ Dossier envoyé avec succès ! Florent vous recontactera par e-mail.")
                else:
                    st.error("❌ Erreur d'envoi. Vérifiez la configuration SMTP.")
        
        if st.button("⬅️ Retour aux Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        if st.button("Générer le GPS (1 crédit)", use_container_width=True):
            with st.status("Planification opérationnelle..."):
                res = model.generate_content(f"Plan GPS pour : {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
