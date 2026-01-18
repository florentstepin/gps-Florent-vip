import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Stratège IA V5", page_icon="⚡", layout="wide")

# ==============================================================================
# 🔐 RÉCUPÉRATION SÉCURISÉE DES CLÉS
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

# --- GESTION ÉTAT ---
if "step" not in st.session_state: st.session_state.step = 1
if "analysis_data" not in st.session_state: st.session_state.analysis_data = {}
if "selected_pivot" not in st.session_state: st.session_state.selected_pivot = None
if "initial_idea" not in st.session_state: st.session_state.initial_idea = ""
# Force l'affichage du menu si des données existent
if "step3" in st.session_state.analysis_data: st.session_state.step = 3
elif "step2" in st.session_state.analysis_data: st.session_state.step = 2

# --- FONCTIONS ---

def get_user(code):
    try:
        code = str(code).strip()
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data: return res.data[0]
    except: pass
    return None

def debit_credit_force(user_obj, current):
    """Débite et force l'interface à se mettre à jour"""
    try:
        # 1. Récupération ID (UUID ou ID)
        user_id = user_obj.get("uuid") or user_obj.get("id")
        col_name = "uuid" if user_obj.get("uuid") else "id"
        
        if not user_id:
            st.error("⚠️ Erreur Technique : ID Utilisateur introuvable. Le débit n'a pas pu se faire.")
            return current

        # 2. Calcul
        new_balance = max(0, current - 1)
        
        # 3. Update Supabase
        supabase.table("users").update({"credits": new_balance}).eq(col_name, user_id).execute()
        
        # 4. FORÇAGE DE LA SESSION LOCALE (C'est ici que ça bloquait)
        st.session_state["user"]["credits"] = new_balance
        
        return new_balance
    except Exception as e:
        st.error(f"Erreur débit : {e}")
        return current

def save_json():
    data = {
        "step": st.session_state.step,
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
            
            # Reconstruction intelligente de l'étape
            if "step3" in st.session_state.analysis_data:
                st.session_state.step = 3
            elif "step2" in st.session_state.analysis_data:
                st.session_state.step = 2
            else:
                st.session_state.step = 1
                
            st.success("📂 Dossier chargé ! Le menu à gauche s'est mis à jour.")
            time.sleep(1)
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

# ================= SIDEBAR (MENU GAUCHE) =================
with st.sidebar:
    st.header("Mon Compte")
    
    # Debug ID (Pour vérifier pourquoi ça bloque)
    user_id_debug = user.get("uuid") or user.get("id")
    if not user_id_debug:
        st.warning("⚠️ ID introuvable (Crédits bloqués)")
    
    if credits > 0:
        st.metric("Crédits Dispo", credits)
    else:
        st.error("Solde épuisé")
        st.markdown(f"👉 **[Recharger]({LIEN_RECHARGE})**")

    st.divider()
    
    # --- NAVIGATION FORCÉE ---
    st.markdown("### 📂 Navigation Dossier")
    
    # Logique : Si j'ai des données Step 2, j'affiche le bouton Step 2
    has_step1 = "step1" in st.session_state.analysis_data
    has_step2 = "step2" in st.session_state.analysis_data
    has_step3 = "step3" in st.session_state.analysis_data
    
    options_nav = ["1. Analyse"]
    if has_step2 or st.session_state.step >= 2: options_nav.append("2. Pivots")
    if has_step3 or st.session_state.step >= 3: options_nav.append("3. GPS")
    
    # Sélecteur
    try:
        choix_nav = st.radio("Aller à :", options_nav, index=len(options_nav)-1)
        affichage_actuel = int(choix_nav.split(".")[0])
    except:
        affichage_actuel = 1

    st.divider()
    
    # --- HIGH TICKET ---
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

# PHASE 1
if affichage_actuel == 1:
    st.subheader("1️⃣ L'Avocat du Diable")
    
    if "step1" in st.session_state.analysis_data:
        st.info(f"Projet : {st.session_state.initial_idea}")
        st.markdown(st.session_state.analysis_data["step1"])
        
        st.divider()
        with st.expander("🔄 Relancer une nouvelle analyse (1 crédit)"):
            new_txt = st.text_area("Nouvelle version de l'idée :", value=st.session_state.initial_idea)
            if st.button("Relancer l'analyse"):
                if credits > 0:
                    st.session_state.initial_idea = new_txt
                    with st.spinner("Analyse V2..."):
                        res = model.generate_content(f"Analyse critique (Thinking mode) : {new_txt}")
                        st.session_state.analysis_data["step1"] = res.text
                        debit_credit_force(user, credits)
                        st.rerun()
                else: st.error("Crédit insuffisant")

    else:
        # Formulaire vierge
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
                        st.session_state.step = 2 
                        debit_credit_force(user, credits)
                        st.rerun()
        else: st.error("Rechargez vos crédits.")

# PHASE 2
elif affichage_actuel == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    
    if "step2" not in st.session_state.analysis_data:
        if st.button("Générer les Pivots"):
            with st.spinner("Recherche d'alternatives..."):
                res = model.generate_content(f"3 Pivots pour : {st.session_state.initial_idea}")
                st.session_state.analysis_data["step2"] = res.text
                st.session_state.step = 2
                st.rerun()
    
    if "step2" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step2"])
        
        st.divider()
        val_defaut = 0
        opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
        if st.session_state.selected_pivot in opts: val_defaut = opts.index(st.session_state.selected_pivot)
            
        ch = st.radio("Choix du modèle :", opts, index=val_defaut)
        if st.button("Valider et aller au GPS"):
            st.session_state.selected_pivot = ch
            st.session_state.step = 3
            st.rerun()

# PHASE 3
elif affichage_actuel == 3:
    st.subheader("3️⃣ GPS : Plan d'Exécution")
    final = st.session_state.initial_idea
    if st.session_state.selected_pivot: final += f" (Option : {st.session_state.selected_pivot})"
    st.info(f"Projet Validé : {final}")
    
    if "step3" not in st.session_state.analysis_data:
        if st.button("Calculer le Plan d'Action"):
            with st.spinner("Calcul itinéraire..."):
                res = model.generate_content(f"Plan d'action COO pour : {final}. Goal, Plan, Steps.")
                st.session_state.analysis_data["step3"] = res.text
                st.session_state.step = 3
                st.rerun()
                
    if "step3" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step3"])
        
        st.divider()
        col_end1, col_end2 = st.columns(2)
        with col_end1:
            st.link_button("💎 Audit Humain (Architecte)", LIEN_ARCHITECTE, type="primary")
        with col_end2:
            if st.button("🚀 Reset Total (Nouveau Projet)"):
                st.session_state.step = 1
                st.session_state.analysis_data = {}
                st.session_state.initial_idea = ""
                st.session_state.selected_pivot = None
                st.rerun()
