import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION SUPABASE ---
# Assurez-vous que vos secrets sont bien dans .streamlit/secrets.toml sur Streamlit Cloud
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("Erreur : Les secrets Supabase (URL et KEY) sont introuvables.")
    st.stop()

# Connexion à la base de données
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 2. CONFIGURATION LEMON SQUEEZY ---
# 👇 REMPLACEZ CECI PAR VOTRE VRAI LIEN LEMON SQUEEZY CHECKOUT
LEMON_SQUEEZY_LINK = "https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67" 

# --- 3. LOGIQUE PRINCIPALE ---

# Récupération du code dans l'URL (ex: ?code=XYZ)
query_params = st.query_params
access_code = query_params.get("code", None)

# Configuration de la page
st.set_page_config(page_title="Mon App VIP", page_icon="🚀")

# Si aucun code n'est présent dans l'URL
if not access_code:
    st.warning("⛔ Accès refusé. Veuillez utiliser le lien personnel reçu par email.")
    st.stop()

# On interroge Supabase pour trouver l'utilisateur
response = supabase.table("users").select("*").eq("access_code", access_code).execute()

# Si le code n'existe pas dans la base
if not response.data:
    st.error("❌ Ce code d'accès est invalide ou n'existe pas.")
    st.stop()

# --- 4. GESTION DE L'UTILISATEUR ---
user = response.data[0]
credits_restants = user['credits']
user_email = user['email']

# Barre latérale pour afficher les infos (Stylé)
with st.sidebar:
    st.header("Mon Compte 👤")
    st.write(f"Email : **{user_email}**")
    
    if credits_restants > 0:
        st.metric(label="Crédits restants", value=credits_restants, delta="Actif")
    else:
        st.metric(label="Crédits restants", value=0, delta="Épuisé", delta_color="inverse")
    
    st.divider()
    st.caption("Chaque génération coûte 1 crédit.")

# --- 5. LE CŒUR DE L'APPLICATION ---

st.title("🚀 Mon Générateur IA")

if credits_restants > 0:
    # ============================================================
    # 🟢 ZONE ACTIVE : L'utilisateur a des crédits
    # C'est ICI que vous mettez vos champs (Input, Selectbox...)
    # ============================================================
    
    st.success(f"Bienvenue ! Vous avez {credits_restants} crédits disponibles.")
    
    # --- Exemple de formulaire (À REMPLACER PAR LE VÔTRE) ---
    user_input = st.text_area("Entrez votre prompt ici :", height=150)
    
    # Le Bouton "Magique"
    if st.button("✨ Lancer la génération", type="primary"):
        if not user_input:
            st.warning("Veuillez écrire quelque chose avant de lancer.")
        else:
            with st.spinner("L'IA travaille pour vous..."):
                
                # ------------------------------------------------
                # A. VOTRE CODE IA VIENT ICI (Appel API, Calculs...)
                # ------------------------------------------------
                # import time
                # time.sleep(2) # Simulation
                st.write(f"✅ Résultat pour : {user_input}")
                st.balloons() # Petit effet sympa
                
                # ------------------------------------------------
                # B. DÉDUCTION DU CRÉDIT (CRITIQUE)
                # ------------------------------------------------
                new_credits = credits_restants - 1
                
                # Mise à jour Supabase
                supabase.table("users").update({"credits": new_credits}).eq("access_code", access_code).execute()
                
                # Message et rechargement pour mettre à jour l'affichage
                st.success("Génération terminée ! 1 crédit utilisé.")
                # On force le rechargement de la page pour actualiser le compteur
                st.rerun()

else:
    # ============================================================
    # 🔴 ZONE BLOQUÉE : 0 Crédit
    # ============================================================
    st.error("⏳ Vous avez épuisé vos 3 crédits gratuits !")
    
    st.markdown("""
    ### Vous avez aimé l'outil ?
    Pour continuer à l'utiliser sans limite (ou recharger votre compte), 
    passez à la version complète.
    """)
    
    # Construction du lien personnalisé (avec l'email pré-rempli)
    # Cela permet à Lemon Squeezy de savoir QUI paie
    checkout_url = f"{LEMON_SQUEEZY_LINK}?checkout[email]={user_email}"
    
    st.link_button("💎 Recharger mon compte maintenant", checkout_url, type="primary")
