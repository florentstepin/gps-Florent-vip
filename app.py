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

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Stratège IA - V2.5 Pro", page_icon="🧠", layout="wide")

# --- CONNEXIONS OPTIMISÉES (CACHE RESOURCE) ---
@st.cache_resource
def get_supabase_client():
    """Maintient une connexion unique à Supabase sans rechargement inutile"""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def get_ai_model():
    """Initialise Gemini 2.5 Pro avec les paramètres de 2026"""
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Configuration du modèle Pro pour une analyse profonde
    return genai.GenerativeModel('gemini-2.5-pro')

try:
    supabase = get_supabase_client()
    model = get_ai_model()
    # Récupération des secrets pour les emails et Stripe
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    SENDER_EMAIL = st.secrets["EMAIL_SENDER"]
    SENDER_PASS = st.secrets["EMAIL_PASSWORD"]
    RECEIVER_EMAIL = st.secrets["EMAIL_RECEIVER"]
except Exception as e:
    st.error(f"⚠️ Erreur d'initialisation des services ou secrets : {e}")
    st.stop()

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; border-radius: 8px; font-weight: bold; height: 3em; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    
    /* Bandeau info : Texte sombre sur fond lavande */
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
    st.error("⚠️ Configuration Secrets incomplète ou erronée dans Streamlit Cloud.")
    st.stop()

# --- 3. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 4. FONCTIONS (PDF, EMAIL, CREDITS) ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DOSSIER STRATEGIQUE - IA BRAINSTORMER", ln=True, align="C")
    pdf.ln(10)
    sections = [
        ("IDEE DU PROJET", data['idea']),
        ("CONTEXTE", data['context']),
        ("1. ANALYSE CRASH-TEST", data['analysis']),
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
            
# --- 5. SIDEBAR (GUIDE RESTAURÉ) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    if st.session_state.user:
        st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
        
        # GUIDE DE SURVIE (RESTAURÉ)
        with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
            t1, t2, t3 = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
            with t1: st.markdown("**PAS DE F5** : N'actualisez jamais.\n**VEILLE** : Gardez l'écran allumé.")
            with t2: st.markdown("**DÉTAILS** : Donnez 5-10 lignes de carburant.\n**AFFINAGE** : Utilisez le bouton 'Relancer' pour ajuster.")
            with t3: st.markdown("**JSON** : Sauvegardez pour reprendre gratuitement.\n**PDF** : Le rapport propre pour Florent.")

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

# --- 6. CORPS DE L'APPLI ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Connexion"):
        res = supabase.table("users").select("*").eq("email", em.strip().lower()).execute()
        if res.data: st.session_state.user = res.data[0]; st.rerun()
    st.stop()

st.title("🧠 Stratège IA V2")
st.markdown("<div class='intro-box'><b>Bienvenue dans votre Usine à Stratégie.</b><br>Suivez les 3 étapes pour transformer une idée floue en plan d'action concret. À tout moment, sollicitez Florent pour un audit approfondi.</div>", unsafe_allow_html=True)

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

# --- ÉTAPE 1 : ANALYSE ---
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        st.divider()
        st.warning("⚠️ Pensez à sauvegarder avant de relancer l'analyse.")
        
    with st.popover("🌀 Affiner & Relancer (1 crédit)"):
            # 1. On crée la zone pour taper l'ajustement
            refine = st.text_area("Ajustements (ex: focus B2B)...")
            
            # 2. On crée le bouton qui déclenche le calcul
            if st.button("Regénérer l'Analyse"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Ré-expertise clinique en cours..."):
                        # 3. LE NOUVEAU PROMPT (votre bloc de positionnement.png)
                        p_refine = f"""
                        # RÔLE : Ingénieur Audit Stratégique (Posture clinique et froide).
                        # MISSION : Ré-expertise D.U.R. suite à ajustement.
                        # IDÉE : {st.session_state.project['idea']}
                        # NOUVEL ANGLE/AJUSTEMENT : {refine}
                        
                        1. Scores D.U.R. (/10) : Douloureux, Urgent, Reconnu.
                        2. Impact de l'ajustement sur les Fractures Structurelles.
                        3. NOUVEAU VERDICT : **GO**, **NO-GO** ou **PIVOT**.
                        """
                        st.session_state.project["analysis"] = model.generate_content(p_refine).text
                        
                        # 4. RESET DES ÉTAPES SUIVANTES (Cascade)
                        st.session_state.project["pivots"], st.session_state.project["gps"] = "", ""
                        consume_credit(); st.rerun()
    if st.button("➡️ Suivant : Pivots", use_container_width=True): 
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", placeholder="Soyez précis...")
        ctx = c2.text_area("Contexte :", placeholder="Ressources, temps...")
        
        if st.button("Lancer l'Audit de Survie (1 crédit)"):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Audit clinique en cours..."):
                    # ICI : L'indentation est maintenant parfaite
                    prompt_master = f"""
                    # RÔLE : Ingénieur Audit (Posture clinique et froide).
                    # MISSION : Analyse D.U.R. de l'idée : {idea}
                    # CONTEXTE : {ctx}
                    
                    1. Scores D.U.R. (/10) : Douloureux, Urgent, Reconnu.
                    2. Les 3 Fractures Structurelles.
                    3. VERDICT : **GO**, **NO-GO** ou **PIVOT**.
                    """
                    res = model.generate_content(prompt_master).text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# --- ÉTAPE 2 : PIVOTS ---
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]:
        st.warning("Veuillez générer l'analyse à l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Ajouter 3 pivots de plus (1 crédit)"):
            refine = st.text_area("Orientation (ex: pivots technologiques)...")
            if st.button("Générer Variantes 4, 5 et 6"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Analyse en cours..."):
                        p = f"Basé sur l'idée : {st.session_state.project['idea']}, génère 3 NOUVEAUX pivots numérotées 4, 5 et 6. Instruction : {refine}. Termine par un tableau comparatif."
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

# --- ÉTAPE 3 : GPS (AVEC CHOIX DU PIVOT) ---
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    
    if not st.session_state.project["pivots"]:
        st.warning("⚠️ Veuillez d'abord générer des pivots à l'étape 2.")
    
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer sur un autre angle"):
            st.session_state.project["gps"] = ""; st.rerun()
    
    else:
        st.info("🎯 **Dernière étape.** Quel angle stratégique avez-vous choisi ?")
        
        # Rappel des pivots pour faciliter le copier-coller
        with st.expander("🔍 Revoir vos pivots générés", expanded=False):
            st.markdown(st.session_state.project["pivots"])
            
        pivot_selectionne = st.text_area("Copiez ici le pivot qui vous intéresse :", 
                                        placeholder="Ex: Pivot n°2 : L'approche B2B...")

        if st.button("Tracer mon GPS sur-mesure (1 crédit)", use_container_width=True):
            if pivot_selectionne:
                with st.status("Génération de la feuille de route..."):
                    prompt_gps = f"""
                    Tu es un Directeur des Opérations expert en exécution.
                    IDÉE : {st.session_state.project['idea']}
                    ANGLE CHOISI : {pivot_selectionne}
                    
                    Génère un plan GPS (Goal, Path, Strategy) concret :
                    - LA VISION : L'objectif final.
                    - MOIS 1 : 3 actions prioritaires.
                    - MOIS 3 : Structure & Acquisition.
                    - L'ALERTE ROUGE : Le signal précis montrant que ce pivot échoue.
                    """
                    st.session_state.project["gps"] = model.generate_content(prompt_gps).text
                    consume_credit(); st.rerun()
            else:
                st.error("Veuillez copier un pivot pour lancer le plan d'action.")
        
        if st.button("⬅️ Retour aux Pivots"):
            st.session_state.current_step = 2; st.rerun()
