import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="L'Architecte (Deep Research)", page_icon="🔬", layout="centered")

# --- INITIALISATION DES VARIABLES (ANTI-CRASH) ---
# C'est ce bloc qui manquait et qui causait l'erreur après le code VIP
if 'model' not in st.session_state:
    st.session_state.model = "En attente..."
if 'audit' not in st.session_state:
    st.session_state.audit = ""
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- CONNEXION ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ Clé API manquante.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

# --- SÉLECTEUR DE MODÈLE ---
def get_expert_response(prompt_text):
    preferred_models = [
        'deep-research-pro-preview-12-2025', 
        'gemini-3.0-pro-preview',
        'gemini-2.5-pro',
        'gemini-2.0-flash-exp'
    ]

    last_error = ""

    for model_name in preferred_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4, 
                )
            )
            return response.text, model_name
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"❌ Erreur sur tous les modèles. Détail : {last_error}", "Aucun"

# --- PROMPTS ---
PROMPT_AUDIT = """
Tu es un Consultant en Stratégie de Haut Niveau.
TA MISSION : Mener une 'Deep Research' sur la viabilité de ce projet.
Ne survole pas. Simule le marché, la concurrence cachée et la psychologie client.

LIVRABLE :
1. 🔬 **Analyse Profonde** (Les non-dits du projet).
2. 📊 **Matrice D.U.R.** (Douleur/Urgence/Reconnu sur 10).
3. ⚖️ **VERDICT** : GO / NO-GO / PIVOT.

IDÉE : {user_idea}
"""

PROMPT_PIVOT = """
Expert en Stratégie de Rupture.
Génère 5 PIVOTS radicaux basés sur des niches inexploitées.
Sois radical.

PROJET : {user_idea}
"""

PROMPT_PLAN = """
Backcasting Opérationnel (J+7 à J-1).
Objectif : Cash-in dans 7 jours.
Actions tactiques uniquement.

STRATÉGIE : {selected_angle}
"""

# --- INTERFACE ---
def main():
    st.title("🔬 L'Architecte")
    st.caption("Propulsé par Google Deep Research Pro")
    
    # Login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.form("login"):
            code = st.text_input("Code VIP", type="password")
            if st.form_submit_button("Entrer"):
                if code == "VIP2025":
                    # On réinitialise tout pour éviter les conflits d'ancienne session
                    st.session_state.step = 1
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Code incorrect.")
        st.stop()

    # Sidebar
    with st.sidebar:
        if st.button("Déconnexion"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.info("Mode : Recherche Profonde")

    # ETAPE 1
    if st.session_state.step == 1:
        st.subheader("1. Audit Deep Research")
        user_idea = st.text_area("Décrivez votre projet :", height=150)
        
        if st.button("Lancer l'Analyse Profonde"):
            if user_idea:
                with st.spinner("Le modèle Deep Research analyse le contexte..."):
                    res, model_used = get_expert_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    
                    st.session_state.audit = res
                    st.session_state.model = model_used
                    st.session_state.idea = user_idea
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2
    elif st.session_state.step == 2:
        # Affichage sécurisé du modèle
        current_model = st.session_state.get('model', 'Inconnu')
        if "deep-research" in current_model:
             st.sidebar.success(f"✅ Deep Research Actif")
        else:
             st.sidebar.warning(f"⚠️ Cerveau : {current_model}")
        
        st.markdown(st.session_state.audit)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Explorer Pivots"):
                with st.spinner("Recherche d'alternatives..."):
                    res, _ = get_expert_response(PROMPT_PIVOT.format(user_idea=st.session_state.get('idea', '')))
                    st.session_state.pivot = res
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("Faire le Plan"):
                st.session_state.choix = st.session_state.get('idea', '')
                st.session_state.step = 4
                st.rerun()
        
        if st.button("Retour"):
            st.session_state.step = 1
            st.rerun()

    # ETAPE 3
    elif st.session_state.step == 3:
        st.markdown(st.session_state.get('pivot', 'Erreur'))
        choix = st.text_input("Choix stratégique :")
        if st.button("Planifier"):
            st.session_state.choix = choix
            st.session_state.step = 4
            st.rerun()

    # ETAPE 4
    elif st.session_state.step == 4:
        if 'plan' not in st.session_state:
            with st.spinner("Génération du plan tactique..."):
                res, _ = get_expert_response(PROMPT_PLAN.format(selected_angle=st.session_state.get('choix', '')))
                st.session_state.plan = res
        
        st.markdown(st.session_state.plan)
        
        st.download_button("Télécharger le Rapport", st.session_state.plan, "Deep_Research_Report.md")
        if st.button("Nouveau Projet"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
