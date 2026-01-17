import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION SUPABASE (CORRIGÉE) ---
# On gère votre configuration spécifique ["supabase"]["url"]
try:
    # On regarde si les secrets sont rangés dans un dossier "supabase"
    if "supabase" in st.secrets:
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
    # Sinon, on tente la méthode standard (au cas où)
    else:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception as e:
    st.error(f"Erreur de connexion : Les secrets sont introuvables. Détail: {e}")
    st.stop()

# Connexion à la base de données
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 2. CONFIGURATION LEMON SQUEEZY ---
# 👇 REMPLACEZ CECI PAR VOTRE VRAI LIEN
LEMON_SQUEEZY_LINK = "https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67" 

# --- 3. LOGIQUE PRINCIPALE ---

# Récupération du code dans l'URL
query_params = st.query_params
access_code = query_params.get("code", None)

st.set_page_config(page_title="Mon App VIP", page_icon="🚀")

# Si aucun code n'est présent
if not access_code:
    st.warning("⛔ Accès refusé. Veuillez utiliser le lien personnel reçu par email.")
    st.stop()

# On interroge Supabase
try:
    response = supabase.table("users").select("*").eq("access_code", access_code).execute()
except Exception as e:
    st.error("Erreur de communication avec la base de données.")
    st.stop()

# Si le code n'existe pas
if not response.data:
    st.error("❌ Ce code d'accès est invalide ou n'existe pas.")
    st.stop()

# --- 4. GESTION DE L'UTILISATEUR ---
user = response.data[0]
credits_restants = user.get('credits', 0)
user_email = user.get('email', 'Email inconnu')

# Barre latérale
with st.sidebar:
    st.header("Mon Compte 👤")
    st.write(f"Email : **{user_email}**")
    
    if credits_restants > 0:
        st.metric(label="Crédits restants", value=credits_restants, delta="Actif")
    else:
        st.metric(label="Crédits restants", value=0, delta="Épuisé", delta_color="inverse")
    
    st.divider()
    st.caption("Chaque génération coûte 1 crédit.")

# --- 5. L'APPLICATION ---

st.title("🚀 Mon Générateur IA")

if credits_restants > 0:
    # 🟢 ZONE AVEC CRÉDITS
    st.success(f"Bienvenue ! Vous avez {credits_restants} crédits.")
    
    user_input = st.text_area("Entrez votre prompt ici :", height=150)
    
    if st.button("✨ Lancer la génération", type="primary"):
        if not user_input:
            st.warning("Écrivez quelque chose d'abord !")
        else:
            with st.spinner("L'IA travaille..."):
                # --- ICI VOTRE CODE IA ---
                # import time
                # time.sleep(2)
                st.write(f"✅ Résultat : {user_input}")
                st.balloons()
                
                # --- DÉCOMPTE DU CRÉDIT ---
                new_credits = credits_restants - 1
                supabase.table("users").update({"credits": new_credits}).eq("access_code", access_code).execute()
                
                st.success("Génération terminée ! -1 Crédit.")
                st.rerun() # Rafraîchit la page immédiatement

else:
    # 🔴 ZONE 0 CRÉDIT
    st.error("⏳ Vous avez épuisé vos 3 crédits gratuits !")
    
    st.markdown("### Continuez l'aventure en illimité")
    
    # Lien de paiement intelligent
    checkout_url = f"{LEMON_SQUEEZY_LINK}?checkout[email]={user_email}"
    
    st.link_button("💎 Recharger mon compte", checkout_url, type="primary")
