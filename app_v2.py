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

# Thème Violet Stratège
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; border-radius: 8px; font-weight: bold; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    .step-label { color: #7f5af0; font-weight: bold; font-size: 1.1em; }
    .main-desc { font-size: 1em; color: rgba(255,255,255,0.7); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SECRETS & CONNEXIONS ---
try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Secrets Email
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

# --- 4. FONCTIONS ---
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

def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RAPPORT STRATEGIQUE - STRATEGE IA", ln=True, align="C")
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
        pdf.multi_cell(0, 5, content.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
    return pdf.output()

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 AUDIT V2 : {st.session_state.user['email']}"
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

# --- 5. SIDEBAR (GUIDE PREMIUM + GESTION + HIGH TICKET) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.info(f"👤 {st.session_state.user['email']}\n\n🎯 **{st.session_state.user['credits']} Crédits**")
        
        # GUIDE DE SURVIE PREMIUM (ONGLETS)
        with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
            t1, t2, t3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
            with t1: st.markdown("**PAS DE F5** : N'actualisez jamais.\n**VEILLE** : Gardez l'écran mobile allumé.")
            with t2: st.markdown("**CARBURANT** : Donnez 5-10 lignes de détails.\n**CIBLE** : Soyez ultra-spécifique.")
            with t3: st.markdown("**JSON** : Sauvegardez pour reprendre gratuitement.\n**PDF** : Votre rapport final structuré.")

        st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
        st.divider()

        # GESTION DE SESSION (IMPORT AVEC CONFIRMATION)
        with st.expander("📂 Gestion de Session", expanded=False):
            json_str = json.dumps({"data": st.session_state.project}, indent=4)
            st.download_button("💾 Exporter JSON", json_str, "projet.json", use_container_width=True)
            up = st.file_uploader("📥 Importer JSON", type="json")
            if up:
                if st.button("✅ Confirmer le chargement", use_container_width=True):
                    st.session_state.project.update(json.load(up).get("data", {}))
                    st.success("Chargé !")
                    time.sleep(1); st.rerun()
            if st.button("✨ Nouveau Projet", use_container_width=True):
                st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}
                st.session_state.current_step = 1; st.rerun()

        # HIGH TICKET (AUDIT EMAIL)
        with st.expander("💎 Expertise Humaine", expanded=True):
            st.markdown("<p style='font-size:0.8em;'>Transférez votre dossier PDF à Florent pour un audit expert.</p>", unsafe_allow_html=True)
            if st.session_state.project["gps"]:
                msg_exp = st.text_area("Votre mot pour Florent :", placeholder="Vos questions...")
                if st.button("🚀 Réserver mon Audit PDF"):
                    with st.spinner("Envoi..."):
                        pdf_data = create_pdf_bytes(st.session_state.project)
                        if send_audit_email(msg_exp, pdf_data): st.success("Dossier envoyé !")
                        else: st.error("Erreur d'envoi.")
            else: st.warning("Terminez le GPS d'abord.")

# --- 6. CORPS DE L'APPLI (NAVIGATION LINEAIRE) ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Connexion"): st.session_state.user = login_user(em); st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")
lbls = ["Analyse", "Pivots", "GPS"]
st.write(f"<p class='step-label'>Étape {st.session_state.current_step} : {lbls[st.session_state.current_step-1]}</p>", unsafe_allow_html=True)
st.progress(st.session_state.current_step / 3)

# ETAPE 1 : ANALYSE
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    st.markdown("<p class='main-desc'>Nous allons évaluer la viabilité brute de votre idée. Soyez précis sur votre cible et vos ressources.</p>", unsafe_allow_html=True)
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        if st.button("➡️ Passer aux Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", height=150, placeholder="Ex: Créer une plateforme de...")
        ctx = c2.text_area("Contexte :", height=150, placeholder="Ex: Solo-preneur, 2000€ budget...")
        if st.button("Lancer l'Analyse (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Analyse en cours..."):
                    res = model.generate_content(f"Critique business: {idea}\nCtx: {ctx}").text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# ETAPE 2 : PIVOTS
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    st.markdown("<p class='main-desc'>Explorez 3 angles d'attaque différents pour contourner les obstacles identifiés.</p>", unsafe_allow_html=True)
    if st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Retour", use_container_width=True): st.session_state.current_step = 1; st.rerun()
        if col2.button("➡️ Passer au GPS", use_container_width=True): st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("Recherche..."):
                res = model.generate_content(f"3 pivots pour: {st.session_state.project['idea']}").text
                st.session_state.project["pivots"] = res
                consume_credit(); st.rerun()
        if st.button("⬅️ Retour"): st.session_state.current_step = 1; st.rerun()

# ETAPE 3 : GPS
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    st.markdown("<p class='main-desc'>Votre feuille de route opérationnelle étape par étape pour passer à l'action.</p>", unsafe_allow_html=True)
    if st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("⬅️ Retour"): st.session_state.current_step = 2; st.rerun()
    else:
        if st.button("Générer le GPS (1 crédit)", use_container_width=True):
            with st.status("Planification..."):
                res = model.generate_content(f"Plan GPS pour: {st.session_state.project['idea']}").text
                st.session_state.project["gps"] = res
                consume_credit(); st.rerun()
        if st.button("⬅️ Retour"): st.session_state.current_step = 2; st.rerun()
