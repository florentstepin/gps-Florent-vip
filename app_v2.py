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
    .intro-box { background-color: rgba(127, 90, 240, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 20px; color: white; }
    .variant-divider { color: #7f5af0; font-weight: bold; border-top: 2px dashed #7f5af0; margin-top: 25px; padding-top: 10px; }
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
    st.error("⚠️ Secrets manquants ou mal formatés. Vérifiez vos paramètres Streamlit.")
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
        ("IDEE DU PROJET", data['idea']),
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
        msg['Subject'] = f"🚀 AUDIT EXPERT : {st.session_state.user['email']}"
        body = f"Message client : {user_msg}\nEmail : {st.session_state.user['email']}"
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

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
        
        with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
            t1, t2, t3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
            with t1: st.markdown("**PAS DE F5** : N'actualisez jamais.\n**VEILLE** : Gardez l'écran allumé.")
            with t2: st.markdown("**DÉTAILS** : Plus vous donnez de carburant, plus l'IA est précise.")
            with t3: st.markdown("**JSON** : Sauvegardez pour reprendre gratuitement.\n**PDF** : Votre rapport final.")

        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()

        with st.expander("📂 Gestion de Session", expanded=False):
            if st.session_state.project["analysis"]:
                pdf_bytes = create_pdf_bytes(st.session_state.project)
                st.download_button("📄 Télécharger le Rapport PDF", pdf_bytes, "Rapport.pdf", "application/pdf", use_container_width=True)
            
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Sauver Projet (JSON)", json_str, "projet.json", use_container_width=True)
            
            up = st.file_uploader("📥 Importer un Projet", type="json")
            if up:
                if st.button("✅ Valider l'Import"):
                    st.session_state.project.update(json.load(up).get("data", {}))
                    st.rerun()

        with st.expander("💎 Expertise Humaine", expanded=True):
            if st.session_state.project["analysis"]:
                msg_exp = st.text_area("Votre mot pour Florent :", placeholder="Demande de coaching...")
                if st.button("🚀 Réserver mon Audit PDF"):
                    with st.spinner("Envoi..."):
                        if send_audit_email(msg_exp, create_pdf_bytes(st.session_state.project)): st.success("Dossier envoyé !")
                        else: st.error("Erreur d'envoi.")
            else: st.warning("Faites l'analyse pour débloquer l'audit.")

# --- 6. CORPS DE L'APPLI ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Connexion"):
        res = supabase.table("users").select("*").eq("email", em.strip().lower()).execute()
        if res.data: st.session_state.user = res.data[0]; st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")

# BANDEAU D'EXPLICATION (RESTAURÉ)
st.markdown("""<div class='intro-box'><b>Bienvenue dans votre Usine à Stratégie.</b><br>
Suivez les 3 étapes pour transformer une idée floue en plan d'action concret. 
À tout moment, vous pouvez solliciter Florent pour un audit approfondi via la barre latérale.</div>""", unsafe_allow_html=True)

# BANDEAU DE NAVIGATION
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

# ETAPE 1 : ANALYSE
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
                    p = f"Analyse cette idée : {st.session_state.project['idea']}.\nInstruction : {refine}."
                    st.session_state.project["analysis"] = model.generate_content(p).text
                    st.session_state.user['credits'] -= 1; st.rerun()
        if st.button("➡️ Suivant : Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea, ctx = c1.text_area("Votre idée :"), c2.text_area("Contexte :")
        if st.button("Lancer l'Analyse (1 crédit)"):
            if idea and st.session_state.user['credits'] > 0:
                res = model.generate_content(f"Critique business: {idea}\nCtx: {ctx}").text
                st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                st.session_state.user['credits'] -= 1; st.rerun()

# ETAPE 2 : PIVOTS (CUMULATIF)
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        with st.popover("➕ Ajouter des variantes (1 crédit)"):
            refine = st.text_area("Ex: Pivots plus technologiques...")
            if st.button("Générer 3 pivots de plus"):
                if st.session_state.user['credits'] > 0:
                    p = f"Génère 3 NOUVEAUX pivots pour : {st.session_state.project['idea']}.\nAjustement : {refine}."
                    res = model.generate_content(p).text
                    st.session_state.project["pivots"] += f"\n\n<div class='variant-divider'>🔄 Variante : {refine}</div>\n\n{res}"
                    st.session_state.user['credits'] -= 1; st.rerun()
        colA, colB = st.columns(2)
        if colA.button("⬅️ Retour"): st.session_state.current_step = 1; st.rerun()
        if colB.button("➡️ Suivant : GPS"): st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)"):
            res = model.generate_content(f"3 pivots pour: {st.session_state.project['idea']}").text
            st.session_state.project["pivots"] = res
            st.session_state.user['credits'] -= 1; st.rerun()

# ETAPE 3 : GPS
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.divider()
        st.warning("⚠️ Pensez à sauvegarder avant de relancer le plan qui écrasera la version actuelle")
        with st.popover("🔄 Affiner & Relancer le GPS (1 crédit)"):
            refine = st.text_area("Ex: Plan sur 6 mois...")
            if st.button("Regénérer le Plan"):
                if st.session_state.user['credits'] > 0:
                    p = f"Fais un plan GPS pour : {st.session_state.project['idea']}.\nContrainte : {refine}."
                    st.session_state.project["gps"] = model.generate_content(p).text
                    st.session_state.user['credits'] -= 1; st.rerun()
        if st.button("⬅️ Retour aux Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        if st.button("Générer le GPS (1 crédit)"):
            res = model.generate_content(f"Plan GPS pour: {st.session_state.project['idea']}").text
            st.session_state.project["gps"] = res
            st.session_state.user['credits'] -= 1; st.rerun()
