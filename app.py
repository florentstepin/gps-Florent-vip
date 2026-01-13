import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="L'Architecte de Projet (Thinking)",
    page_icon="🧠",
    layout="centered"
)

# --- 1. GESTION DES SECRETS (API KEY) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        # Configuration de l'API avec la clé
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ ERREUR CRITIQUE : La clé 'GOOGLE_API_KEY' est introuvable dans les Secrets de Streamlit.")
        st.info("Allez dans Settings > Secrets et ajoutez : GOOGLE_API_KEY = 'votre-clé'")
        st.stop()
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

# --- 2. DÉFINITION DU MODÈLE "THINKING" ---
def get_gemini_response(prompt_text):
    """
    Fonction centralisée pour appeler le modèle Thinking.
    Gère les erreurs de surcharge (503) ou de modèle introuvable.
    """
    try:
        # On tente d'abord le modèle le plus intelligent (Thinking)
        # Note: Si ce modèle spécifique n'est pas dispo, on basculera sur le 1.5 Pro
        model_name = 'gemini-2.0-flash-thinking-exp-1219' 
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(prompt_text)
        return response.text
        
    except Exception as e:
        # Fallback de sécurité si le modèle expérimental plante
        st.warning(f"⚠️ Le modèle Thinking est surchargé ou indisponible ({e}). Passage automatique au modèle standard.")
        try:
            fallback_model = genai.GenerativeModel('gemini-1.5-pro')
            response = fallback_model.generate_content(prompt_text)
            return response.text
        except Exception as e2:
            return f"❌ Erreur fatale de l'IA : {e2}"

# --- 3. LES PROMPTS EXPERTS (VOS PDF) ---

PROMPT_AUDIT_DUR = """
Rôle : Tu agis en tant qu'Ingénieur en Stratégie (Audit Crash-Test).
TA MISSION : Utilise tes capacités de RAISONNEMENT (Thinking) pour décortiquer cette idée.
Ne sois pas complaisant. Cherche la faille.

Analyse l'idée selon le Framework D.U.R. :
1. DOULOUREUX (Pain) : Est-ce une "Vitamine" (nice to have) ou une "Aspirine" (must have) ? Note /10.
2. URGENT (Time) : Le problème empire-t-il chaque jour ? Note /10.
3. RECONNU (Market) : La cible sait-elle qu'elle a ce problème et cherche-t-elle activement ? Note /10.

LIVRABLE :
- Le verdict chiffré (Score D.U.R.).
- Le point de rupture principal (pourquoi ça pourrait échouer).
- VERDICT FINAL : GO / NO-GO / PIVOT.

IDÉE À ANALYSER :
{user_idea}
"""

PROMPT_EXPLORATEUR = """
Rôle : Stratège en Innovation de Rupture.
CONTEXTE : L'idée initiale a des faiblesses ou peut être améliorée.
MISSION : Génère 5 "Pivots" (angles d'attaque différents) pour contourner la concurrence.
Pour chaque pivot, change radicalement une variable (La Cible, Le Mécanisme, ou Le Modèle Économique).

LIVRABLE : Une liste structurée de 5 angles audacieux.

PROJET INITIAL : {user_idea}
"""

PROMPT_PLAN_BACKCASTING = """
Rôle : Chef de Projet Agile (Méthode Backcasting).
MISSION : Construis le plan de bataille pour sortir ce MVP en 7 jours.
Pars du Jour 7 (Lancement/Vente) et remonte jusqu'au Jour 1.
Une seule action critique par jour. Pas de bla-bla.

STRATÉGIE RETENUE : {selected_angle}
"""

# --- 4. INTERFACE UTILISATEUR (MAIN) ---

def main():
    st.title("🧠 L'Architecte (Mode Thinking)")
    st.markdown("---")

    # --- A. LOGIN (GATEKEEPER SIMPLE) ---
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        col1, col2 = st.columns([2,1])
        with col1:
            password = st.text_input("Mot de passe d'accès", type="password")
        with col2:
            st.write("") # Spacer
            st.write("")
            if st.button("Entrer"):
                if password == "VIP2025": # <--- VOTRE CODE D'ACCÈS
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Accès refusé.")
        st.stop()

    # --- B. L'APPLICATION ---
    
    # Sidebar de contrôle
    with st.sidebar:
        st.success(f"Connecté (Licence VIP)")
        if st.button("Sortir"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
        st.caption("Modèle : Gemini 2.0 Flash Thinking")

    # Gestion des étapes (State Machine)
    if 'step' not in st.session_state:
        st.session_state.step = 1

    # ÉTAPE 1 : L'INPUT & AUDIT
    if st.session_state.step == 1:
        st.subheader("1. Le Crash-Test D.U.R. 💥")
        user_idea = st.text_area("Quelle est votre idée de business ?", height=150, placeholder="Ex: Une formation drone pour les géomètres...")
        
        if st.button("Lancer le Raisonnement IA"):
            if user_idea:
                with st.spinner("L'IA réfléchit (Thinking Process en cours)..."):
                    # Appel IA
                    response = get_gemini_response(PROMPT_AUDIT_DUR.format(user_idea=user_idea))
                    
                    # Stockage
                    st.session_state.audit_result = response
                    st.session_state.user_idea = user_idea
                    st.session_state.step = 2
                    st.rerun()
            else:
                st.warning("Il faut une idée pour commencer !")

    # ÉTAPE 2 : RÉSULTAT & PIVOT
    elif st.session_state.step == 2:
        st.subheader("Diagnostic de l'IA")
        st.markdown(st.session_state.audit_result)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Chercher des Pivots (Explorer)"):
                with st.spinner("Génération des angles d'attaque..."):
                    response = get_gemini_response(PROMPT_EXPLORATEUR.format(user_idea=st.session_state.user_idea))
                    st.session_state.pivot_result = response
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("🚀 Garder cette idée & Faire le Plan"):
                st.session_state.selected_angle = st.session_state.user_idea
                st.session_state.step = 4
                st.rerun()
        
        if st.button("🔙 Revenir au début"):
            st.session_state.step = 1
            st.rerun()

    # ÉTAPE 3 : CHOIX DU PIVOT
    elif st.session_state.step == 3:
        st.subheader("Exploration des Possibles 🔭")
        st.markdown(st.session_state.pivot_result)
        
        st.info("Copiez ci-dessous le titre de la stratégie que vous retenez.")
        selected_angle = st.text_input("Votre choix final :")
        
        if st.button("Valider et Générer le Plan"):
            if selected_angle:
                st.session_state.selected_angle = selected_angle
                st.session_state.step = 4
                st.rerun()
            else:
                st.warning("Choisissez une option.")

    # ÉTAPE 4 : PLAN D'ACTION
    elif st.session_state.step == 4:
        st.subheader("Plan d'Action Immédiat (7 Jours)")
        
        if 'plan_result' not in st.session_state:
            with st.spinner("Construction du Backcasting..."):
                response = get_gemini_response(PROMPT_PLAN_BACKCASTING.format(selected_angle=st.session_state.selected_angle))
                st.session_state.plan_result = response
        
        st.markdown(st.session_state.plan_result)
        
        # Bouton d'export
        full_report = f"# PROJET : {st.session_state.selected_angle}\n\n## 1. AUDIT\n{st.session_state.get('audit_result','')}\n\n## 2. PLAN\n{st.session_state.plan_result}"
        
        st.download_button("📥 Télécharger le Rapport (.md)", full_report, "projet_architecte.md")
        
        if st.button("Nouveau Projet"):
            for key in ['step', 'audit_result', 'plan_result', 'user_idea']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
    
