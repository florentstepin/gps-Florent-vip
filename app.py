import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai
import json
import time

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Stratège IA 2026 (Pro)", page_icon="🧠", layout="wide")

# ==============================================================================
# 🔐 RÉCUPÉRATION SÉCURISÉE DES CLÉS (Validé par l'Inspecteur)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    LIEN_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Configuration Fixe
    LIEN_ARCHITECTE = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    MODEL_NAME = 'gemini-2.5-pro' # Le modèle puissant
except Exception as e:
    st.error(f"❌ Erreur technique : {e}")
    st.stop()

# --- CONNEXIONS ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"❌ Erreur de connexion aux services : {e}")
    st.stop()

# --- GESTION ÉTAT (SESSION STATE) ---
if "step" not in st.session_state: st.session_state.step = 1
if "analysis_data" not in st.session_state: st.session_state.analysis_data = {}
if "selected_pivot" not in st.session_state: st.session_state.selected_pivot = None
if "initial_idea" not in st.session_state: st.session_state.initial_idea = ""

# --- FONCTIONS ROBUSTES ---

def get_user(code):
    try:
        code = str(code).strip()
        res = supabase.table("users").select("*").eq("access_code", code).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except: pass
    return None

def debit_credit_smart(user_obj, current):
    """Débite le crédit et met à jour l'interface immédiatement"""
    try:
        # 1. Identifier (UUID ou ID)
        user_id = user_obj.get("uuid") or user_obj.get("id")
        col_name = "uuid" if user_obj.get("uuid") else "id"
        
        if not user_id:
            st.error("Erreur critique : ID utilisateur introuvable.")
            return current

        # 2. Calculer
        new_balance = max(0, current - 1)
        
        # 3. Mettre à jour Supabase
        supabase.table("users").update({"credits": new_balance}).eq(col_name, user_id).execute()
        
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
            st.session_state.step = data.get("step", 1)
            st.session_state.initial_idea = data.get("idea", "")
            st.session_state.analysis_data = data.get("analysis", {})
            st.session_state.selected_pivot = data.get("pivot", None)
            st.success("Chargé !")
            time.sleep(1)
            st.rerun()
        except: st.error("Fichier invalide")

# --- ROUTAGE LOGIN ---
if "user" not in st.session_state:
    qp = st.query_params
    c_url = qp.get("code") or qp.get("access_code")
    if c_url:
        u = get_user(c_url)
        if u:
            st.session_state["user"] = u
            st.rerun()

# --- LOGIN SCREEN ---
if "user" not in st.session_state:
    st.title("🔐 Accès Stratège 2026")
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
    st.caption(f"Moteur: {MODEL_NAME}")

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
st.title(f"🧠 Stratège IA (Thinking Mode)")

steps = ["1. Analyse Profonde", "2. Pivot", "3. GPS"]
st.progress(st.session_state.step / 3)
st.caption(f"Phase : {steps[min(st.session_state.step-1, 2)]}")

# PHASE 1
if st.session_state.step == 1:
    st.subheader("1️⃣ L'Avocat du Diable (Mode Raisonnement)")
    if credits > 0:
        txt = st.text_area("Votre idée :", value=st.session_state.initial_idea, height=150)
        if st.button("Lancer l'analyse (1 crédit)"):
            if not txt: st.warning("Idée vide ?")
            else:
                st.session_state.initial_idea = txt
                with st.spinner("L'IA réfléchit étape par étape (Deep Thinking)..."):
                    try:
                        # PROMPT THINKING 2.5 PRO
                        prompt = f"""
                        Tu es un Expert Stratège Senior. Analyse : "{txt}".
                        
                        INSTRUCTION (Chain of Thought):
                        Ne réponds pas vite. Analyse le marché, la psycho client et la tech.
                        
                        RÉPONSE (Markdown):
                        1. **CONTEXTE & ANALYSE MACRO** : Pertinence 2026.
                        2. **3 FAILLES MORTELLES** : Ce que les autres ne voient pas.
                        3. **BIAIS COGNITIF** : L'angle mort du créateur.
                        4. **VERDICT** : [GO], [NOGO] ou [PIVOT].
                        5. **JUSTIFICATION** : Pourquoi.
                        """
                        
                        res = model.generate_content(prompt)
                        st.session_state.analysis_data["step1"] = res.text
                        
                        # DÉBIT ET FORÇAGE DE MISE À JOUR
                        new_c = debit_credit_smart(user, credits)
                        user["credits"] = new_c
                        st.session_state["user"] = user
                        st.rerun() # Rafraîchit l'écran immédiatement

                    except Exception as e:
                        st.error(f"Erreur API : {e}")
    else:
        st.error("Rechargez vos crédits.")

    if "step1" in st.session_state.analysis_data:
        st.divider()
        st.markdown(st.session_state.analysis_data["step1"])
        st.markdown(f"👉 **[Demander un Audit Architecte (Humain)]({LIEN_ARCHITECTE})**")
        c1, c2 = st.columns(2)
        if c1.button("➡️ GO -> Plan d'Action"):
            st.session_state.step = 3
            st.rerun()
        if c2.button("🔄 PIVOT -> Alternatives"):
            st.session_state.step = 2
            st.rerun()

# PHASE 2
elif st.session_state.step == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    if "step2" not in st.session_state.analysis_data:
        with st.spinner("Génération des pivots..."):
            try:
                res = model.generate_content(f"3 Pivots radicaux pour : {st.session_state.initial_idea}")
                st.session_state.analysis_data["step2"] = res.text
            except: pass
            
    st.markdown(st.session_state.analysis_data.get("step2", ""))
    ch = st.radio("Choix :", ["Initial", "Pivot 1", "Pivot 2", "Pivot 3"])
    if st.button("Valider"):
        st.session_state.selected_pivot = ch
        st.session_state.step = 3
        st.rerun()

# PHASE 3
elif st.session_state.step == 3:
    st.subheader("3️⃣ GPS : Plan d'Exécution")
    final = st.session_state.initial_idea
    if st.session_state.selected_pivot: final += f" ({st.session_state.selected_pivot})"
    st.info(f"Projet validé : {final}")
    
    if "step3" not in st.session_state.analysis_data:
        if st.button("Générer Plan"):
            with st.spinner("Calcul de l'itinéraire optimal..."):
                try:
                    res = model.generate_content(f"Plan d'action GPS pour : {final}")
                    st.session_state.analysis_data["step3"] = res.text
                    st.rerun()
                except: pass
    
    if "step3" in st.session_state.analysis_data:
        st.markdown(st.session_state.analysis_data["step3"])
        if st.button("Nouveau projet"):
            st.session_state.step = 1
            st.session_state.analysis_data = {}
            st.rerun()
