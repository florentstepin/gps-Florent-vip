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
from fpdf import FPDF

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; border-radius: 8px; font-weight: bold; height: 3em; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    .nav-active { background-color: #7f5af0 !important; color: white !important; }
    .intro-box { background-color: rgba(127, 90, 240, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXIONS & SECRETS ---
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
            with t2: st.markdown("**DÉTAILS** : Donnez 5-10 lignes de carburant.\n**AFFINAGE** : Utilisez le bouton 'Relancer' pour ajuster.")
            with t3: st.markdown("**JSON** : Sauvegardez pour reprendre gratuitement.\n**PDF** : Le rapport propre pour Florent.")

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
        st.session_state.current_step = 2; st.rerun()
with nav_c3:
    if st.button("🗺️ 3. GPS", use_container_width=True, type="primary" if st.session_state.current_step == 3 else "secondary"):
        st.session_state.current_step = 3; st.rerun()

st.progress(st.session_state.current_step / 3)

# ETAPE 1 : ANALYSE
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        with st.popover("🔄 Affiner & Relancer une variante (1 crédit)"):
            refine = st.text_area("Instructions spéciales (Ex: 'Exclure le B2C', 'Ajouter un cas d'usage...')", key="ref1")
            if st.button("Relancer l'Analyse"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Nouvelle analyse en cours..."):
                        prompt = f"Réanalyse cette idée : {st.session_state.project['idea']}.\nRetour utilisateur : {refine}.\nContexte : {st.session_state.project['context']}"
                        st.session_state.project["analysis"] = model.generate_content(prompt).text
                        consume_credit(); st.rerun()
        st.divider()
        if st.button("➡️ Passer aux Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", height=150)
        ctx = c2.text_area("Contexte :", height=150)
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Analyse..."):
                    res = model.generate_content(f"Critique business: {idea}\nCtx: {ctx}").text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# ETAPE 2 : PIVOTS
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        with st.popover("🔄 Affiner & Relancer une variante (1 crédit)"):
            refine = st.text_area("Ex: 'Chercher des pivots plus low-cost', 'Exclure l'abonnement'...", key="ref2")
            if st.button("Relancer les Pivots"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Brainstorming..."):
                        prompt = f"Génère 3 NOUVEAUX pivots pour : {st.session_state.project['idea']}.\nContrainte : {refine}."
                        st.session_state.project["pivots"] = model.generate_content(prompt).text
                        consume_credit(); st.rerun()
        st.divider()
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Retour", use_container_width=True): st.session_state.current_step = 1; st.rerun()
        if col2.button("➡️ Passer au GPS", use_container_width=True): st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("Brainstorming..."):
                res = model.generate_content(f"3 pivots pour: {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()

# ETAPE 3 : GPS
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        with st.popover("🔄 Affiner & Relancer une variante (1 crédit)"):
            refine = st.text_area("Ex: 'Plan sur 3 mois seulement', 'Ajouter une étape marketing'...", key="ref3")
            if st.button("Relancer le GPS"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Planification..."):
                        prompt = f"Refais le plan GPS pour : {st.session_state.project['idea']}.\nAjustement : {refine}."
                        st.session_state.project["gps"] = model.generate_content(prompt).text
                        consume_credit(); st.rerun()
        st.divider()
        if st.button("⬅️ Retour aux Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        if st.button("Générer le GPS (1 crédit)", use_container_width=True):
            with st.status("Planification..."):
                res = model.generate_content(f"Plan GPS pour: {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
