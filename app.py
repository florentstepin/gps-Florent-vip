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

# --- 2. CONNEXIONS (CACHE RESOURCE) ---
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
    st.error(f"⚠️ Erreur Secrets : {e}")
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

# --- 4. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 5. FONCTIONS (PDF, EMAIL, CREDITS) ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DOSSIER STRATEGIQUE - IA BRAINSTORMER", ln=True, align="C")
    pdf.ln(10)
    sections = [
        ("IDEE DU PROJET", data['idea']),
        ("CONTEXTE", data['context']),
        ("1. ANALYSE CRASH-TEST (D.U.R.)", data['analysis']),
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

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
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
        if 'total_runs' in st.session_state.user:
            st.session_state.user['total_runs'] += 1

# --- 6. ACCÈS (FIXÉ UUID) ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Accéder à mon espace", use_container_width=True):
        email_clean = em.strip().lower()
        if email_clean:
            try:
                res = supabase.table("users").select("*").eq("email", email_clean).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    new_user = {"access_code": str(uuid.uuid4()), "email": email_clean, "credits": 2, "total_runs": 0}
                    insert_res = supabase.table("users").insert(new_user).execute()
                    if insert_res.data:
                        st.session_state.user = insert_res.data[0]
                        st.success("Bienvenue ! Compte créé.")
                        st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")
        else: st.warning("Email requis.")
    st.stop()

# --- 7. SIDEBAR (GUIDE & EXPERTISE RESTAURÉS) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
    
    # GUIDE DE SURVIE
    with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
        t1, t2, t3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
        with t1: st.markdown("**PAS DE F5** : N'actualisez jamais.\n**VEILLE** : Gardez l'écran allumé.")
        with t2: st.markdown("**DÉTAILS** : Donnez du carburant (5-10 lignes).\n**AFFINAGE** : Utilisez 'Relancer' pour ajuster.")
        with t3: st.markdown("**JSON** : Sauvegardez pour reprendre plus tard.\n**PDF** : Votre rapport final.")

    st.link_button("⚡ Recharger", LINK_RECHARGE, type="primary", use_container_width=True)
    st.divider()

    with st.expander("📂 Gestion de Session", expanded=False):
        if st.session_state.project["analysis"]:
            st.download_button("📄 Telecharger PDF", create_pdf_bytes(st.session_state.project), "Rapport.pdf", use_container_width=True)
        st.download_button("💾 Sauver JSON", json.dumps({"data": st.session_state.project}, indent=4), "projet.json", use_container_width=True)
        up = st.file_uploader("📥 Importer JSON", type="json")
        if up and st.button("✅ Valider l'Import"):
            st.session_state.project.update(json.load(up).get("data", {}))
            st.rerun()

    with st.expander("💎 Expertise Humaine", expanded=True):
        if st.session_state.project["analysis"]:
            msg_exp = st.text_area("Mot pour Florent :", placeholder="Questions, demande d'audit...")
            if st.button("🚀 Réserver mon Audit PDF"):
                if send_audit_email(msg_exp, create_pdf_bytes(st.session_state.project)): st.success("Dossier envoyé !")
                else: st.error("Erreur d'envoi.")
        else: st.warning("Complétez l'étape 1 pour débloquer.")

# --- 8. CORPS DE L'APPLI ---
st.title("🧠 Stratège IA V2.5")
st.markdown("<div class='intro-box'><b>Bienvenue.</b> Suivez les 3 étapes pour transformer votre idée en plan d'action.</div>", unsafe_allow_html=True)

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

# ÉTAPE 1 : ANALYSE (PROMPT DUR)
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test D.U.R.")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        with st.popover("🌀 Affiner & Relancer (1 crédit)"):
            refine = st.text_area("Ajustements (ex: focus B2B)...")
            if st.button("Regénérer"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Ré-expertise clinique..."):
                        p = f"MISSION : Ré-expertise D.U.R. IDÉE : {st.session_state.project['idea']}. AJUSTEMENT : {refine}. 1. Scores D.U.R. (/10). 2. Fractures Structurelles. 3. Verdict: GO/NO-GO/PIVOT."
                        st.session_state.project["analysis"] = model.generate_content(p).text
                        st.session_state.project["pivots"], st.session_state.project["gps"] = "", ""
                        consume_credit(); st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :")
        ctx = c2.text_area("Contexte :")
        if st.button("Lancer l'Audit (1 crédit)"):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Audit clinique..."):
                    p = f"Analyse D.U.R. IDÉE : {idea}. CONTEXTE : {ctx}. 1. Scores D.U.R. (/10). 2. Fractures Structurelles. 3. Verdict: GO/NO-GO/PIVOT."
                    res = model.generate_content(p).text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# ÉTAPE 2 : PIVOTS (PROMPT HARMONISÉ TABLEAU)
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]:
        st.warning("Veuillez générer l'analyse à l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Plus de pivots (1 crédit)"):
            refine = st.text_area("Orientation (ex: pivots technologiques)...")
            if st.button("Générer 4, 5 et 6"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Analyse..."):
                        p = f"IDÉE : {st.session_state.project['idea']}. Orientation: {refine}. Génère 3 NOUVEAUX pivots (4, 5, 6). REQUIS : TABLEAU COMPARATIF (Concept Clé, Cible, Avantage, Revenus, Complexité, Potentiel Marge). Pas de notes /10."
                        st.session_state.project["pivots"] += f"\n\n<div class='variant-divider'>🔄 Variante : {refine}</div>\n\n{model.generate_content(p).text}"
                        consume_credit(); st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)"):
            with st.status("Calcul des trajectoires..."):
                p = f"IDÉE : {st.session_state.project['idea']}. ANALYSE : {st.session_state.project['analysis']}. Propose 3 pivots (1, 2, 3). REQUIS : TABLEAU COMPARATIF (Concept Clé, Cible, Avantage, Revenus, Complexité, Potentiel Marge). Pas de notes /10."
                st.session_state.project["pivots"] = model.generate_content(p).text
                consume_credit(); st.rerun()

# ÉTAPE 3 : GPS (PROMPT ACTION)
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if not st.session_state.project["pivots"]:
        st.warning("Générez des pivots d'abord.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer"): st.session_state.project["gps"] = ""; st.rerun()
    else:
        sel = st.text_area("Copiez le pivot choisi :")
        if st.button("Tracer mon GPS (1 crédit)"):
            if sel:
                with st.status("Génération..."):
                    p = f"IDÉE : {st.session_state.project['idea']}. PIVOT CHOISI : {sel}. Génère un plan GPS : Vision, Mois 1 (3 actions), Mois 3 (Structure/Acquisition), Alerte Rouge."
                    st.session_state.project["gps"] = model.generate_content(p).text
                    consume_credit(); st.rerun()
