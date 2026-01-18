import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="IA Critique & GPS",
    page_icon="🚀",
    layout="wide"
)

# --- 1. RÉCUPÉRATION DES SECRETS (Existants) ---
# Le code va chercher vos clés actuelles dans .streamlit/secrets.toml
# Il ne faut RIEN changer ici si cela marchait avant.
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    # On cherche la clé Google. Si elle s'appelle différemment dans vos secrets
    # (ex: GEMINI_API_KEY), modifiez juste le nom entre guillemets ci-dessous.
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error(f"Erreur de secrets : {e}. Vérifiez votre fichier .streamlit/secrets.toml")
    st.stop()

# Connexion Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Connexion Google Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Modèle rapide et efficace

# --- 2. FONCTIONS UTILITAIRES ---

def get_user_by_code(access_code):
    """Récupère l'utilisateur via son code d'accès unique"""
    try:
        response = supabase.table("users").select("*").eq("access_code", access_code).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erreur DB (Recherche): {e}")
        return None

def decrement_credits(user_id, current_credits):
    """Enlève 1 crédit après usage"""
    try:
        new_credits = max(0, current_credits - 1)
        supabase.table("users").update({"credits": new_credits}).eq("id", user_id).execute()
        return new_credits
    except Exception as e:
        st.error(f"Erreur DB (Débit): {e}")
        return current_credits

# --- 3. GESTION DE LA CONNEXION (URL MAGIC LINK) ---

if "user" not in st.session_state:
    query_params = st.query_params
    if "access_code" in query_params:
        code_url = query_params["access_code"]
        user = get_user_by_code(code_url)
        if user:
            st.session_state["user"] = user
            st.rerun()

# --- 4. INTERFACE UTILISATEUR ---

# CAS A : PAS CONNECTÉ
if "user" not in st.session_state:
    st.title("🔐 Accès Réservé")
    st.write("Veuillez utiliser le lien reçu par email.")
    
    # Connexion de secours
    code_input = st.text_input("Ou entrez votre code ici :")
    if st.button("Valider"):
        user = get_user_by_code(code_input)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Code inconnu.")
    
    st.markdown("---")
    # LIEN TALLY (Déjà rempli pour vous)
    st.info("Pas encore de compte ? [3 crédits offerts ici](https://tally.so/r/3xQqjL)")
    st.stop()

# CAS B : CONNECTÉ (L'APPLICATION)
user = st.session_state["user"]
credits = user["credits"]

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("Mon Compte")
    st.write(f"👤 {user['email']}")
    
    if credits > 0:
        st.metric("Crédits", credits, delta="Disponible")
    else:
        st.metric("Crédits", 0, delta="Épuisé", delta_color="inverse")
        st.warning("Plus de crédits !")
        
        # --- 🛑 ZONE À MODIFIER CI-DESSOUS ---
        # Remplacez le lien entre parenthèses par votre lien Lemon Squeezy
        st.markdown("[👉 Recharger (49€)](https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67)", unsafe_allow_html=True)
        # -------------------------------------

    st.divider()
    if st.button("Se déconnecter"):
        del st.session_state["user"]
        st.rerun()

# --- CŒUR DE L'APP (IA GOOGLE) ---
st.title("🚀 Générateur IA : Critique & GPS")

if credits > 0:
    user_input = st.text_area("Votre idée ou projet :", height=150)
    
    if st.button("Lancer l'analyse (1 crédit)"):
        if not user_input:
            st.warning("Écrivez quelque chose d'abord !")
        else:
            with st.spinner("Analyse par Google Gemini en cours..."):
                try:
                    # 1. Avocat du Diable
                    prompt_critique = f"Agis comme un critique constructif. Trouve 3 failles et 2 risques pour cette idée : '{user_input}'."
                    res_critique = model.generate_content(prompt_critique)
                    
                    # 2. GPS
                    prompt_gps = f"Agis comme un stratège. Donne un Objectif, un Plan en 3 étapes et la 1ère action pour : '{user_input}'."
                    res_gps = model.generate_content(prompt_gps)
                    
                    # 3. Affichage
                    st.subheader("😈 Analyse Critique")
                    st.write(res_critique.text)
                    st.divider()
                    st.subheader("📍 Plan GPS")
                    st.write(res_gps.text)
                    
                    # 4. Débit Crédit
                    new_solde = decrement_credits(user["id"], credits)
                    user["credits"] = new_solde
                    st.session_state["user"] = user
                    st.toast("Terminé ! Crédit débité.", icon="✅")
                    
                except Exception as e:
                    st.error(f"Erreur lors de la génération : {e}")

else:
    st.error("Vous devez recharger votre compte pour utiliser l'IA.")
