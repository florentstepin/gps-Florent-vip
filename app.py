import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Stratège IA V7", page_icon="🎯", layout="wide")

# ==============================================================================
# 🔐 RÉCUPÉRATION DES CLÉS
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    LIEN_RECHARGE = st.secrets["LIEN_RECHARGE"]
    LIEN_ARCHITECTE = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    MODEL_NAME = 'gemini-2.5-pro'
except Exception as e:
    st.error(f"❌ Erreur secrets : {e}")
    st.stop()

# --- CONNEXIONS ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"❌ Erreur connexion : {e}")
    st.stop()

# --- GESTION ÉTAT (STATE MACHINE) ---
# 1. Niveau maximum débloqué (1, 2 ou 3)
if "max_step" not in st.session_state: st.session_state.max_step = 1
# 2. Vue actuelle (Ce qu'on regarde : "1. Analyse", etc.)
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"

# Stockage des données
if "analysis_data" not in st.session_state: st.session_state.analysis_data = {}
if "selected_pivot" not in st.session_state: st.session_state.selected_pivot = None
if "initial_idea" not in st.session_state: st.session_state.initial_idea = ""

# --- FONCTIONS ---

def get_user(code):
    try:
        code = str(code).strip()
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data: return res.data[0]
    except: pass
    return None

def debit_credit_atomic(user_obj, current):
    """Débite et met à jour l'affichage immédiatement"""
    try:
        user_id = user_obj.get("uuid") or user_obj.get("id")
        col_name = "uuid" if user_obj.get("uuid") else "id"
        
        new_balance = max(0, current - 1)
        supabase.table("users").update({"credits": new_balance}).eq(col_name, user_id).execute()
        
        # Mise à jour locale forcée
        st.session_state["user"]["credits"] = new_balance
        return new_balance
    except Exception as e:
        st.error(f"Erreur débit : {e}")
        return current

def save_json():
    data = {
        "max_step": st.session_state.max_step,
        "idea": st.session_state.initial_idea,
        "analysis": st.session_state.analysis_data,
        "pivot": st.session_state.selected_pivot
    }
    return json.dumps(data, indent=4)

def load_json(uploaded_file):
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.session_state.initial_idea = data.get("idea", "")
            st.session_state.analysis_data = data.get("analysis", {})
            st.session_state.selected_pivot = data.get("pivot", None)
            
            # Restauration intelligente
            saved_step = data.get("max_step", 1)
            # On s'assure que le step est cohérent avec les données
            if "step3" in st.session_state.analysis_data: saved_step = 3
            elif "step2" in st.session_state.analysis_data: saved_step = 2
            
            st.session_state.max_step = saved_step
            # On remet la vue au début pour que l'utilisateur voit son dossier
            st.session_state.current_view = "1. Analyse"
                
            st.success("📂 Dossier chargé !")
            time.sleep(0.5)
            st.rerun()
        except: st.error("Fichier invalide")

# --- LOGIN ---
if "user" not in st.session_state:
    qp = st.query_params
    c_url = qp.get("code") or qp.get("access_code")
    if c_url:
        u = get_user(c_url)
        if u:
            st.session_state["user"] = u
            st.rerun()
            
    st.title("🔐 Accès Stratège 2026")
    c_input = st.text_input("Code d'accès :")
    if st.button("Valider"):
        u = get_user(c_input)
        if u:
            st.session_state["user"] = u
            st.rerun()
    st.stop()

# --- APP START ---
user = st.session_state["user"]
credits = user.get("credits", 0)

# ================= SIDEBAR (NAVIGATION) =================
with st.sidebar:
    st.header("Mon Compte")
    if credits > 0:
        st.metric("Crédits Dispo", credits)
    else:
        st.error("Solde épuisé")
        st.markdown(f"👉 **[Recharger]({LIEN_RECHARGE})**")

    st.divider()
    
    st.markdown("### 📂 Navigation")
    
    # Construction de la liste des pages accessibles
    # On a toujours accès à l'étape 1
    options_nav = ["1. Analyse"]
    
    # Si étape 2 débloquée (soit par historique, soit par génération récente)
    if st.session_state.max_step >= 2 or "step2" in st.session_state.analysis_data:
        options_nav.append("2. Pivots")
        st.session_state.max_step = max(st.session_state.max_step, 2)
        
    # Si étape 3 débloquée
    if st.session_state.max_step >= 3 or "step3" in st.session_state.analysis_data:
        options_nav.append("3. GPS")
        st.session_state.max_step = max(st.session_state.max_step, 3)
    
    # --- LOGIQUE CRITIQUE DE NAVIGATION ---
    # On détermine l'index à afficher dans le Radio Bouton
    # Par défaut, on cherche où est "current_view" dans la liste
    try:
        index_actuel = options_nav.index(st.session_state.current_view)
    except ValueError:
        index_actuel = 0 # Sécurité si la vue n'existe pas
        
    # Le Widget Radio
    choix_nav = st.radio("Aller à :", options_nav, index=index_actuel)
    
    # Si l'utilisateur clique sur le radio, on met à jour la vue
    if choix_nav != st.session_state.current_view:
        st.session_state.current_view = choix_nav
        st.rerun()

    affichage_actuel = int(st.session_state.current_view.split(".")[0])

    st.divider()
    st.info("💎 **Expertise Humaine**")
    st.link_button("Réserver un Audit", LIEN_ARCHITECTE, type="primary")
    
    st.divider()
    st.download_button("💾 Sauvegarder", save_json(), "projet.json", "application/json")
    up = st.file_uploader("📤 Charger", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

# ================= MAIN CONTENT =================
st.title(f"🧠 Stratège IA")
st.progress(affichage_actuel / 3)

# PHASE 1 : ANALYSE
if affichage_actuel == 1:
    st.subheader("1️⃣ L'Avocat du Diable")
    
    if "step1" in st.session_state.analysis_data:
        st.info(f"Projet : {st.session_state.initial_idea}")
        st.markdown(st.session_state.analysis_data["step1"])
        
        # --- BOUTONS NAVIGATION ---
        st.divider()
        col_next, col_retry = st.columns([2, 1])
        
        with col_next:
            # Bouton pour aller à la suite MANUELLEMENT
            if st.button("➡️ Passer à l'étape 2 : Les Pivots", type="primary"):
                st.session_state.max_step = 2
                st.session_state.current_view = "2. Pivots" # C'est ici qu'on force le changement de vue
                st.rerun()
                
        with col_retry:
             with st.expander("🔄 Relancer (1 crédit)"):
                new_txt = st.text_area("Nouvelle version :", value=st.session_state.initial_idea)
                if st.button("Relancer l'analyse"):
                    if credits > 0:
                        st.session_state.initial_idea = new_txt
                        # Nettoyage du futur
                        st.session_state.analysis_data.pop("step2", None)
                        st.session_state.analysis_data.pop("step3", None)
                        st.session_state.max_step = 1 # On revient au niveau 1
                        
                        with st.spinner("Analyse V2..."):
                            res = model.generate_content(f"Analyse critique (Thinking mode) : {new_txt}")
                            st.session_state.analysis_data["step1"] = res.text
                            # ON RESTE SUR LA VUE 1
                            st.session_state.current_view = "1. Analyse"
                            debit_credit_atomic(user, credits)
                            st.rerun()
                    else: st.error("Crédit insuffisant")

    else:
        # Premier démarrage
        if credits > 0:
            txt = st.text_area("Votre idée :", value=st.session_state.initial_idea, height=150)
            if st.button("Lancer l'analyse (1 crédit)"):
                if txt:
                    st.session_state.initial_idea = txt
                    with st.spinner("Réflexion stratégique..."):
                        prompt = f"""Expert Stratège. Analyse : "{txt}".
                        Output Markdown: 1. Context 2. 3 Failles 3. Biais 4. Verdict 5. Justification"""
                        res = model.generate_content(prompt)
                        st.session_state.analysis_data["step1"] = res.text
                        
                        # IMPORTANT : On débloque le niveau 2, MAIS on reste sur la vue 1
                        st.session_state.max_step = 2 
                        st.session_state.current_view = "1. Analyse"
                        
                        debit_credit_atomic(user, credits)
                        st.rerun()
        else: st.error("Rechargez vos crédits.")

# PHASE 2 : PIVOTS
elif affichage_actuel == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    
    # Génération automatique si on arrive ici sans données
    if "step2" not in st.session_state.analysis_data:
        with st.spinner("Génération des pivots..."):
             res = model.generate_content(f"3 Pivots pour : {st.session_state.initial_idea}")
             st.session_state.analysis_data["step2"] = res.text
             st.rerun() # On recharge pour afficher le résultat
    
    # Affichage
    if "step2" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step2"])
        
        st.divider()
        st.markdown("### 🎯 Choix Stratégique")
        
        val_defaut = 0
        opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
        if st.session_state.selected_pivot in opts: val_defaut = opts.index(st.session_state.selected_pivot)
            
        # Widget radio avec clé unique pour ne pas perdre l'état
        ch = st.radio("Sur quelle stratégie part-on ?", opts, index=val_defaut, key="pivot_radio")
        
        if st.button("Valider ce choix et Aller au GPS", type="primary"):
            st.session_state.selected_pivot = ch
            
            # Nettoyage si changement
            if "step3" in st.session_state.analysis_data:
                del st.session_state.analysis_data["step3"]
            
            # Navigation explicite
            st.session_state.max_step = 3
            st.session_state.current_view = "
