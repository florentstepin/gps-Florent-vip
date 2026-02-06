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

# --- 2. CONNEXIONS OPTIMISÉES (CACHE) ---
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
    st.error(f"⚠️ Erreur de configuration : {e}")
    st.stop()

# --- 3. STYLE CSS (COULEURS & SOUS-TITRE) ---
st.markdown("""
    <style>
    /* 1. Bouton ROUGE : Crédits supplémentaires */
    div.stButton > button[kind="primary"] {
        background-color: #e02e2e !important;
        color: white !important;
        border: none !important;
    }
    
    /* 2. Bouton VERT : Expertise Humaine (L'expander) */
    .st-key-expander_expertise { 
        border: 1px solid #2eb82e !important;
    }
    .st-key-expander_expertise > details > summary {
        background-color: #2eb82e !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
    }

    /* 3. Bouton JAUNE : Import / Export */
    .st-key-expander_io > details > summary {
        background-color: #ffcc00 !important;
        color: #1a1a1a !important;
        border-radius: 8px;
        font-weight: bold;
    }

    .intro-box { 
        background-color: rgba(127, 90, 240, 0.15); 
        padding: 20px; border-radius: 10px; border: 1px solid #7f5af0; 
        margin-bottom: 25px; color: #1a1a1a;
    }
    .intro-box h3 { margin: 0; font-size: 1.25rem; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- 4. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_step" not in st.session_state: st.session_state.current_step = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": ""}

# --- 5. FONCTIONS MÉTIER ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DOSSIER STRATEGIQUE - STRATEGE IA", ln=True, align="C")
    pdf.ln(10)
    sections = [("IDEE", data['idea']), ("CONTEXTE", data['context']), 
                ("1. AUDIT D.U.R.", data['analysis']), ("2. PIVOTS", data['pivots']), ("3. PLAN GPS", data['gps'])]
    for title, content in sections:
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(127, 90, 240)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Helvetica", size=10); pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, (content if content else "Etape non faite").encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)
    return bytes(pdf.output())

def send_audit_email(user_msg, pdf_content):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL; msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"🚀 AUDIT QUALIFIÉ : {st.session_state.user['email']}"
        msg.attach(MIMEText(f"Détails du prospect :\n{user_msg}", 'plain'))
        part = MIMEBase('application', 'octet-stream'); part.set_payload(pdf_content)
        encoders.encode_base64(part); part.add_header('Content-Disposition', "attachment; filename=Dossier_Strategique.pdf")
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

@st.dialog("🚀 Guide Quick-Start : Maîtrisez Stratège IA en 5 minutes")
def show_quick_start():
    st.markdown("""
    Bienvenue dans votre **Usine à Stratégie**. Cet outil n'est pas un simple chat, c'est un laboratoire où nous allons tester la résistance de votre idée avant de tracer votre route vers le succès.

    ### 💡 La Règle d'Or : "Le Carburant"
    Plus vous donnez de détails, plus l'IA est précise. Ne dites pas : *"Je veux vendre des fleurs"*. Dites : *"Je veux vendre des bouquets de fleurs séchées par abonnement pour les bureaux d'entreprises à Lyon, avec une livraison en vélo-cargo."*

    ### 🛠️ Votre Parcours en 3 Étapes
    | Étape | Action | Objectif |
    | :--- | :--- | :--- |
    | **01. Audit D.U.R.** | Saisissez idée + contexte | Verdict : **GO, NO-GO ou PIVOT** |
    | **02. Les Pivots** | Explorez 3 trajectoires | Comparer les modèles & marges |
    | **03. Le Plan GPS** | Copiez votre pivot favori | Feuille de route : **Vision, M1 & M3** |

    ### 🧠 3 Astuces pour tirer le maximum de l'outil
    * **Affiner & Relancer** : Si l'audit est trop général, utilisez le popover pour ajouter une contrainte (ex: *"Budget de 500€"*). L'IA recalculera tout.
    * **Accumulez les Variantes** : À l'étape 2, générez 6 ou 9 angles. Ils se cumulent dans votre rapport pour vous laisser le choix.
    * **Sauvez votre "Cerveau de Projet"** : Exportez en **JSON**. Demain, importez-le pour reprendre là où vous en étiez sans consommer de nouveaux crédits.

    ### ⚠️ Précautions Techniques
    * **Pas de touche F5** : N'actualisez jamais. Utilisez les boutons de navigation interne (🔍, 💡, 🗺️).
    * **Écran Allumé** : Gardez l'onglet actif pendant les calculs (10-15 sec).

    ### 💎 Besoin d'un regard humain ?
    Une fois l'étape 1 terminée :
    1. Allez dans la barre latérale : **"Expertise Humaine"**.
    2. Précisez votre importance et votre attente.
    3. Cliquez sur **"Réserver mon Audit"**.
    
    *Le rapport final (PDF) vous attend dans la barre latérale. Bonne stratégie !*
    """)
    if st.button("Fermer le guide"):
        st.rerun()

# --- 6. ACCÈS (LOGIN/SIGNUP UUID) ---
if not st.session_state.user:
    st.title("🚀 Accès Stratège IA")
    em = st.text_input("Email Pro")
    if st.button("Se connecter ou s'inscrire", use_container_width=True):
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
                        st.session_state.user = insert_res.data[0]; st.rerun()
            except Exception as e: st.error(f"Erreur base de données : {e}")
    st.stop()

# --- 7. SIDEBAR (V3 TEST : ÉPURÉE & COLORÉE) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
    
    if st.button("🚀 Guide Quick-Start", use_container_width=True):
        show_quick_start()

    # Bouton ROUGE
    st.link_button("⚡ Crédits supplémentaires", LINK_RECHARGE, type="primary", use_container_width=True)

    st.divider()

    # Bouton JAUNE (Import/Export)
    with st.expander("📂 Import / Export", expanded=False):
        # On force une clé unique pour le style CSS
        st.markdown('<div class="st-key-expander_io"></div>', unsafe_allow_html=True)
        if st.session_state.project["analysis"]:
            st.download_button("📄 Telecharger PDF", create_pdf_bytes(st.session_state.project), "Rapport.pdf", use_container_width=True)
        st.download_button("💾 Sauver JSON", json.dumps({"data": st.session_state.project}), "projet.json", use_container_width=True)
        up = st.file_uploader("📥 Importer JSON", type="json")
        if up and st.button("✅ Valider l'Import"):
            st.session_state.project.update(json.load(up).get("data", {})); st.rerun()

    # Bouton VERT (Expertise Humaine)
    with st.expander("💎 Expertise Humaine (Qualification)", expanded=True):
        st.markdown('<div class="st-key-expander_expertise"></div>', unsafe_allow_html=True)
        if st.session_state.project["analysis"]:
            importance = st.selectbox("Importance projet :", ["haute", "moyenne", "basse"], key="qualif_imp")
            timeline = st.selectbox("Timing :", ["Immédiat", "Sous 3 mois", "En réflexion"], key="qualif_time")
            attente = st.text_area("Quelle est votre attente ?", key="qualif_attente")
            
            if st.button("🚀 Réserver mon Audit PDF", use_container_width=True, key="qualif_btn"):
                if attente:
                    details = f"IMPORTANCE: {importance} | TIMELINE: {timeline} | ATTENTE: {attente}"
                    if send_audit_email(details, create_pdf_bytes(st.session_state.project)): 
                        st.success("Dossier envoyé !"); st.balloons()
                else: st.warning("Précisez votre attente.")
        else:
            st.warning("Terminez l'étape 1 pour débloquer l'expertise.")

    # BOUTON JAUNE : Import / Export
    with st.expander("📂 Import / Export", expanded=False):
        if st.session_state.project["analysis"]:
            st.download_button("📄 Telecharger PDF", create_pdf_bytes(st.session_state.project), "Rapport.pdf", use_container_width=True)
        st.download_button("💾 Sauver JSON", json.dumps({"data": st.session_state.project}), "projet.json", use_container_width=True)
        up = st.file_uploader("📥 Importer JSON", type="json")
        if up and st.button("✅ Valider l'Import"):
            st.session_state.project.update(json.load(up).get("data", {})); st.rerun()

    # ÉVOLUTION 1 : FORMULAIRE DE QUALIFICATION MODIFIÉ
    with st.expander("💎 Expertise Humaine (Qualification)", expanded=True):
        if st.session_state.project["analysis"]:
            # Remplacement du budget par l'importance
            importance = st.selectbox("Importance projet :", ["basse", "moyenne", "haute"])
            timeline = st.selectbox("Timing :", ["Immédiat", "Sous 3 mois", "En réflexion"])
            # Remplacement de la question par l'attente
            attente = st.text_area("Quelle est votre attente ?", placeholder="Expliquez ce que vous recherchez...")
            
            if st.button("🚀 Réserver mon Audit PDF"):
                if attente:
                    details = f"Importance: {importance} | Timing: {timeline} | Attente: {attente}"
                    if send_audit_email(details, create_pdf_bytes(st.session_state.project)): 
                        st.success("Dossier envoyé !"); st.balloons()
                    else: st.error("Erreur d'envoi.")
                else:
                    st.warning("Veuillez préciser votre attente pour valider.")
        else: st.warning("Terminez l'étape 1 pour contacter Florent.")


# --- 8. CORPS DE L'APPLI ---
st.title("🧠 Stratège IA V2.5 Pro")
st.markdown(f"""
    <div class='intro-box'>
        <h3>Transformer en moins de 5 minutes une idée floue en plan d'action concret</h3>
    </div>
""", unsafe_allow_html=True)

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

# --- ÉTAPE 1 : ANALYSE ---
if st.session_state.current_step == 1:
    st.header("🔍 Analyse Crash-Test D.U.R.")
    if st.session_state.project["analysis"]:
        st.markdown(st.session_state.project["analysis"])
        st.divider()
        with st.popover("🌀 Affiner & Relancer (1 crédit)"):
            refine = st.text_area("Ajustements (ex: focus B2B)...")
            if st.button("Regénérer l'Analyse"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Ré-expertise clinique..."):
                        p = f"Audit D.U.R. IDÉE : {st.session_state.project['idea']}. AJUSTEMENT : {refine}. Scores /10, Fractures, Verdict: GO/NO-GO/PIVOT."
                        st.session_state.project["analysis"] = model.generate_content(p).text
                        st.session_state.project["pivots"], st.session_state.project["gps"] = "", ""
                        consume_credit(); st.rerun()
        # BOUTON DE NAVIGATION BASSE
        if st.button("➡️ Suivant : Lancer les Pivots", use_container_width=True):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        idea = c1.text_area("Votre idée :", placeholder="Soyez précis...")
        ctx = c2.text_area("Contexte :", placeholder="Ressources, temps...")
        if st.button("Lancer l'Audit de Survie (1 crédit)", use_container_width=True):
            if idea and st.session_state.user['credits'] > 0:
                with st.status("Audit clinique..."):
                    p = f"Analyse D.U.R. complète pour : {idea}. Contexte : {ctx}. Scores /10, Fractures, Verdict: GO/NO-GO/PIVOT."
                    res = model.generate_content(p).text
                    st.session_state.project.update({"idea": idea, "context": ctx, "analysis": res})
                    consume_credit(); st.rerun()

# --- ÉTAPE 2 : PIVOTS ---
elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]: st.warning("Faites l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        st.divider()
        with st.popover("➕ Ajouter 3 pivots de plus (1 crédit)"):
            refine = st.text_area("Nouvelle orientation...")
            if st.button("Générer Variantes 4, 5 et 6"):
                if st.session_state.user['credits'] > 0:
                    with st.status("Calcul..."):
                        p = f"Génère 3 NOUVEAUX pivots (4, 5, 6) pour {st.session_state.project['idea']}. Instruction : {refine}. TABLEAU COMPARATIF REQUIS (Concept, Cible, Avantage, Revenus, Complexité, Marge). Pas de notes /10."
                        st.session_state.project["pivots"] += f"\n\n<div class='variant-divider'>🔄 Variante : {refine}</div>\n\n{model.generate_content(p).text}"
                        consume_credit(); st.rerun()
        # BOUTON DE NAVIGATION BASSE
        if st.button("➡️ Suivant : Lancer le Plan d'Action (GPS)", use_container_width=True):
            st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", use_container_width=True):
            with st.status("Trajectoires..."):
                p = f"Propose 3 pivots pour {st.session_state.project['idea']}. TABLEAU COMPARATIF REQUIS (Concept, Cible, Avantage, Revenus, Complexité, Marge). Pas de notes /10."
                st.session_state.project["pivots"] = model.generate_content(p).text
                consume_credit(); st.rerun()

# --- ÉTAPE 3 : GPS ---
elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action GPS")
    if not st.session_state.project["pivots"]: st.warning("Générez des pivots d'abord.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer sur un autre angle"):
            st.session_state.project["gps"] = ""; st.rerun()
    else:
        with st.expander("Revoir vos pivots"): st.markdown(st.session_state.project["pivots"])
        sel = st.text_area("Copiez le pivot choisi :")
        if st.button("Tracer mon GPS sur-mesure (1 crédit)", use_container_width=True):
            if sel:
                with st.status("Génération..."):
                    p = f"IDÉE : {st.session_state.project['idea']}. PIVOT : {sel}. Génère un plan GPS : Vision, Mois 1 (3 actions), Mois 3 (Structure), Alerte Rouge."
                    st.session_state.project["gps"] = model.generate_content(p).text
                    consume_credit(); st.rerun()
