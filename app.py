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
GOOGLE_API_KEY = "AIzaSyDsYZxJmLnLtfeA60IDDLnRv9Sm8cMdYdw"

# 3. Votre lien de paiement LEMON SQUEEZY (https://...)
LIEN_PAIEMENT = "https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67"

# ==============================================================================
# CONFIGURATION IA (Version 2.5)
# ==============================================================================
# On force l'appel au modèle 2.5 comme vous l'aviez avant.
MODEL_NAME = 'gemini-2.5-flash' 

# --- CONNEXION AUX SERVICES ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"❌ Erreur de configuration : {e}")
    st.stop()

# --- FONCTIONS TECHNIQUES ---

def get_user_by_code(access_code):
    try:
        # Recherche flexible (code ou access_code)
        response = supabase.table("users").select("*").eq("access_code", access_code).execute()
        if response.data: return response.data[0]
    except: pass
    return None

def decrement_credits(user_id, current_credits):
    try:
        new_credits = max(0, current_credits - 1)
        supabase.table("users").update({"credits": new_credits}).eq("id", user_id).execute()
        return new_credits
    except: return current_credits

# --- GESTION LOGIN ---
if "user" not in st.session_state:
    qp = st.query_params
    code_url = qp.get("code") or qp.get("access_code")
    
    if code_url:
        user = get_user_by_code(code_url)
        if user:
            st.session_state["user"] = user
            st.rerun()

# --- INTERFACE ---

# 1. NON CONNECTÉ
if "user" not in st.session_state:
    st.title("🔐 Accès Réservé")
    st.markdown("Veuillez utiliser le lien reçu par email.")
    
    code_input = st.text_input("Ou code manuel :")
    if st.button("Valider"):
        user = get_user_by_code(code_input)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Code inconnu.")
            
    st.divider()
    st.info("Pas encore inscrit ? [3 crédits offerts ici](https://tally.so/r/3xQqjL)")
    st.stop()

# 2. CONNECTÉ
user = st.session_state["user"]
credits = user["credits"]

with st.sidebar:
    st.header("Mon Compte")
    st.write(f"👤 {user['email']}")
    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.metric("Crédits", 0, delta="Épuisé", delta_color="inverse")
        st.markdown(f"👉 **[Recharger (49€)]({LIEN_PAIEMENT})**")
    
    st.divider()
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

# --- ZONE IA ---
st.title(f"🚀 Générateur IA")

if credits > 0:
    user_input = st.text_area("Votre idée :", height=100)
    
    if st.button("Analyser (1 crédit)"):
        if not user_input:
            st.warning("Écrivez une idée !")
        else:
            with st.spinner(f"Analyse en cours..."):
                try:
                    prompt = f"""
                    Analyse l'idée : '{user_input}'.
                    1. AVOCAT DU DIABLE : 3 failles critiques, 2 risques.
                    2. GPS STRATÉGIQUE : Objectif, Plan (3 étapes), 1ère Action.
                    Utilise du Markdown.
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # Débit
                    new_c = decrement_credits(user["id"], credits)
                    user["credits"] = new_c
                    st.session_state["user"] = user
                    st.success("Terminé !")
                    
                except Exception as e:
                    st.error(f"Erreur API : {e}")
else:
    st.error("Solde épuisé.")
    st.markdown(f"**[Recharger ici]({LIEN_PAIEMENT})**")
