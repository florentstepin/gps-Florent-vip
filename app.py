import streamlit as st
from supabase import create_client, Client
from openai import OpenAI

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="IA Critique & GPS",
    page_icon="🚀",
    layout="wide"
)

# --- 1. CONNEXION AUX SERVICES (SECRETS) ---
# Assurez-vous que vos secrets sont bien dans .streamlit/secrets.toml
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    st.error("⚠️ Il manque les clés API dans les secrets (.streamlit/secrets.toml).")
    st.stop()

# Initialisation des clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# --- 2. FONCTIONS UTILITAIRES ---

def get_user_by_code(access_code):
    """Cherche un utilisateur par son code d'accès"""
    try:
        response = supabase.table("users").select("*").eq("access_code", access_code).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erreur de connexion DB: {e}")
        return None

def decrement_credits(user_id, current_credits):
    """Enlève 1 crédit à l'utilisateur"""
    try:
        new_credits = max(0, current_credits - 1)
        supabase.table("users").update({"credits": new_credits}).eq("id", user_id).execute()
        return new_credits
    except Exception as e:
        st.error(f"Erreur lors du débit des crédits: {e}")
        return current_credits

# --- 3. GESTION DE LA SESSION (LOGIN) ---

# Vérification du lien magique (URL)
if "user" not in st.session_state:
    query_params = st.query_params
    if "access_code" in query_params:
        code_url = query_params["access_code"]
        user = get_user_by_code(code_url)
        if user:
            st.session_state["user"] = user
            st.rerun() # Recharger pour nettoyer l'URL

# --- 4. INTERFACE UTILISATEUR ---

# A. SI PAS CONNECTÉ
if "user" not in st.session_state:
    st.title("🔐 Accès Réservé")
    st.markdown("Veuillez utiliser votre **lien magique** reçu par email.")
    
    # Optionnel : Connexion manuelle de secours
    code_input = st.text_input("Ou entrez votre code d'accès ici :")
    if st.button("Se connecter"):
        user = get_user_by_code(code_input)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Code invalide.")
    
    st.markdown("---")
    st.info("Pas encore inscrit ? [Cliquez ici pour obtenir 3 crédits gratuits](https://tally.so/r/Bzp6E4)") # REMPLACEZ PAR VOTRE LIEN TALLY
    st.stop()

# B. SI CONNECTÉ (LE VRAI PROGRAMME)
user = st.session_state["user"]
credits = user["credits"]

# --- SIDEBAR (Infos Compte) ---
with st.sidebar:
    st.header("Mon Compte 👤")
    st.write(f"**Email :** {user['email']}")
    
    # Affichage dynamique des crédits
    if credits > 0:
        st.metric(label="Crédits restants", value=credits, delta="Actif")
    else:
        st.metric(label="Crédits restants", value=0, delta="Épuisé", delta_color="inverse")
        st.error("🚫 Vous n'avez plus de crédits.")
        # LIEN DE PAIEMENT LEMON SQUEEZY
        st.markdown(f"[👉 Recharger mon compte (49€)](https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67)", unsafe_allow_html=True) # REMPLACEZ PAR VOTRE LIEN CHECKOUT LEMON

    st.markdown("---")
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

# --- MAIN CONTENT (L'IA) ---

st.title("🚀 Mon Générateur IA : Critique & GPS")

if credits > 0:
    st.success(f"Bienvenue ! Vous avez {credits} crédits. Prêt à challenger vos idées ?")
    
    user_input = st.text_area("Entrez votre idée, votre projet ou votre problématique ici :", height=150)
    
    if st.button("🔥 Lancer l'analyse (Coût : 1 crédit)"):
        if not user_input:
            st.warning("Veuillez écrire quelque chose d'abord !")
        else:
            with st.spinner("L'Avocat du Diable analyse votre idée..."):
                
                # --- ETAPE 1 : L'AVOCAT DU DIABLE ---
                prompt_avocat = f"""
                Agis comme un "Avocat du Diable" impitoyable mais constructif.
                Analyse l'idée suivante : "{user_input}".
                Identifie 3 failles majeures, 2 risques cachés et 1 biais cognitif potentiel.
                Sois direct, incisif, mais termine par une note encourageante.
                """
                
                response_avocat = client.chat.completions.create(
                    model="gpt-4o-mini", # Ou gpt-3.5-turbo ou gpt-4
                    messages=[{"role": "user", "content": prompt_avocat}]
                )
                analyse_critique = response_avocat.choices[0].message.content
                
                # --- ETAPE 2 : LE SYSTÈME GPS ---
                prompt_gps = f"""
                Agis comme un système GPS stratégique (Goal - Plan - Step).
                Basé sur l'idée : "{user_input}" et les critiques potentielles.
                Donne-moi :
                1. GOAL (L'objectif reformulé et clarifié)
                2. PLAN (La stratégie en 3 grandes phases)
                3. STEP (La toute première action concrète à faire dans les 24h)
                """
                
                response_gps = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_gps}]
                )
                plan_gps = response_gps.choices[0].message.content

                # --- AFFICHAGE DES RÉSULTATS ---
                st.markdown("### 😈 L'Analyse de l'Avocat du Diable")
                st.write(analyse_critique)
                
                st.markdown("---")
                
                st.markdown("### 📍 Le Système GPS (Plan d'Action)")
                st.write(plan_gps)
                
                # --- DEBITER LE CRÉDIT ---
                new_balance = decrement_credits(user["id"], credits)
                
                # Mettre à jour la session pour l'affichage immédiat
                user["credits"] = new_balance
                st.session_state["user"] = user
                
                st.toast("✅ Analyse terminée ! 1 crédit utilisé.", icon="🎉")
                
                # Petit bouton pour rafraichir le compteur visuel si besoin
                if st.button("Nouvelle recherche"):
                    st.rerun()

else:
    st.warning("Vous devez recharger votre compte pour utiliser le générateur.")
    st.info("Le lien de paiement est disponible dans la barre latérale à gauche.")
