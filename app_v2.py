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
    
    .intro-box { 
        background-color: rgba(127, 90, 240, 0.15); 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #7f5af0; 
        margin-bottom: 25px; 
        color: #1a1a1a !important; 
        font-weight: 500;
    }
    .variant-divider { color: #7f5af0; font-weight: bold; border-top: 2px dashed #7f5af0; margin-top: 30px; padding-top: 15px; }
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
    st.error("⚠️ Configuration Secrets incomplète ou erronée.")
    st.stop()

# --- 3. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 4. FONCTIONS ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DOSSIER STRATEGIQUE - IA BRAINSTORMER", ln=True, align="C")
    pdf.ln(10)
    sections = [("IDEE", data['idea']), ("CONTEXTE", data['context']), ("1. ANALYSE", data['analysis']), ("2. PIVOTS", data['pivots']), ("3. GPS", data['gps'])]
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(127, 90, 240)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Helvetica", size=10); pdf.set_text_color(0, 0, 0)
        text = content if content else "Non genere"
        pdf.multi_cell(0, 5, text.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
    return bytes(pdf.output())

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart(); msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 DEMANDE AUDIT : {st.session_state.user['email']}"
        msg.attach(MIMEText(f"Message : {user_msg}\nClient : {st.session_state.user['email']}", 'plain'))
        part = MIMEBase('application', 'octet-stream'); part.set_payload(pdf_content)
        encoders.encode_base64(part); part.add_header('Content-Disposition', f"attachment; filename= Audit.pdf")
        msg.attach(part)
        server = smtplib.SMTP("smtp.gmail.com", 587); server.starttls(); server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg); server.quit(); return True
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
        st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()

        with st.expander("📂 Gestion de Session", expanded=False):
            if st.session_state.project["analysis"]:
                st.download_button("📄 Telecharger PDF", create_pdf_bytes(st.session_state.project), "Rapport.pdf", "application/pdf", use_container_width=True)
            st.download_button("💾 Sauver JSON", json.dumps({"data": st.session_state.project}, indent=4), "projet.json", use_container_width=True)
            up = st.file_uploader("📥 Importer JSON", type="json")
            if up and st.button("✅ Valider l'Import"):
                st.session_state.project.update(json.load(up).get("data", {}))
                st.rerun()

        with st.expander("💎 Expertise Humaine", expanded=True):
            if st.session_state.project["analysis"]:
                msg_exp = st.text_area("Mot pour Florent :", placeholder="Questions, audit...")
                if st.button("🚀 Réserver mon Audit PDF"):
                    if send_audit_email(msg_exp, create_pdf_bytes(st.session_state.project)): st.success("Dossier envoyé !")
                    else: st.error("Erreur d'envoi.")
            else: st.warning("Faites l'étape 1 pour débloquer.")

# --- 6. CORPS ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Connexion"):
        res = supabase.table("users").select("*").eq("email", em.strip().lower()).execute()
        if res.data: st.session_state.user = res.data[0]; st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")
st.markdown("<div class='intro-box'><b>Bienvenue dans votre Usine à Stratégie.</b><br>Suivez les 3 étapes pour transformer une idée floue en plan d'action concret. À tout moment, sollicitez Florent pour un audit approfondi.</div>", unsafe_allow_html=True)

# Navigation
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

st.progress(st.session_state.current_step / 3)

# ETAPE 1 : ANALYSE (CASCADE RESET)
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        st.divider()
        st.warning("⚠️ Pensez à sauvegarder avant de relancer l'analyse qui écrasera la version actuelle")
        with st.popover("🔄 Affiner & Relancer (1 crédit)"):
            refine = st.text_area("Ajustements (ex: focus B2B)...")
            if st.button("Regénérer l'Analyse"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Analyse en cours..."):
                        p = f"Analyse cette idée : {st.session_state.project['idea']}.\nInstruction : {refine}."
                        st.session_state.project["analysis"] = model.generate_content(p).text
                        # RESET de la cascade pour coherence
                        st.session_state.project["pivots"] = ""
                        st.session_state.project["gps"] = ""
                        consume_credit(); st.rerun()
        if st.button("➡️ Suivant : Pivots", use_container_width=True): st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea, ctx = c1.text_area("Votre idée :"), c2.text_area("Contexte :")
        if st.button("Lancer l'Analyse (1 crédit)"):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Analyse en cours..."):
                    res = model.generate_content(f"Critique business: {idea}\nCtx: {ctx}").text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# ETAPE 2 : PIVOTS (CUMULATIF)
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]:
        st.warning("Veuillez d'abord générer l'analyse à l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Ajouter 3 nouveaux pivots (1 crédit)"):
            refine = st.text_area("Orientation pour les variantes 4, 5 et 6...")
            if st.button("Générer les variantes"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Analyse en cours..."):
                        p = f"Basé sur l'idée : {st.session_state.project['idea']}, génère 3 NOUVELLES variantes de pivots numérotées 4, 5 et 6. Instruction : {refine}. Termine par un tableau comparatif."
                        res = model.generate_content(p).text
                        st.session_state.project["pivots"] += f"\n\n<div class='variant-divider'>🔄 Variante : {refine}</div>\n\n{res}"
                        consume_credit(); st.rerun()
        colA, colB = st.columns(2)
        if colA.button("⬅️ Retour"): st.session_state.current_step = 1; st.rerun()
        if colB.button("➡️ Suivant : GPS"): st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)"):
            with st.status("Analyse en cours..."):
                res = model.generate_content(f"3 pivots pour: {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()

# ETAPE 3 : GPS
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if not st.session_state.project["pivots"]:
        st.warning("Veuillez d'abord générer les pivots à l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.divider()
        st.warning("⚠️ Pensez à sauvegarder avant de relancer le plan qui écrasera la version actuelle")
        with st.popover("🔄 Affiner & Relancer le GPS (1 crédit)"):
            refine = st.text_area("Ajustement (ex: Plan sur 12 mois)...")
            if st.button("Regénérer le Plan"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Analyse en cours..."):
                        p = f"Fais un plan GPS pour : {st.session_state.project['idea']}.\nContrainte : {refine}."
                        st.session_state.project["gps"] = model.generate_content(p).text
                        consume_credit(); st.rerun()
        if st.button("⬅️ Retour aux Pivots"): st.session_state.current_step = 2; st.rerun()
    else:
        if st.button("Générer le GPS (1 crédit)"):
            with st.status("Analyse en cours..."):
                res = model.generate_content(f"Plan GPS pour: {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
