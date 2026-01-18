import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Générateur Stratégique IA", page_icon="🚀", layout="wide")

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

# 4. Choix du Modèle
# Si 'gemini-2.5-flash' fonctionnait, laissez tel quel.
# En cas d'erreur 404, remplacez par 'gemini-3.0' ou 'gemini-pro'.
MODEL_NAME = 'gemini-2.5-flash' 

# ==============================================================================
# FIN DE LA CONFIGURATION. LE RESTE EST AUTOMATIQUE.
# ==============================================================================

# --- CONNEXION AUX SERVICES ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"❌ Erreur critique de connexion : {e}")
    st.stop()

# --- FONCTIONS UTILITAIRES ---

def get_user_by_code(access_code):
    """Récupère l'utilisateur en base de données"""
    try:
        # On nettoie le code d'éventuels espaces
        access_code = access_code.strip()
        response = supabase.table("users").select("*").eq("access_code", access_code).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        # En production, on peut masquer l'erreur exacte
        pass
    return None

def decrement_credits(user_id, current_credits):
    """Débite 1 crédit à l'utilisateur"""
    try:
        new_credits = max(0, current_credits - 1)
        supabase.table("users").update({"credits": new_credits}).eq("id", user_id).execute()
        return new_credits
    except:
        return current_credits

# --- GESTION DU LOGIN (ROBUSTE) ---

if "user" not in st.session_state:
    # On regarde dans l'URL
    qp = st.query_params
    # On accepte 'code' (Email) OU 'access_code' (Anciens liens)
    code_url = qp.get("code") or qp.get("access_code")
    
    if code_url:
        user = get_user_by_code(code_url)
        if user:
            st.session_state["user"] = user
            st.rerun()

# --- INTERFACE ---

# CAS 1 : UTILISATEUR NON CONNECTÉ
if "user" not in st.session_state:
    st.title("🔐 Accès Espace VIP")
    st.markdown("### Veuillez vous identifier")
    st.write("Utilisez le lien magique reçu par email pour accéder à votre espace.")
    
    # Connexion de secours
    col1, col2 = st.columns([3, 1])
    with col1:
        code_input = st.text_input("Ou entrez votre code personnel ici :", placeholder="Ex: a1b2c3d4...")
    with col2:
        st.write("") # Espace
        st.write("") # Espace
        if st.button("Valider l'accès"):
            user = get_user_by_code(code_input)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Code non reconnu.")
            
    st.divider()
    st.info("Pas encore de compte ? [Obtenez 3 crédits gratuits ici](https://tally.so/r/3xQqjL)")
    st.stop()

# CAS 2 : UTILISATEUR CONNECTÉ (L'APPLICATION)
user = st.session_state["user"]
credits = user["credits"]

# --- BARRE LATÉRALE (Compte & Paiement) ---
with st.sidebar:
    st.header("👤 Mon Espace")
    st.write(f"Email : **{user['email']}**")
    
    st.divider()
    
    if credits > 0:
        st.metric(label="Crédits disponibles", value=credits)
        st.success("✅ Compte actif")
    else:
        st.metric(label="Crédits", value=0)
        st.error("⛔ Solde épuisé")
        st.markdown("### 🚀 Passez au niveau supérieur")
        st.markdown("Pour continuer à générer des stratégies, rechargez votre compte.")
        # LE LIEN HIGH TICKET / RECHARGE
        st.markdown(f"👉 **[Recharger maintenant]({LIEN_PAIEMENT})**", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Se déconnecter"):
        del st.session_state["user"]
        st.rerun()

# --- ZONE PRINCIPALE : L'INTELLIGENCE ARTIFICIELLE ---
st.title("🧠 Générateur de Stratégie & Critique")
st.markdown("Transformez une idée brute en plan d'action bétonné.")

if credits > 0:
    user_input = st.text_area("Décrivez votre idée, projet ou offre :", height=150, placeholder="Ex: Je veux lancer une formation sur la permaculture pour les citadins...")
    
    if st.button("Lancer l'analyse complète (1 crédit)"):
        if not user_input:
            st.warning("Veuillez entrer une idée pour commencer.")
        else:
            with st.spinner("L'IA analyse votre projet sous tous les angles..."):
                try:
                    # 1. Construction du Prompt "Tout-en-un" pour garantir la cohérence
                    prompt_complet = f"""
                    Tu es un consultant business d'élite. Analyse l'idée suivante : "{user_input}".
                    
                    ---
                    PARTIE 1 : L'AVOCAT DU DIABLE 😈
                    Sois impitoyable mais juste. Identifie :
                    1. La faille mortelle (pourquoi ça peut échouer).
                    2. Un biais cognitif du créateur.
                    3. Un risque caché marché/concurrentiel.
                    
                    ---
                    PARTIE 2 : LE SYSTÈME GPS (Goal - Plan - Step) 📍
                    Transforme les critiques en actions :
                    1. GOAL : Reformule l'objectif pour qu'il soit SMART et ambitieux.
                    2. PLAN : Donne 3 grandes étapes chronologiques.
                    3. STEP : La toute première action à faire dans l'heure qui suit (Action immédiate).
                    
                    Utilise une mise en forme Markdown propre (Gras, Titres, Listes).
                    """
                    
                    # 2. Appel à l'IA
                    response = model.generate_content(prompt_complet)
                    
                    # 3. Affichage du résultat
                    st.markdown(response.text)
                    
                    # 4. Débit du crédit (UNIQUEMENT si ça a marché)
                    new_solde = decrement_credits(user["id"], credits)
                    user["credits"] = new_solde
                    st.session_state["user"] = user
                    
                    st.toast("Analyse réussie ! Crédit débité.", icon="🎉")
                    
                except Exception as e:
                    st.error(f"Une erreur est survenue lors de l'analyse : {e}")
                    st.info("Si l'erreur persiste, vérifiez le nom du modèle ou votre clé API.")

else:
    # Ecran quand 0 crédits
    st.warning("Vous avez utilisé toutes vos explorations gratuites.")
    st.markdown(f"### 👉 [Cliquez ici pour débloquer l'accès illimité / Recharger]({LIEN_PAIEMENT})")
