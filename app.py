import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="L'Architecte (Pro)", page_icon="🏗️", layout="centered")

# --- 2. BOUTON D'URGENCE (SIDEBAR) ---
if st.sidebar.button("♻️ RESET COMPLET"):
    st.session_state.clear()
    st.rerun()

# --- 3. INITIALISATION ROBUSTE (Anti-Crash) ---
# On déclare toutes les variables vides au démarrage pour éviter l'écran rouge
defaults = {
    'logged_in': False,
    'step': 1,
    'audit': "",
    'model_used': "En attente",
    'idea': "",
    'pivot': "",
    'plan': "",
    'choix': ""
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 4. CONNEXION ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ Pas de Clé API.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

# --- 5. LE CERVEAU HYBRIDE ---
def get_strategic_response(prompt_text):
    """
    Stratégie : Tente le modèle PRO (Intelligent) d'abord.
    Si quota dépassé ou erreur, bascule sur le FLASH (Rapide et sûr).
    """
    try:
        # Priorité 1 : Le modèle PRO (celui de votre liste) pour l'analyse D.U.R.
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt_text)
        return response.text, "gemini-2.5-pro (Intelligence Max)"
    except:
        try:
            # Priorité 2 : Le modèle FLASH (celui qui a marché à l'instant)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt_text)
            return response.text, "gemini-2.5-flash (Mode Rapide)"
        except Exception as e:
            return f"❌ Erreur critique : {e}", "Aucun"

# --- 6. LES PROMPTS EXPERTS (Le retour du D.U.R.) ---

PROMPT_AUDIT = """
RÔLE : Tu es un "Avocat du Diable" et Stratège Business impitoyable.
MISSION : Analyse le projet suivant. Ne sois pas complaisant.

STRUCTURE DE RÉPONSE OBLIGATOIRE :
1. 🛡️ **PRE-MORTEM (Pourquoi ça va rater)** : Cite 3 raisons fatales (marché, concurrence, finance).
2. 📊 **MATRICE D.U.R.** (Donne une note sur 10 précise) :
   - **D**ouleur (Est-ce insupportable pour le client ?) : _/10
   - **U**rgence (Doit-il acheter maintenant ?) : _/10
   - **R**econnu (Sait-il qu'il a ce problème ?) : _/10
3. 🏁 **VERDICT** : GO / NO-GO / PIVOT (en gras).

PROJET : {user_idea}
"""

PROMPT_PIVOT = """
RÔLE : Expert en Innovation de Rupture.
CONTEXTE : Le projet initial est trop classique.
MISSION : Propose 5 PIVOTS radicaux pour changer la donne.
(Change la cible, le modèle économique, ou la technologie).

PROJET : {user_idea}
"""

PROMPT_PLAN = """
RÔLE : Chef de projet Commando.
MÉTHODE : Backcasting (Partir de la vente J+7 et remonter à J-1).
OBJECTIF : Première vente en 7 jours.
LIVRABLE : Plan d'action jour par jour (Actions concrètes uniquement, pas de "réflexion").

STRATÉGIE RETENUE : {selected_angle}
"""

# --- 7. INTERFACE ---

def main():
    st.title("🏗️ L'Architecte")
    st.caption("v3.0 - Analyse Stratégique")

    # LOGIN
    if not st.session_state.logged_in:
        with st.form("login"):
            code = st.text_input("Code VIP", type="password")
            if st.form_submit_button("Entrer"):
                if code == "VIP2025":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Code incorrect.")
        st.stop()

    # SIDEBAR
    with st.sidebar:
        st.success("Licence Active ✅")
        if st.button("Déconnexion"):
            st.session_state.clear()
            st.rerun()

    # ETAPE 1 : AUDIT
    if st.session_state.step == 1:
        st.subheader("1. Le Crash-Test D.U.R.")
        user_idea = st.text_area("Votre idée :", height=120, placeholder="Ex: Formation drone...")
        
        if st.button("Lancer l'Audit Impitoyable 💥"):
            if user_idea:
                with st.spinner("L'Architecte analyse les failles..."):
                    res, model_name = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    
                    st.session_state.audit = res
                    st.session_state.model_used = model_name
                    st.session_state.idea = user_idea
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2 : RÉSULTAT
    elif st.session_state.step == 2:
        st.caption(f"🧠 Cerveau utilisé : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Chercher des Pivots"):
                with st.spinner("Recherche d'angles morts..."):
                    res, _ = get_strategic_response(PROMPT_PIVOT.format(user_idea=st.session_state.idea))
                    st.session_state.pivot = res
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("🚀 Valider & Planifier"):
                st.session_state.choix = st.session_state.idea
                st.session_state.step = 4
                st.rerun()
        
        if st.button("Nouvelle Analyse"):
            st.session_state.step = 1
            st.rerun()

    # ETAPE 3 : PIVOTS
    elif st.session_state.step == 3:
        st.subheader("Stratégies Alternatives")
        st.markdown(st.session_state.pivot)
        
        choix = st.text_input("Quelle stratégie choisissez-vous ?")
        if st.button("Générer le Plan"):
            st.session_state.choix = choix
            st.session_state.step = 4
            st.rerun()

    # ETAPE 4 : PLAN
    elif st.session_state.step == 4:
        st.subheader("Plan d'Action (7 Jours)")
        if not st.session_state.plan:
            with st.spinner("Rédaction du plan tactique..."):
                res, _ = get_strategic_response(PROMPT_PLAN.format(selected_angle=st.session_state.choix))
                st.session_state.plan = res
        
        st.markdown(st.session_state.plan)
        
        st.download_button("Télécharger le Rapport", st.session_state.plan, "Rapport_Architecte.md")
        
        if st.button("Recommencer"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
