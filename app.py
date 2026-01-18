import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Stratège IA V10", page_icon="⚡", layout="wide")

# 1. SECRETS
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    LIEN_RECHARGE = st.secrets["LIEN_RECHARGE"]
    LIEN_ARCHITECTE = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    MODEL_NAME = 'gemini-2.5-pro'
except Exception as e:
    st.error(f"Erreur Secrets: {e}")
    st.stop()

# 2. CLIENTS
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"Erreur Connexion: {e}")
    st.stop()

# 3. ETAT
if "max_step" not in st.session_state: st.session_state.max_step = 1
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"
if "analysis_data" not in st.session_state: st.session_state.analysis_data = {}
if "selected_pivot" not in st.session_state: st.session_state.selected_pivot = None
if "initial_idea" not in st.session_state: st.session_state.initial_idea = ""

# 4. FONCTIONS
def get_user(code):
    try:
        code = str(code).strip()
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data: return res.data[0]
    except: pass
    return None

def debit_force(user_obj, current):
    """Met à jour l'interface immédiatement"""
    new_bal = max(0, current - 1)
    if "user" in st.session_state:
        st.session_state["user"]["credits"] = new_bal
    try:
        uid = user_obj.get("uuid") or user_obj.get("id")
        col = "uuid" if user_obj.get("uuid") else "id"
        if uid:
            supabase.table("users").update({"credits": new_bal}).eq(col, uid).execute()
    except: pass
    return new_bal

def save_json():
    data = {
        "max_step": st.session_state.max_step,
        "idea": st.session_state.initial_idea,
        "analysis": st.session_state.analysis_data,
        "pivot": st.session_state.selected_pivot
    }
    return json.dumps(data, indent=4)

def load_json(f):
    if f:
        try:
            data = json.load(f)
            st.session_state.initial_idea = data.get("idea", "")
            st.session_state.analysis_data = data.get("analysis", {})
            st.session_state.selected_pivot = data.get("pivot", None)
            
            s = data.get("max_step", 1)
            if "step3" in st.session_state.analysis_data: s = max(s, 3)
            elif "step2" in st.session_state.analysis_data: s = max(s, 2)
            
            st.session_state.max_step = s
            st.session_state.current_view = "1. Analyse"
            st.success("Chargé !")
            time.sleep(0.5)
            st.rerun()
        except: st.error("Erreur fichier")

# 5. LOGIN
if "user" not in st.session_state:
    qp = st.query_params
    c_url = qp.get("code") or qp.get("access_code")
    if c_url:
        u = get_user(c_url)
        if u:
            st.session_state["user"] = u
            st.rerun()
            
    st.title("🔐 Accès Stratège")
    c_input = st.text_input("Code d'accès :")
    if st.button("Valider"):
        u = get_user(c_input)
        if u:
            st.session_state["user"] = u
            st.rerun()
    st.stop()

# 6. APP
user = st.session_state["user"]
credits = user.get("credits", 0)

with st.sidebar:
    st.header("Mon Compte")
    if credits > 0:
        st.metric("Crédits", credits)
    else:
        st.error("Solde épuisé")
        st.markdown(f"[Recharger]({LIEN_RECHARGE})")

    st.divider()
    st.markdown("### 📂 Menu")
    
    # Navigation simplifiée (Anti-bug syntaxe)
    opts = ["1. Analyse"]
    if st.session_state.max_step >= 2 or "step2" in st.session_state.analysis_data:
        opts.append("2. Pivots")
        st.session_state.max_step = max(st.session_state.max_step, 2)
        
    if st.session_state.max_step >= 3 or "step3" in st.session_state.analysis_data:
        opts.append("3. GPS")
        st.session_state.max_step = max(st.session_state.max_step, 3)
    
    idx = 0
    if st.session_state.current_view in opts:
        idx = opts.index(st.session_state.current_view)
    else:
        st.session_state.current_view = "1. Analyse"
        
    nav = st.radio("Aller à :", opts, index=idx)
    
    if nav != st.session_state.current_view:
        st.session_state.current_view = nav
        st.rerun()
        
    step_num = 1
    if "2." in st.session_state.current_view: step_num = 2
    if "3." in st.session_state.current_view: step_num = 3

    st.divider()
    st.link_button("💎 Audit Humain", LIEN_ARCHITECTE, type="primary")
    st.download_button("💾 Sauver", save_json(), "projet.json")
    up = st.file_uploader("📤 Charger", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        del st.session_state["user"]
        st.rerun()

st.title("🧠 Stratège IA")
st.progress(step_num / 3)

# PHASE 1
if step_num == 1:
    st.subheader("1️⃣ Analyse")
    if "step1" in st.session_state.analysis_data:
        st.info(f"Projet: {st.session_state.initial_idea}")
        st.markdown(st.session_state.analysis_data["step1"])
        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            if st.button("➡️ Suite (Pivots)", type="primary"):
                st.session_state.max_step = max(st.session_state.max_step, 2)
                st.session_state.current_view = "2. Pivots"
                st.rerun()
        with c2:
            with st.expander("Relancer (1 crédit)"):
                n_txt = st.text_area("Correction :", value=st.session_state.initial_idea)
                if st.button("Relancer"):
                    if credits > 0:
                        st.session_state.initial_idea = n_txt
                        st.session_state.analysis_data.pop("step2", None)
                        st.session_state.analysis_data.pop("step3", None)
                        st.session_state.max_step = 1
                        with st.spinner("Analyse..."):
                            res = model.generate_content(f"Analyse critique: {n_txt}")
                            st.session_state.analysis_data["step1"] = res.text
                            debit_force(user, credits)
                            st.rerun()
                    else: st.error("Pas de crédit")
    else:
        if credits > 0:
            txt = st.text_area("Votre idée :", height=150)
            if st.button("Analyser (1 crédit)"):
                if txt:
                    st.session_state.initial_idea = txt
                    with st.spinner("Reflexion..."):
                        p = f"Role: Expert Stratège. Analyse critique de: {txt}. Format: Markdown. 1.Macro 2.Failles 3.Biais 4.Verdict."
                        res = model.generate_content(p)
                        st.session_state.analysis_data["step1"] = res.text
                        st.session_state.max_step = 2
                        debit_force(user, credits)
                        st.rerun()
        else: st.error("Rechargez vos crédits")

# PHASE 2
elif step_num == 2:
    st.subheader("2️⃣ Pivots")
    if "step2" not in st.session_state.analysis_data:
        with st.spinner("Génération..."):
            try:
                res = model.generate_content(f"3 Pivots pour: {st.session_state.initial_idea}")
                st.session_state.analysis_data["step2"] = res.text
                st.rerun()
            except: st.error("Erreur API")
            
    if "step2" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step2"])
        st.divider()
        st.markdown("### Choix")
        opts_p = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
        idx_p = 0
        if st.session_state.selected_pivot in opts_p:
            idx_p = opts_p.index(st.session_state.selected_pivot)
        
        ch = st.radio("Stratégie :", opts_p, index=idx_p)
        
        if st.button("Valider et Suite", type="primary"):
            st.session_state.selected_pivot = ch
            st.session_state.analysis_data.pop("step3", None)
            st.session_state.max_step = 3
            st.session_state.current_view = "3. GPS"
            st.rerun()

# PHASE 3
elif step_num == 3:
    st.subheader("3️⃣ GPS")
    fin = st.session_state.initial_idea
    if st.session_state.selected_pivot: fin += f" ({st.session_state.selected_pivot})"
    st.info(f"Cible: {fin}")
    
    if "step3" not in st.session_state.analysis_data:
        if st.button("Calculer Plan"):
            with st.spinner("Calcul..."):
                res = model.generate_content(f"Plan d'action COO pour: {fin}. Goal 90j, Plan 30j, Actions Today.")
                st.session_state.analysis_data["step3"] = res.text
                st.rerun()
                
    if "step3" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step3"])
        st.divider()
        c_a, c_b = st.columns(2)
        with c_a: st.link_button("💎 Audit Humain", LIEN_ARCHITECTE, type="primary")
        with c_b:
            if st.button("🔄 Nouveau Projet"):
                st.session_state.max_step = 1
                st.session_state.current_view = "1. Analyse"
                st.session_state.analysis_data = {}
                st.session_state.initial_idea = ""
                st.
