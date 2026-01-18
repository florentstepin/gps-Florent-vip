import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Stratège IA (Final)", page_icon="🚀", layout="wide")

# ==============================================================================
# 🛑 ZONE DE CONFIGURATION (VOS CLÉS)
# ==============================================================================

# 1. Vos clés SUPABASE 
SUPABASE_URL = "https://idvkrilkrfpzdmmmxgnj.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkdmtyaWxrcmZwemRtbW14Z25qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzNjY4NTIsImV4cCI6MjA4Mzk0Mjg1Mn0.pmjlyfNbe_4V4j26KeiFgUkNzI9tz9zPY3DwJho_RRU"
# 2. Votre clé GOOGLE GEMINI 
GOOGLE_API_KEY = "AIzaSyCHXZecD22-YyrAhiKUkgli4aBzKsWgAeg"
# 3. Votre lien de paiement 
LIEN_PAIEMENT = "https://ia-brainstormer.lemonsqueezy.com/checkout/buy/df3c85cc-c30d-4e33-b40a-0e1ee4ebab67"
# 4. Modèle IA
MODEL_NAME = 'gemini-2.5-flash'
# 5. Lien "Besoin d'un regard humain" (Architecte) - Votre Google Form
LIEN_ARCHITECTE = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform?usp=dialog"


# ==============================================================================
# FIN CONFIGURATION
# ==============================================================================

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

# --- FONCTIONS INTELLIGENTES (Compatible UUID) ---

def get_user(code):
    try:
        code = str(code).strip()
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except: pass
    return None

def debit_credit_smart(user_obj, current):
    """
    S'adapte automatiquement : fonctionne avec 'uuid' OU 'id'
    """
    try:
        # 1. Détection de la colonne ID (uuid ou id)
        user_id = None
        column_name = "id" # par défaut
        
        if "uuid" in user_obj:
            user_id = user_obj["uuid"]
            column_name = "uuid"
        elif "id" in user_obj:
            user_id = user_obj["id"]
            column_name = "id"
        
        # Sécurité si rien trouvé
        if not user_id:
            st.error("Erreur technique : Impossible de trouver l'ID utilisateur (uuid manquant).")
            return current

        # 2. Calcul du nouveau solde
        new_balance = max(0, current - 1)
        
        # 3. Mise à jour en utilisant le bon nom de colonne
        supabase.table("users").update({"credits": new_balance}).eq(column_name, user_id).execute()
        return new_balance

    except Exception as e:
        st.error(f"Erreur de débit : {e}")
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
            st.session_state.step = data.get("step", 1)
            st.session_state.initial_idea = data.get("idea", "")
            st.session_state.analysis_data = data.get("analysis", {})
            st.session_state.selected_pivot = data.get("pivot", None)
            st.success("Chargé !")
            time.sleep(1)
            st.rerun()
        except: st.error("Fichier invalide")

# --- ROUTAGE ---
if "user" not in st.session_state:
    qp = st.query_params
    c_url = qp.get("code") or qp.get("access_code")
    if c_url:
        u = get_user(c_url)
        if u:
            st.session_state["user"] = u
            st.rerun()

# --- LOGIN ---
if "user" not in st.session_state:
    st.title("🔐 Accès VIP")
    c_input = st.text_input("Code d'accès :")
    if st.button("Valider"):
        u = get_user(c_input)
        if u:
            st.session_state["user"] = u
            st.rerun()
        else: st.error("Code inconnu.")
    st.stop()

# --- APP START ---
user = st.session_state["user"]
credits = user.get("credits", 0)

with st.sidebar:
    st.header(f"Compte : {user.get('email', 'Email inconnu')}")
    
    # Affichage intelligent de l'ID pour vérification
    user_id_display = user.get("uuid") or user.get("id") or "Inconnu"
    st.caption(f"ID: {user_id_display}")

    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.error("Solde épuisé")
        st.markdown(f"👉 **[Recharger]({LIEN_RECHARGE})**")

    st.divider()
    st.download_button("💾 Sauvegarder", save_json(), "projet.json", "application/json")
    up = st.file_uploader("📂 Charger", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

# --- MAIN ---
st.title(f"🚀 Stratège IA")

steps = ["1. Crash Test", "2. Pivot", "3. GPS"]
st.progress(st.session_state.step / 3)
st.caption(f"Phase : {steps[min(st.session_state.step-1, 2)]}")

# PHASE 1
if st.session_state.step == 1:
    st.subheader("1️⃣ L'Avocat du Diable")
    if credits > 0:
        txt = st.text_area("Votre idée :", value=st.session_state.initial_idea)
        if st.button("Analyser (1 crédit)"):
            if not txt: st.warning("Idée vide ?")
            else:
                st.session_state.initial_idea = txt
                with st.spinner("Analyse..."):
                    try:
                        prompt = f"""Analyse l'idée : '{txt}'.
                        Rôle : Investisseur critique.
                        Output Markdown :
                        1. 3 Failles critiques.
                        2. Verdict : [GO], [NOGO] ou [PIVOT].
                        Justifie."""
                        
                        res = model.generate_content(prompt)
                        st.session_state.analysis_data["step1"] = res.text
                        
                        # DÉBIT INTELLIGENT (UUID ou ID)
                        new_c = debit_credit_smart(user, credits)
                        
                        user["credits"] = new_c
                        st.session_state["user"] = user
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur API : {e}")
    else:
        st.error("Rechargez vos crédits.")

    if "step1" in st.session_state.analysis_data:
        st.divider()
        st.markdown(st.session_state.analysis_data["step1"])
        st.markdown(f"👉 **[Demander un Audit Humain]({LIEN_ARCHITECTE})**")
        c1, c2 = st.columns(2)
        if c1.button("➡️ GO -> Plan d'Action"):
            st.session_state.step = 3
            st.rerun()
        if c2.button("🔄 PIVOT -> Alternatives"):
            st.session_state.step = 2
            st.rerun()

# PHASE 2
elif st.session_state.step == 2:
    st.subheader("2️⃣ Pivots")
    if "step2" not in st.session_state.analysis_data:
        with st.spinner("Recherche d'alternatives..."):
            res = model.generate_content(f"3 Pivots radicaux pour : {st.session_state.initial_idea}")
            st.session_state.analysis_data["step2"] = res.text
    st.markdown(st.session_state.analysis_data["step2"])
    ch = st.radio("Choix :", ["Initial", "Pivot 1", "Pivot 2", "Pivot 3"])
    if st.button("Valider"):
        st.session_state.selected_pivot = ch
        st.session_state.step = 3
        st.rerun()

# PHASE 3
elif st.session_state.step == 3:
    st.subheader("3️⃣ GPS Action")
    final = st.session_state.initial_idea
    if st.session_state.selected_pivot: final += f" ({st.session_state.selected_pivot})"
    st.info(f"Projet : {final}")
    
    if "step3" not in st.session_state.analysis_data:
        if st.button("Générer Plan"):
            with st.spinner("Calcul GPS..."):
                res = model.generate_content(f"Plan d'action (Goal, Plan, 1st Step) pour : {final}")
                st.session_state.analysis_data["step3"] = res.text
                st.rerun()
    
    if "step3" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step3"])
        if st.button("Nouveau"):
            st.session_state.step = 1
            st.session_state.analysis_data = {}
            st.rerun()
