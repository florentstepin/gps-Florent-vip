import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Architecte (Gemini 2.5)", page_icon="🚀", layout="centered")

# Bouton de secours (en cas de bug de mémoire)
if st.sidebar.button("🔴 RESET MÉMOIRE"):
    st.session_state.clear()
    st.rerun()

# --- 2. INITIALISATION VARIABLES (Anti-Crash) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'audit' not in st.session_state:
    st.session_state.audit = ""
if 'model_name' not in st.session_state:
    st.session_state.model_name = "En attente"
if 'idea' not in st.session_state:
    st.session_state.idea = ""

# --- 3. CONNEXION API ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ Pas de Clé API.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

# --- 4. LE MOTEUR COMPATIBLE (Votre Liste) ---
def get_safe_response(prompt_text):
    """
    On utilise gemini-2.5-flash car il est en haut de votre liste 'API Active'.
    """
    try:
        # C'est le modèle que VOUS avez (vu sur votre capture d'écran)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"❌ ERREUR API : {e}"

# --- 5. LOGIN ---
st.title("🚀 Mode 2.5 Flash")

if not st.session_state.logged_in:
    with st.form("login_form"):
        code = st.text_input("Code VIP", type="password")
        submit = st.form_submit_button("Entrer")
        if submit:
            if code == "VIP2025":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Code faux")
    st.stop()

# --- 6. APPLICATION ---

st.success("✅ Système connecté à Gemini 2.5")

# ÉTAPE 1
if st.session_state.step == 1:
    st.subheader("Test de génération")
    user_idea = st.text_area("Votre idée :", "Formation drone photogrammétrie")
    
    if st.button("Lancer le test"):
        with st.spinner("Gemini 2.5 Flash travaille..."):
            res = get_safe_response(f"Fais une critique très courte (3 points) de ce projet : {user_idea}")
            st.session_state.audit = res
            st.session_state.model_name = "gemini-2.5-flash"
            st.session_state.step = 2
            st.rerun()

# ÉTAPE 2
elif st.session_state.step == 2:
    st.info(f"Réponse générée par : {st.session_state.model_name}")
    st.write(st.session_state.audit)
    
    if st.button("Nouvel Essai"):
        st.session_state.step = 1
        st.rerun()
