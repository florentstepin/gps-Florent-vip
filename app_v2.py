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
    .step-label { color: #7f5af0; font-weight: bold; font-size: 1.1em; }
    .intro-box { background-color: rgba(127, 90, 240, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 20px; }
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
    st.error("⚠️ Configuration manquante dans les Secrets Streamlit.")
    st.stop()

# --- 3. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 4. FONCTIONS PDF & EMAIL ---
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
        ("2. PIVOTS PROPOSES", data['pivots'] if data['pivots'] else "Non généré"),
        ("3. PLAN D'ACTION GPS", data['gps'] if data['gps'] else "Non généré")
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

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 DEMANDE AUDIT : {st.session_state.user['email']}"
        body = f"Bonjour Florent,\n\nUne nouvelle demande de coaching/audit vient d'arriver.\n\nClient : {st.session_state.user['email']}\nMessage : {user_msg}"
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
        
        with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
            t1, t2, t3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
            with t1: st.markdown("**PAS DE F5** : N'actualisez jamais.\n**VEILLE** : Gardez l'écran allumé.")
            with t2: st.markdown("**DÉTAILS** : Donnez 5-10 lignes de carburant.\n**PRÉCISION** : Spécifiez votre cible.")
            with t3: st.markdown("**JSON** : Sauvegardez pour reprendre gratuitement.\n**PDF** : Le rapport propre pour Florent.")

        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()

        with st.expander("📂 Gestion de Session", expanded=False):
            # EXPORT PDF
            if st.session_state.project["analysis"]:
                if st.button("📄 Télécharger le Rapport PDF", use_container_width=True):
                    pdf_data = create_pdf_bytes(st.session_state.project)
                    st.download_button("Cliquez pour enregistrer le PDF", pdf_data, "Rapport_Stratege.pdf", "application/pdf", use_container_width=True)
            
            # EXPORT JSON
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Sauver Projet (JSON)", json_str, "projet.json", use_container_width=True)
            
            # IMPORT JSON
            up = st.file_uploader("📥 Charger un Projet", type="json")
            if up:
                if st.button("✅ Valider l'Import"):
                    st.session_state.project.update(json.load(up).get("data", {}))
                    st.rerun()

        # HIGH TICKET DÉBLOQUÉ
        with st.expander("💎 Expertise Humaine", expanded=True):
            if st.session_state.project["analysis"]:
                st.markdown("<p style='font-size:0.85em;'>Besoin d'aller plus loin ? Envoyez ce dossier à Florent pour un audit expert.</p>", unsafe_allow_html=True)
                msg_exp = st.text_area("Votre mot pour Florent :", placeholder="Questions, demande de coaching...")
                if st.button("🚀 Envoyer mon dossier à Florent"):
                    with st.spinner("Envoi..."):
                        pdf_data = create_pdf_bytes(st.session_state.project)
                        if send_audit_email(msg_exp, pdf_data): st.success("Dossier envoyé ! Florent vous répondra vite.")
                        else: st.error("Erreur technique d'envoi.")
            else:
                st.warning("⚠️ Faites l'analyse étape 1 pour débloquer l'audit.")

# --- 6. CORPS DE L'APPLI ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Connexion"):
        st.session_state.user = supabase.table("users").select("*").eq("email", em.strip().lower()).execute().data[0]
        st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")
st.markdown("""<div class='intro-box'><b>Bienvenue dans votre Usine à Stratégie.</b><br>
Suivez les 3 étapes pour transformer une idée floue en plan d'action concret. 
À tout moment, vous pouvez solliciter Florent pour un audit approfondi via la barre latérale.</div>""", unsafe_allow_html=True)

# Barre de progression
lbls = ["Analyse", "Pivots", "GPS"]
st.write(f"<p class='step-label'>Étape {st.session_state.current_step} : {lbls[st.session_state.current_step-1]}</p>", unsafe_allow_html=True)
st.progress(st.session_state.current_step / 3)

# ETAPE 1 : ANALYSE
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        st.divider()
        if st.button("➡️ Étape Suivante : Les Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", height=150, placeholder="Ex: Créer une app de...")
        ctx = c2.text_area("Contexte (Cible, budget) :", height=150, placeholder="Ex: Solo-preneur, 2000€...")
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Analyse en cours..."):
                    res = model.generate_content(f"Critique business: {idea}\nCtx: {ctx}").text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# ETAPE 2 : PIVOTS
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        st.divider()
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Étape Précédente", use_container_width=True):
            st.session_state.current_step = 1; st.rerun()
        if col2.button("➡️ Étape Suivante : Le GPS", use_container_width=True):
            st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("Brainstorming..."):
                res = model.generate_content(f"3 pivots pour: {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()
        if st.button("⬅️ Retour"): st.session_state.current_step = 1; st.rerun()

# ETAPE 3 : GPS
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.divider()
        if st.button("⬅️ Étape Précédente", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        if st.button("Générer le GPS (1 crédit)", use_container_width=True):
            with st.status("Planification..."):
                res = model.generate_content(f"Plan GPS pour: {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
        if st.button("⬅️ Retour"): st.session_state.current_step = 2; st.rerun()
