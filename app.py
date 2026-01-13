import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="L'Architecte de Projet", page_icon="🏗️")

# --- 1. CONNEXION GEMINI (Votre point fort) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Clé API manquante dans les Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Erreur de connexion IA : {e}")

# --- 2. LES PROMPTS INTELLIGENTS (Vos PDF) ---
PROMPT_AUDIT = """
Rôle : Tu es un Ingénieur en Stratégie (Audit D.U.R.).
Analyse cette idée : {user_idea}
Donne un score sur 10 pour : Douleur, Urgence, Reconnu.
Donne un verdict : GO ou NO-GO.
"""

PROMPT_PIVOT = """
Génère 5 angles d'attaque radicaux (Pivots) pour cette idée : {user_idea}.
Format : Liste à puces.
"""

PROMPT_PLAN = """
Crée un plan d'action sur 7 jours pour lancer ce projet : {selected_angle}.
"""

# --- 3. INTERFACE UTILISATEUR ---
st.title("🏗️ L'Architecte de Projet")
st.markdown("### L'outil de validation par l'Intelligence Artificielle")

# --- A. LE GATEKEEPER (Login Simplifié) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login"):
        st.info("🔒 Accès Sécurisé")
        # On remplace Google Sheets par un code simple pour l'instant
        code = st.text_input("Entrez le Code d'Accès :", type="password")
        submit = st.form_submit_button("Entrer")
        
        if submit:
            if code == "VIP2025": # <--- VOTRE MOT DE PASSE TEMPORAIRE
                st.session_state.logged_in = True
                st.success("Accès Autorisé.")
                st.rerun()
            else:
                st.error("Code invalide.")
    st.stop()

# --- B. L'ATELIER (Une fois connecté) ---
if st.sidebar.button("Déconnexion"):
    st.session_state.logged_in = False
    st.rerun()

st.info("✅ Système connecté à Gemini Pro")

# Étape 1 : L'Idée
idea = st.text_area("Quelle est votre idée de business ?", height=100)
launch_btn = st.button("Lancer l'Audit D.U.R. 💥")

if launch_btn and idea:
    with st.spinner("L'Architecte analyse votre marché..."):
        # Appel réel à Gemini
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(PROMPT_AUDIT.format(user_idea=idea))
        
        st.markdown("---")
        st.subheader("Résultat de l'Audit")
        st.write(response.text)
        
        # On sauvegarde pour la suite
        st.session_state.last_result = response.text

# Bouton de suite (fictif pour l'instant, pour tester l'interface)
if "last_result" in st.session_state:
    st.button("👉 Passer à la phase Pivot (Bientôt disponible)")
