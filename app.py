import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="L'Architecte (Deep Research)", page_icon="🔬", layout="centered")

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

# --- SÉLECTEUR DE MODÈLE (HIÉRARCHIE D'ÉLITE) ---
def get_expert_response(prompt_text):
    """
    PRIORITÉ ABSOLUE : Deep Research.
    C'est le modèle le plus puissant pour l'analyse critique.
    """
    preferred_models = [
        'deep-research-pro-preview-12-2025', # Le Saint Graal (que vous avez détecté)
        'gemini-3.0-pro-preview',            # Le plan B (Très puissant)
        'gemini-2.5-pro',                    # Le plan C (Valeur sûre)
        'gemini-2.0-flash-exp'               # Le plan D (Vitesse)
    ]

    last_error = ""

    for model_name in preferred_models:
        try:
            model = genai.GenerativeModel(model_name)
            
            # Pour Deep Research, on laisse une température un peu plus haute 
            # pour qu'il explore des pistes créatives (0.4)
            response = model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4, 
                )
            )
            return response.text, model_name
        except Exception as e:
            last_error = str(e)
            continue # On essaie le suivant
            
    return f"❌ Erreur sur tous les modèles. Détail : {last_error}", "Aucun"

# --- PROMPTS "SYSTEM 2" (Optimisés pour Deep Research) ---

PROMPT_AUDIT = """
Tu es un Consultant en Stratégie de Haut Niveau.
TA MISSION : Mener une 'Deep Research' sur la viabilité de ce projet.

🧠 INSTRUCTION SPÉCIALE :
Ce modèle est capable de profondeur. Ne survole pas.
1. Simule le marché : Qui sont les concurrents invisibles ?
2. Teste la robustesse financière : Est-ce rentable rapidement ?
3. Cherche la faille psychologique : Pourquoi le client n'achètera PAS ?

FORMAT DE SORTIE :
1. 🔬 **Analyse Profonde** (Les non-dits du projet).
2. 📊 **Matrice D.U.R.** (Douleur/Urgence/Reconnu sur 10).
3. ⚖️ **VERDICT** : GO / NO-GO / PIVOT.

IDÉE : {user_idea}
"""

PROMPT_PIVOT = """
Expert en Stratégie de Rupture.
L'idée est trop fragile.
Utilise tes capacités de recherche pour trouver 5 PIVOTS basés sur des tendances lourdes ou des niches inexploitées.
Sois radical.

PROJET : {user_idea}
"""

PROMPT_PLAN = """
Backcasting Opérationnel (J+7 à J-1).
Objectif : Cash-in dans 7 jours.
Ne donne que des actions exécutables (Call, Email, Setup). Pas de "réflexion".

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
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Non.")
        st.stop()

    # Sidebar
    with st.sidebar:
        if st.button("Déconnexion"):
            st.session_state.logged_in = False
            st.rerun()
        st.info("Mode : Recherche Profonde")

    # Logique
    if 'step' not in st.session_state:
        st.session_state.step = 1

    # ETAPE 1
    if st.session_state.step == 1:
        st.subheader("1. Audit Deep Research")
        user_idea = st.text_area("Décrivez votre projet :", height=150)
        
        if st.button("Lancer l'Analyse Profonde"):
            if user_idea:
                with st.spinner("Le modèle Deep Research analyse le contexte (cela peut prendre 10s)..."):
                    res, model_used = get_expert_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    
                    st.session_state.audit = res
                    st.session_state.model = model_used
                    st.session_state.idea = user_idea
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2
    elif st.session_state.step == 2:
        # Affichage du modèle utilisé
        if "deep-research" in st.session_state.model:
             st.sidebar.success(f"✅ Deep Research Actif")
        else:
             st.sidebar.warning(f"⚠️ Fallback : {st.session_state.model}")
        
        st.markdown(st.session_state.audit)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Explorer Pivots"):
                with st.spinner("Recherche d'alternatives..."):
                    res, _ = get_expert_response(PROMPT_PIVOT.format(user_idea=st.session_state.idea))
                    st.session_state.pivot = res
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("Faire le Plan"):
                st.session_state.choix = st.session_state.idea
                st.session_state.step = 4
                st.rerun()
        
        if st.button("Retour"):
            st.session_state.step = 1
            st.rerun()

    # ETAPE 3
    elif st.session_state.step == 3:
        st.markdown(st.session_state.pivot)
        choix = st.text_input("Choix stratégique :")
        if st.button("Planifier"):
            st.session_state.choix = choix
            st.session_state.step = 4
            st.rerun()

    # ETAPE 4
    elif st.session_state.step == 4:
        if 'plan' not in st.session_state:
            with st.spinner("Génération du plan tactique..."):
                res, _ = get_expert_response(PROMPT_PLAN.format(selected_angle=st.session_state.choix))
                st.session_state.plan = res
        
        st.markdown(st.session_state.plan)
        
        st.download_button("Télécharger le Rapport", st.session_state.plan, "Deep_Research_Report.md")
        if st.button("Nouveau Projet"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
