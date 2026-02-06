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

# --- 2. CONNEXIONS (CACHE) ---
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
    st.error(f"⚠️ Erreur configuration : {e}")
    st.stop()

# --- 3. STYLE CSS (BOUTONS & H3) ---
st.markdown("""
    <style>
    /* Bouton ROUGE : Crédits supplémentaires */
    div.stButton > button[kind="primary"] { background-color: #e02e2e !important; color: white !important; border: none !important; }
    
    /* Expander VERT : Expertise Humaine */
    .expert-box > div:first-child { background-color: #2eb82e !important; color: white !important; border-radius: 8px; }

    /* Expander JAUNE : Import / Export */
    .io-box > div:first-child { background-color: #ffcc00 !important; color: #1a1a1a !important; border-radius: 8px; }

    .intro-box { background-color: rgba(127, 90, 240, 0.15); padding: 20px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 25px; color: #1a1a1a; }
    .intro-box h3 { margin: 0; font-size: 1.3rem; font-weight: 700; color: #1a1a1a; }
    .variant-divider { color: #7f5af0; font-weight: bold; border-top: 2px dashed #7f5af0; margin-top: 30px; padding-top: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. DIALOG : GUIDE QUICK-START ---
@st.dialog("🚀 Guide Quick-Start : Maîtrisez Stratège IA en 5 minutes")
def show_quick_start():
    st.markdown("""
    Bienvenue dans votre laboratoire de stratégie.
    ### 💡 La Règle d'Or : "Le Carburant"
    Soyez précis. Ne dites pas : *"Je veux vendre des fleurs"*. Dites : *"Je veux vendre des bouquets de fleurs séchées par abonnement B2B à Lyon avec livraison écologique."*
    ### 🛠️ Parcours en 3 Étapes
    1. **Audit D.U.R.** : Verdict clinique GO/NO-GO.
    2. **Les Pivots** : 3 trajectoires avec tableau de marges.
    3. **Plan d'Action** : Votre feuille de route opérationnelle (Mois 1 & 3).
    ### 🧠 Astuces
    * **Affiner** : Utilisez le bouton dédié pour ajuster sans frais.
    * **Sauver** : Exportez en **JSON** pour reprendre gratuitement plus tard.
    ---
    *Fermez cette fenêtre via la croix en haut à droite.*
    """)

# --- 5. FONCTIONS MÉTIER ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AUDIT STRATEGIQUE - V2.5 PRO", ln=True, align="C")
    sections = [("IDEE", data['idea']), ("1. D.U.R.", data['analysis']), ("2. PIVOTS", data['pivots']), ("3. ACTION", data['gps'])]
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Helvetica", size=10); pdf.multi_cell(0, 5, str(content).encode('latin-1', 'replace').decode('latin-1'))
    return bytes(pdf.output())

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 AUDIT : {st.session_state.user['email']}"
        msg.attach(MIMEText(user_msg, 'plain'))
        part = MIMEBase('application', 'octet-stream'); part.set_payload(pdf_content)
        encoders.encode_base64(part); part.add_header('Content-Disposition', "attachment; filename=Audit.pdf")
        msg.attach(part)
        server = smtplib.SMTP("smtp.gmail.com", 587); server.starttls(); server.login(SENDER_EMAIL, SENDER_PASS)
        server.send_message(msg); server.quit(); return True
    except: return False

def consume_credit():
    if st.session_state.user:
        new_val = max(0, st.session_state.user['credits'] - 1)
        supabase.table("users").update({"credits": new_val}).eq("email", st.session_state.user['email']).execute()
        st.session_state.user['credits'] = new_val

# --- 6. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 7. ACCÈS (LOGIN) ---
if not st.session_state.user:
    st.title("🚀 Connexion Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Accéder"):
        email_clean = em.strip().lower()
        if email_clean:
            res = supabase.table("users").select("*").eq("email", email_clean).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else:
                new = {"access_code": str(uuid.uuid4()), "email": email_clean, "credits": 2}
                ins = supabase.table("users").insert(new).execute()
                if ins
