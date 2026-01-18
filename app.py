import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Critique & GPS", page_icon="🚀", layout="wide")

# ==========================================
# 🛑 ZONE DE CONFIGURATION (REMPLISSEZ ICI)
# ==========================================

# 1. Vos clés SUPABASE (Collez vos vraies clés entre les guillemets)
SUPABASE_URL = "https://idvkrilkrfpzdmmmxgnj.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkdmtyaWxrcmZwemRtbW14Z25qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzNjY4NTIsImV4cCI6MjA4Mzk0Mjg1Mn0.pmjlyfNbe_4V4j26KeiFgUkNzI9tz9zPY3DwJho_RRU"

# 2. Votre clé GOOGLE GEMINI (Collez votre clé ici)
GOOGLE_API_KEY = "AIzaSyAWxtPV_SzbEHNgQJecfugMZZoXRn0mKUc"

# 3. Votre lien de paiement LEMON SQUEEZY (https://...)
LIEN_PAIEMENT = "https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67"

# ==========================================
# FIN DE LA CONFIGURATION - NE TOUCHEZ PLUS RIEN DESSOUS
# ==========================================

# Connexion aux services
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erreur de configuration des clés : {e}")
    st.stop()

# --- FONCTIONS ---
def get_user_by_code(access_code):
    """Récupère l'utilisateur via son code d'accès"""
    try:
        response = supabase.table("users").select("*").eq("access_code", access_code).execute()
        if response.data:
            return response.data[0]
    except:
        pass
    return None

def decrement_credits(user_id, current_credits):
    """Enlève 1 crédit"""
    try:
        new_credits = max(0, current_credits - 1)
        supabase.table("users").update({"credits": new_credits}).eq("id", user_id).execute()
        return new_credits
    except:
        return current_credits

# --- GESTION CONNEXION ---
if "user" not in st.session_state:
    query_params = st.query_params
    if "access_code" in query_params:
        user = get_user_by_code(query_params["access_code"])
        if user:
            st.session_state["user"] = user
            st.rerun()

# --- INTERFACE ---

# 1. PAS CONNECTÉ
if "user" not in st.session_state:
    st.title("🔐 Accès Réservé")
    st.write("Veuillez utiliser le lien reçu par email.")
    
    code = st.text_input("Ou code manuel :")
    if st.button("Valider"):
        user = get_user_by_code(code)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Code inconnu.")
    
    st.divider()
    st.info("Pas encore de compte ? [3 crédits offerts ici](https://tally.so/r/3xQqjL)")
    st.stop()

# 2. CONNECTÉ (L'APP)
user = st.session_state["user"]
credits = user["credits"]

with st.sidebar:
    st.header("Mon Compte")
    st.write(f"👤 {user['email']}")
    
    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.metric("Crédits", 0, delta="Épuisé", delta_color="inverse")
        st.warning("Recharge nécessaire")
        st.markdown(f"[👉 Recharger (49€)]({LIEN_PAIEMENT})")

    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

st.title("🚀 Générateur IA : Critique & GPS")

if credits > 0:
    prompt = st.text_area("Votre idée :", height=100)
    
    if st.button("Analyser (1 crédit)"):
        if not prompt:
            st.warning("Écrivez une idée !")
        else:
            with st.spinner("Analyse en cours..."):
                try:
                    # Génération Google Gemini
                    response = model.generate_content(
                        f"Analyse l'idée : '{prompt}'. \n"
                        f"1. Rôle : Avocat du Diable (3 critiques). \n"
                        f"2. Rôle : GPS Stratégique (Objectif, Plan, 1ère Action). \n"
                        f"Utilise du Markdown clair."
                    )
                    
                    st.markdown(response.text)
                    
                    # Débit
                    new_credits = decrement_credits(user["id"], credits)
                    user["credits"] = new_credits
                    st.session_state["user"] = user
                    st.success("Terminé !")
                    
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
else:
    st.error("Solde insuffisant. Rechargez via le menu.")
