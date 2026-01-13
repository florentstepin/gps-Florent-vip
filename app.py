import streamlit as st
import google.generativeai as genai
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="L'Architecte (High IQ)", page_icon="🧠", layout="centered")

# --- CONNEXION STABLE (GEMINI 1.5 PRO) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("Clé API manquante.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

def get_high_iq_response(prompt_text):
    """
    Simule le 'Thinking' avec Gemini 1.5 Pro via un prompt structuré.
    C'est la méthode la plus fiable pour égaler GPT-4.
    """
    try:
        # On utilise le modèle PRO (Le plus intelligent des stables)
        # Surtout pas le 'Flash' qui est trop rapide/bête pour ça.
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        response = model.generate_content(
            prompt_text,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4, # Température basse = plus de rigueur logique
            )
        )
        return response.text
    except Exception as e:
        return f"Erreur IA : {str(e)}"

# --- LES PROMPTS "SYSTEM 2" (Raisonnement Forcé) ---

PROMPT_AUDIT_DUR = """
Tu es un Expert Radical en Stratégie (Niveau McKinsey/BCG).
Ton objectif est de détruire l'idée proposée pour voir si elle survit (Crash Test).

CONSIGNE DE RAISONNEMENT (OBLIGATOIRE) :
Avant de donner le verdict, tu dois mener une réflexion interne étape par étape :
1. Cherche la faille la plus évidente (Pourquoi personne ne l'a fait ?).
2. Analyse la "Douleur" réelle (Est-ce que les gens se réveillent la nuit pour ça ?).
3. Vérifie la solvabilité (La cible a-t-elle de l'argent ?).

FORMAT DE RÉPONSE ATTENDU :
Affiche d'abord ta réflexion brute sous forme de bullet points "⚡ ANALYSE FLASH".
Ensuite, affiche le TABLEAU D.U.R (Notes sur 10 avec justification cinglante).
Enfin, le VERDICT : GO / NO-GO / PIVOT.

IDÉE : {user_idea}
"""

PROMPT_EXPLORATEUR = """
Agis comme un Génie du "Lateral Thinking".
L'idée actuelle est trop banale ou fragile.
Génère 5 PIVOTS radicaux. Pour chaque pivot, change une variable lourde :
- Change la cible (ex: B2C -> B2B High Ticket)
- Change l'ennemi (ex: Contre l'ennui -> Contre la peur)
- Change le modèle (ex: Vente -> Abonnement)

IDÉE DE DÉPART : {user_idea}
"""

PROMPT_PLAN = """
Méthode Backcasting (Inversion temporelle).
Objectif : MVP vendu dans 7 jours.
Interdiction de mettre des tâches administratives (pas de logo, pas de statut juridique).
Que de l'action de vente/création.

STRATÉGIE : {selected_angle}
"""

# --- INTERFACE ---

def main():
    st.title("🧠 L'Architecte (Pro)")
    
    # Login Rapide
    if 'logged_in' not in st.session_state:
        code = st.text_input("Code d'accès", type="password")
        if st.button("Valider"):
            if code == "VIP2025":
                st.session_state.logged_in = True
                st.rerun()
        st.stop()

    # Sidebar
    if st.sidebar.button("Reset / Déconnexion"):
        st.session_state.clear()
        st.rerun()

    # Machine à états
    if 'step' not in st.session_state:
        st.session_state.step = 1

    # --- ÉTAPE 1 : AUDIT ---
    if st.session_state.step == 1:
        st.markdown("### 1. Le Crash-Test")
        user_idea = st.text_area("Votre idée brute :", height=100)
        
        if st.button("Lancer l'Analyse Profonde"):
            if user_idea:
                with st.spinner("Analyse critique en cours (Simulation System 2)..."):
                    # On appelle la fonction "High IQ"
                    res = get_high_iq_response(PROMPT_AUDIT_DUR.format(user_idea=user_idea))
                    st.session_state.audit_result = res
                    st.session_state.user_idea = user_idea
                    st.session_state.step = 2
                    st.rerun()

    # --- ÉTAPE 2 : RÉSULTAT ---
    elif st.session_state.step == 2:
        st.info("💡 Analyse terminée. Lisez attentivement les critiques ci-dessous.")
        st.markdown(st.session_state.audit_result)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Explorer des Pivots"):
                with st.spinner("Recherche d'angles morts..."):
                    res = get_high_iq_response(PROMPT_EXPLORATEUR.format(user_idea=st.session_state.user_idea))
                    st.session_state.pivots = res
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("Faire le Plan (Go)"):
                st.session_state.choix = st.session_state.user_idea
                st.session_state.step = 4
                st.rerun()
        
        if st.button("Essayer une autre idée"):
            st.session_state.step = 1
            st.rerun()

    # --- ÉTAPE 3 : PIVOTS ---
    elif st.session_state.step == 3:
        st.markdown("### 2. Les Pivots Stratégiques")
        st.markdown(st.session_state.pivots)
        
        choix = st.text_input("Copiez le titre du pivot choisi :")
        if st.button("Valider ce Pivot"):
            st.session_state.choix = choix
            st.session_state.step = 4
            st.rerun()

    # --- ÉTAPE 4 : PLAN ---
    elif st.session_state.step == 4:
        st.markdown("### 3. Plan d'Action Commando")
        if 'plan' not in st.session_state:
            with st.spinner("Génération du plan..."):
                res = get_high_iq_response(PROMPT_PLAN.format(selected_angle=st.session_state.choix))
                st.session_state.plan = res
        
        st.markdown(st.session_state.plan)
        
        report = f"# PROJET\n{st.session_state.choix}\n\n## ANALYSE\n{st.session_state.get('audit_result')}\n\n## PLAN\n{st.session_state.plan}"
        st.download_button("Télécharger le rapport", report, "projet.md")
        
        if st.button("Recommencer"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
