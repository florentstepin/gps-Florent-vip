import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
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

# --- 3. STYLE CSS (HARMONISATION TITRE & BOUTONS) ---
st.markdown("""
    <style>
    /* TITRE PRINCIPAL : SUPÉRIEUR AUX BOUTONS */
    .main-title {
        font-size: 4.8rem !important;      /* Légèrement supérieur aux 3.5rem des boutons */
        font-weight: 900 !important;
        color: #1a1a1a;
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
        letter-spacing: -2px;
    }

    /* NAVIGATION HAUTE : POLICE MASSIVE (Vu sur fenêtre bis.png) */
    .st-key-nav_1 button p, .st-key-nav_2 button p, .st-key-nav_3 button p {
        font-size: 3.5rem !important;      /* Taille validée sur capture */
        font-weight: 900 !important;
        line-height: 1 !important;
        margin: 0 !important;
    }
    
    .st-key-nav_1 button, .st-key-nav_2 button, .st-key-nav_3 button {
        height: auto !important;
        min-height: 140px !important;      /* Adapté à la taille bis */
        border: 4px solid #7f5af0 !important;
        border-radius: 25px !important;
        background-color: white !important;
        transition: transform 0.2s ease;
    }
    .st-key-nav_1 button:hover, .st-key-nav_2 button:hover, .st-key-nav_3 button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(127, 90, 240, 0.2);
    }

    /* BOUTONS COULEURS SIDEBAR */
    div.stButton > button[kind="primary"] { background-color: #e02e2e !important; color: white !important; border: none !important; }
    .expert-box > div:first-child { background-color: #2eb82e !important; color: white !important; border-radius: 8px; }
    .io-box > div:first-child { background-color: #ffcc00 !important; color: #1a1a1a !important; border-radius: 8px; }

    .intro-box { background-color: rgba(127, 90, 240, 0.15); padding: 25px; border-radius: 15px; border: 1px solid #7f5af0; margin-bottom: 30px; }
    .intro-box h3 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #1a1a1a; }
    </style>
""", unsafe_allow_html=True)

# --- 4. DIALOG : GUIDE QUICK-START (SÉCURISÉ) ---
@st.dialog("🚀 Guide Quick-Start : Maîtrisez Stratège IA en 5 minutes")
def show_quick_start():
    st.error("⚠️ Ne rafraichissez pas la page avant d'avoir fait un export JSON de votre travail. Pour raison de confidentialité vos données ne sont pas stockées.")
    st.markdown("""
    ### 🛠️ Votre Parcours en 3 Étapes
    | Étape | Action | Objectif |
    | :--- | :--- | :--- |
    | **01. Audit D.U.R.** | Saisissez idée + contexte | Verdict : **GO, NO-GO ou PIVOT** |
    | **02. Les Pivots** | Explorez 3 trajectoires | Comparer modèles, cibles & marges |
    | **03. Plan d'Action** | Copiez votre pivot favori | Feuille de route : **Vision, M1 & M3** |

    ### 🧠 3 Astuces pour réussir
    1. **Affiner** : Ajustez vos résultats sans frais via le popover.
    2. **Sauver** : Exportez en **JSON** (Sauvegarde) pour reprendre gratuitement.
    3. **Partager** : Exportez votre dossier en **PDF** (Partage) pour vos partenaires.

    ### 💎 Expertise & Audit Qualifié
    L'audit humain par Florent est **exclusivement réservé aux projets précis** pour éviter le tourisme entrepreneurial.
    """)
    if st.button("J'ai bien compris, fermer le guide", use_container_width=True):
        st.rerun()

# --- 5. FONCTIONS MÉTIER ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AUDIT STRATEGIQUE - V2.5 PRO", ln=True, align="C")
    sections = [("IDEE", data['idea']), ("1. D.U.R.", data['analysis']), ("2. PIVOTS", data['pivots']), ("3. PLAN D'ACTION", data['gps'])]
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Helvetica", size=10); pdf.multi_cell(0, 5, str(content).encode('latin-1', 'replace').decode('latin-1'))
    return bytes(pdf.output())

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 AUDIT HAUT POTENTIEL : {st.session_state.user['email']}"
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

# --- 7. ACCÈS (CORRIGÉ LIGNE 124) ---
if not st.session_state.user:
    st.markdown("<h1 class='main-title'>🧠 Stratège IA</h1>", unsafe_allow_html=True)
    em = st.text_input("Email Pro")
    if st.button("Accéder"):
        email_clean = em.strip().lower()
        if email_clean:
            res = supabase.table("users").select("*").eq("email", email_clean).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else:
                new = {"access_code": str(uuid.uuid4()), "email": email_clean, "credits": 2}
                ins = supabase.table("users").insert(new).execute()
                if ins.data: # Fix syntaxe ':'
                    st.session_state.user = ins.data[0]; st.rerun()
    st.stop()

# --- 8. SIDEBAR ---
with st.sidebar:
    st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
    if st.button("🚀 Guide Quick-Start", use_container_width=True, key="btn_guide_final"): show_quick_start()
    st.link_button("⚡ Crédits supplémentaires", LINK_RECHARGE, type="primary", use_container_width=True)
    st.divider()

    st.markdown('<div class="io-box">', unsafe_allow_html=True)
    with st.expander("📂 Import / Export", expanded=False):
        if st.session_state.project["analysis"]:
            st.download_button("📄 PDF (Partage)", create_pdf_bytes(st.session_state.project), "Audit.pdf", key="dl_pdf_f")
        st.download_button("💾 JSON (Sauvegarde)", json.dumps({"data": st.session_state.project}), "projet.json", key="dl_json_f")
        up = st.file_uploader("📥 Charger un projet", type="json", key="up_json_f")
        if up and st.button("✅ Valider", key="btn_up_f"):
            st.session_state.project.update(json.load(up).get("data", {})); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="expert-box">', unsafe_allow_html=True)
    with st.expander("💎 Expertise Humaine (Audit)", expanded=True):
        if st.session_state.project["analysis"]:
            imp = st.selectbox("Importance projet :", ["haute", "moyenne", "basse"], key="q_imp_f")
            tim = st.selectbox("Timing :", ["Immédiat", "Sous 3 mois", "En réflexion"], key="q_time_f")
            att = st.text_area("Quelle est votre attente ?", key="q_att_f")
            if st.button("🚀 Réserver mon Audit PDF", use_container_width=True, key="q_btn_f"):
                if att:
                    if send_audit_email(f"Importance: {imp} | Timing: {tim} | Attente: {att}", create_pdf_bytes(st.session_state.project)):
                        st.success("Demande transmise !"); st.balloons()
        else: st.warning("Faites l'étape 1 d'abord.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. CORPS ---
st.markdown("<h1 class='main-title'>🧠 Stratège IA V2.5 Pro</h1>", unsafe_allow_html=True)
st.markdown("<div class='intro-box'><h3>Transformer en moins de 5 minutes une idée floue en plan d'action concret</h3></div>", unsafe_allow_html=True)

n1, n2, n3 = st.columns(3)
with n1:
    if st.button("🔍 1.Analyse", use_container_width=True, key="nav_1"): st.session_state.current_step = 1; st.rerun()
with n2:
    if st.button("💡 2.Pivots", use_container_width=True, key="nav_2"): st.session_state.current_step = 2; st.rerun()
with n3:
    if st.button("🗺️ 3.Plan d'Action", use_container_width=True, key="nav_3"): st.session_state.current_step = 3; st.rerun()

# --- LOGIQUE ÉTAPES ---
if st.session_state.current_step == 1:
    st.header("🔍 Audit D.U.R.")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        with st.popover("🌀 Affiner l'analyse"):
            ref = st.text_area("Ajustements...", key="ref_1_f")
            if st.button("Regénérer", key="btn_ref_1_f"):
                if st.session_state.user['credits'] > 0:
                    st.session_state.project["analysis"] = model.generate_content(f"Audit D.U.R pour {st.session_state.project['idea']}. Ajustement: {ref}").text
                    consume_credit(); st.rerun()
        if st.button("➡️ Suivant : Lancer les Pivots", use_container_width=True, key="next_1_f"):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        id_ = c1.text_area("Votre idée précise :", key="in_idea_f")
        ctx = c2.text_area("Votre contexte :", key="in_ctx_f")
        if st.button("Lancer l'Audit (1 crédit)", key="btn_step1_f", use_container_width=True):
            if id_ and st.session_state.user['credits'] > 0:
                res = model.generate_content(f"Audit D.U.R complet pour: {id_}. Contexte: {ctx}").text
                st.session_state.project.update({"idea": id_, "context": ctx, "analysis": res})
                consume_credit(); st.rerun()

elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]: st.warning("Faites l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Plus de variantes"): # Fix Ligne 270
            ref2 = st.text_area("Orientation...", key="ref_2_f")
            if st.button("Générer 4-6", key="btn_ref_2_f"):
                if st.session_state.user['credits'] > 0:
                    p = f"Génère 3 pivots pour {st.session_state.project['idea']}. Orientation: {ref2}."
                    st.session_state.project["pivots"] += f"\n\n{model.generate_content(p).text}"
                    consume_credit(); st.rerun()
        if st.button("➡️ Suivant : Plan d'Action", use_container_width=True, key="next_2_f"):
            st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", key="btn_step2_f", use_container_width=True):
            p = f"3 pivots pour {st.session_state.project['idea']}. Tableau comparatif requis."
            st.session_state.project["pivots"] = model.generate_content(p).text
            consume_credit(); st.rerun()

elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action")
    if not st.session_state.project["pivots"]: st.warning("Faites l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer", key="btn_reset_3_f"): st.session_state.project["gps"] = ""; st.rerun()
    else:
        sel = st.text_area("Pivot choisi :", key="sel_pivot_f")
        if st.button("Tracer le Plan d'Action (1 crédit)", key="btn_step3_f", use_container_width=True):
            if sel:
                p = f"Plan d'Action pour : {sel}."
                st.session_state.project["gps"] = model.generate_content(p).text
                consume_credit(); st.rerun()
