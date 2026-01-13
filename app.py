import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION ET NETTOYAGE IMMÉDIAT ---
st.set_page_config(page_title="Architecte (Rescue)", page_icon="🚑", layout="centered")

# Bouton de secours pour nettoyer la mémoire si ça plante
if st.sidebar.button("🔴 RESET TOTAL (Cliquer ici si bug)"):
    st.session_state.clear()
    st.rerun()

# --- 2. INITIALISATION SÉCURISÉE (Anti-Crash) ---
# On initialise TOUTES les variables possibles dès le début
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
if 'pivot' not in st.session_state:
    st.session_state.pivot = ""
if 'plan' not in st.session_state:
    st.session_state.plan = ""
if 'choix' not in st.session_state:
    st.session_state.choix = ""

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

# --- 4. LE MOTEUR "INCASSABLE" ---
def get_safe_response(prompt_text):
    """
    On utilise UNIQUEMENT Gemini 1.5 Flash.
    C'est le modèle le plus stable du monde. Pas d'expérimental, pas de crash.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"❌ ERREUR API : {e}"

# --- 5. INTERFACE LOGIN ---
st.title("🚑 Mode Réparation")

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
    st.stop() # Arrête tout ici si pas connecté

# --- 6. APPLICATION (Une fois connecté) ---

st.success("✅ Connexion réussie. Système stable.")

# ÉTAPE 1 : L'INPUT
if st.session_state.step == 1:
    st.subheader("Test de génération")
    user_idea = st.text_area("Votre idée :", "Vente de drones")
    
    if st.button("Lancer le test"):
        with st.spinner("Appel à Gemini 1.5 Flash..."):
            res = get_safe_response(f"Analyse critique courte de : {user_idea}")
            st.session_state.audit = res
            st.session_state.model_name = "gemini-1.5-flash"
            st.session_state.idea = user_idea
            st.session_state.step = 2
            st.rerun()

# ÉTAPE 2 : RÉSULTAT
elif st.session_state.step == 2:
    st.info(f"Modèle utilisé : {st.session_state.model_name}")
    st.write(st.session_state.audit)
    
    if st.button("Recommencer"):
        st.session_state.step = 1
        st.rerun()
