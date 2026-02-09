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

# --- 3. STYLE CSS (ÉQUILIBRÉ) ---
st.markdown("""
    <style>
    /* TITRE HARMONISÉ */
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #1a1a1a;
        margin-bottom: 10px !important;
    }

    /* NAVIGATION : UN CRAN EN-DESSOUS DU TITRE */
    .st-key-nav_1 button p, .st-key-nav_2 button p, .st-key-nav_3 button p {
        font-size: 1.8rem !important;      /* Taille lisible et proportionnelle */
        font-weight: 700 !important;
        line-height: 1.1 !important;
    }
    
    .st-key-nav_1 button, .st-key-nav_2 button, .st-key-nav_3 button {
        height: auto !important;
        min-height: 80px !important;       /* Moins haut pour le mobile */
        border: 2px solid #7f5af0 !important;
        border-radius: 12px !important;
        background-color: white !important;
    }

    /* BOUTONS COULEURS */
    div.stButton > button[kind="primary"] { background-color: #e02e2e !important; color: white !important; border: none !important; }
    .expert-box > div:first-child { background-color: #2eb82e !important; color: white !important; border-radius: 8px; }
    .io-box > div:first-child { background-color: #ffcc00 !important; color: #1a1a1a !important; border-radius: 8px; }

    .intro-box { background-color: rgba(127, 90, 240, 0.1); padding: 20px; border-radius: 10px; border: 1px solid #7f5af0; margin-bottom: 20px; }
    .intro-box h3 { margin: 0; font-size: 1.1rem; font-weight: 600; color: #1a1a1a; }
    </style>
""", unsafe_allow_html=True)

# --- 4. DIALOG : GUIDE QUICK-START COMPLET ---
@st.dialog("🚀 Guide Quick-Start : Maîtrisez Stratège IA en 5 minutes")
def show_quick_start():
    # Alerte de sécurité prioritaire
    st.error("⚠️ Ne rafraichissez pas la page avant d'avoir fait un export JSON de votre travail. Pour raison de confidentialité vos données ne sont pas stockées.")
    
    st.markdown("""
    Bienvenue dans votre **Usine à Stratégie**. Cet outil n'est pas un simple chat, c'est un laboratoire où nous allons tester la résistance de votre idée avant de tracer votre route vers le succès.

    ### 💡 La Règle d'Or : "Le Carburant"
    Plus vous donnez de détails, plus l'IA est précise. Ne dites pas : *"Je veux vendre des fleurs"*. Dites : *"Je veux vendre des bouquets de fleurs séchées par abonnement pour les bureaux d'entreprises à Lyon, avec une livraison en vélo-cargo."*

    ### 🛠️ Votre Parcours en 3 Étapes
    | Étape | Action | Objectif |
    | :--- | :--- | :--- |
    | **01. L'Audit D.U.R.** | Saisissez votre idée et votre contexte. | Verdict clinique : **GO, NO-GO ou PIVOT**. |
    | **02. Les Pivots** | Explorez 3 trajectoires stratégiques. | Comparer les modèles (Cibles, Revenus, Marges). |
    | **03. Plan d'Action** | Copiez votre pivot favori. | Feuille de route : **Vision, Mois 1 et Mois 3**. |

    ### 🧠 3 Astuces pour réussir
    1. **Affiner & Relancer** : Si l'audit initial est trop général, utilisez le popover pour ajouter une contrainte (ex: *"Prends en compte un budget de 500€"*). L'IA recalculera tout.
    2. **Sauver (JSON)** : Cliquez sur **"Sauver JSON"** pour télécharger votre session. Vous pourrez la réimporter plus tard gratuitement pour reprendre là où vous en étiez.
    3. **Partager (PDF)** : Exportez votre dossier en **PDF**. C'est le support professionnel idéal pour présenter votre vision à des partenaires ou investisseurs.

    ### ⚠️ Précautions Techniques
    * **Pas de touche F5** : N'actualisez jamais la page, cela réinitialise la session. Utilisez uniquement les boutons de navigation (Analyse, Pivots, Plan d'Action).
    * **Écran Allumé** : Gardez l'onglet actif pendant les phases de calcul (environ 10-15 secondes).

    ### 💎 Besoin d'un regard humain ?
    L'audit humain par Florent est **exclusivement réservé aux projets précis** pour éviter le tourisme entrepreneurial. Une fois l'étape 1 terminée, utilisez le formulaire de qualification dans la barre latérale pour soumettre votre dossier.
    
    *Le rapport final (PDF) vous attend dans la barre latérale. Bonne stratégie !*
    """)
    if st.button("J'ai compris, fermer le guide", use_container_width=True):
        st.rerun()

# --- 5. FONCTIONS MÉTIER ---
def create_pdf_bytes(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AUDIT STRATEGIQUE", ln=True, align="C")
    sections = [("IDEE", data['idea']), ("1. D.U.R.", data['analysis']), ("2. PIVOTS", data['pivots']), ("3. ACTION", data['gps'])]
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

# --- 7. ACCÈS ---
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
                if ins.data: st.session_state.user = ins.data[0]; st.rerun()
    st.stop()

# --- 8. SIDEBAR ---
with st.sidebar:
    st.info(f"👤 {st.session_state.user['email']}\n🎯 **{st.session_state.user['credits']} Crédits**")
    if st.button("🚀 Guide Quick-Start", use_container_width=True, key="btn_gs_v3"): show_quick_start()
    st.link_button("⚡ Crédits supplémentaires", LINK_RECHARGE, type="primary", use_container_width=True)
    st.divider()

    st.markdown('<div class="io-box">', unsafe_allow_html=True)
    with st.expander("📂 Import / Export", expanded=False):
        if st.session_state.project["analysis"]:
            st.download_button("📄 PDF (Partage)", create_pdf_bytes(st.session_state.project), "Audit.pdf", key="dl_pdf_v3")
        st.download_button("💾 JSON (Sauvegarde)", json.dumps({"data": st.session_state.project}), "projet.json", key="dl_json_v3")
        up = st.file_uploader("📥 Charger un projet", type="json", key="up_json_v3")
        if up and st.button("✅ Valider", key="btn_up_v3"):
            st.session_state.project.update(json.load(up).get("data", {})); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="expert-box">', unsafe_allow_html=True)
    with st.expander("💎 Expertise Humaine (Qualification)", expanded=True):
        if st.session_state.project["analysis"]:
            imp = st.selectbox("Importance :", ["haute", "moyenne", "basse"], key="q_imp_v3")
            tim = st.selectbox("Timing :", ["Immédiat", "Sous 3 mois", "En réflexion"], key="q_time_v3")
            att = st.text_area("Votre attente ?", key="q_att_v3")
            if st.button("🚀 Réserver mon Audit PDF", use_container_width=True, key="q_btn_v3"):
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
            ref = st.text_area("Ajustements...", key="ref_1_v3")
            if st.button("Regénérer", key="btn_ref_1_v3"):
                if st.session_state.user['credits'] > 0:
                    with st.status("🔄 Ré-expertise clinique en cours..."): # BULLE RESTAURÉE
                        p = f"D.U.R pour {st.session_state.project['idea']}. Ajustement: {ref}."
                        st.session_state.project["analysis"] = model.generate_content(p).text
                        consume_credit()
                    st.rerun()
        if st.button("➡️ Suivant : Lancer les Pivots", use_container_width=True, key="next_1_v3"):
            st.session_state.current_step = 2; st.rerun()
    else:
        c1, c2 = st.columns(2)
        id_ = c1.text_area("Votre idée précise :", key="in_idea_v3")
        ctx = c2.text_area("Votre contexte :", key="in_ctx_v3")
        if st.button("Lancer l'Audit (1 crédit)", key="btn_step1_v3", use_container_width=True):
            if id_ and st.session_state.user['credits'] > 0:
                with st.status("🧠 Audit D.U.R en cours..."): # BULLE RESTAURÉE
                    res = model.generate_content(f"Audit D.U.R complet pour: {id_}. Contexte: {ctx}.").text
                    st.session_state.project.update({"idea": id_, "context": ctx, "analysis": res})
                    consume_credit()
                st.rerun()

elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]: st.warning("Faites l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Plus de variantes"): 
            ref2 = st.text_area("Orientation...", key="ref_2_v3")
            if st.button("Générer 4-6", key="btn_ref_2_v3"):
                if st.session_state.user['credits'] > 0:
                    with st.status("⚡ Calcul de nouvelles trajectoires..."): # BULLE RESTAURÉE
                        p = f"Génère 3 pivots pour {st.session_state.project['idea']}. Orientation: {ref2}."
                        st.session_state.project["pivots"] += f"\n\n{model.generate_content(p).text}"
                        consume_credit()
                    st.rerun()
        if st.button("➡️ Suivant : Plan d'Action", use_container_width=True, key="next_2_v3"):
            st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", key="btn_step2_v3", use_container_width=True):
            with st.status("💡 Exploration des pivots possibles..."): # BULLE RESTAURÉE
                p = f"3 pivots pour {st.session_state.project['idea']}. Tableau comparatif requis."
                st.session_state.project["pivots"] = model.generate_content(p).text
                consume_credit()
            st.rerun()

elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action")
    
    if not st.session_state.project["analysis"]: 
        st.warning("Veuillez effectuer l'étape 1 d'abord.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer / Changer de base", key="btn_reset_3_v3"): 
            st.session_state.project["gps"] = ""
            st.rerun()
    else:
        # --- NOUVEAUTÉ : SÉLECTEUR DE SOURCE ---
        st.markdown("### Sur quelle base tracer votre plan ?")
        source_plan = st.radio(
            "Choisissez la direction à suivre :",
            ["Utiliser l'Analyse Initiale (Verdict GO)", "Utiliser un Pivot spécifique de l'Étape 2"],
            index=0,
            horizontal=True,
            key="source_plan_choice"
        )

        content_to_process = ""
        
        if source_plan == "Utiliser un Pivot spécifique de l'Étape 2":
            with st.expander("👁️ Revoir vos pivots pour copier-coller"):
                st.markdown(st.session_state.project["pivots"])
            content_to_process = st.text_area("Collez ici le pivot que vous avez retenu :", key="sel_pivot_v3", placeholder="Collez le texte du tableau ici...")
        else:
            st.info("✅ Mode Fast-Track : L'IA va baser le plan sur votre Audit D.U.R initial.")
            content_to_process = st.session_state.project["analysis"]

        # --- BOUTON DE GÉNÉRATION ---
        if st.button("Tracer le Plan d'Action (1 crédit)", key="btn_step3_v3", use_container_width=True):
            if content_to_process:
                with st.status("🗺️ Génération de la feuille de route opérationnelle..."):
                    # On adapte le prompt selon la source
                    instruction = "l'analyse initiale" if source_plan == "Utiliser l'Analyse Initiale (Verdict GO)" else "le pivot suivant"
                    p = f"""
                    MISSION : Tracer un Plan d'Action GPS.
                    CONTEXTE : Tu te bases sur {instruction}.
                    DONNÉES : {content_to_process}
                    STRUCTURE REQUISE : Vision long terme, Actions prioritaires Mois 1, Structure & Acquisition Mois 3, Alerte Rouge (Risques).
                    """
                    st.session_state.project["gps"] = model.generate_content(p).text
                    consume_credit()
                st.rerun()
            else:
                st.warning("Veuillez fournir un contenu (pivot ou analyse) pour générer le plan.")

elif st.session_state.current_step == 2:
    st.header("💡 Pivots Stratégiques")
    if not st.session_state.project["analysis"]: st.warning("Faites l'étape 1.")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"], unsafe_allow_html=True)
        with st.popover("➕ Plus de variantes"): 
            ref2 = st.text_area("Orientation...", key="ref_2_v3")
            if st.button("Générer 4-6", key="btn_ref_2_v3"):
                if st.session_state.user['credits'] > 0:
                    p = f"Génère 3 pivots pour {st.session_state.project['idea']}. Orientation: {ref2}."
                    st.session_state.project["pivots"] += f"\n\n{model.generate_content(p).text}"
                    consume_credit(); st.rerun()
        if st.button("➡️ Suivant : Plan d'Action", use_container_width=True, key="next_2_v3"):
            st.session_state.current_step = 3; st.rerun()
    else:
        if st.button("Générer les 3 Pivots (1 crédit)", key="btn_step2_v3", use_container_width=True):
            p = f"3 pivots pour {st.session_state.project['idea']}. Tableau comparatif requis."
            st.session_state.project["pivots"] = model.generate_content(p).text
            consume_credit(); st.rerun()

elif st.session_state.current_step == 3:
    st.header("🗺️ Plan d'Action")
    if not st.session_state.project["pivots"]: st.warning("Faites l'étape 2.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        if st.button("🔄 Recalculer", key="btn_reset_3_v3"): st.session_state.project["gps"] = ""; st.rerun()
    else:
        sel = st.text_area("Pivot choisi :", key="sel_pivot_v3")
        if st.button("Tracer le Plan d'Action (1 crédit)", key="btn_step3_v3", use_container_width=True):
            if sel:
                p = f"Plan d'Action pour : {sel}."
                st.session_state.project["gps"] = model.generate_content(p).text
                consume_credit(); st.rerun()
