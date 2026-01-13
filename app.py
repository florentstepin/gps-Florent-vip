import streamlit as st
import google.generativeai as genai
import urllib.parse # Nécessaire pour créer le lien email magique

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="L'Architecte (Pro)", page_icon="🏗️", layout="centered")

# --- 🔴 VOTRE EMAIL DE CONTACT ICI 🔴 ---
EMAIL_CONTACT = "votre-email@gmail.com" 
# ----------------------------------------

# --- 2. BOUTON D'URGENCE ---
if st.sidebar.button("♻️ RESET COMPLET"):
    st.session_state.clear()
    st.rerun()

# --- 3. INITIALISATION ---
defaults = {'logged_in': False, 'step': 1, 'audit': "", 'model_used': "En attente", 
            'idea': "", 'pivot': "", 'plan': "", 'choix': ""}
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

# --- 5. CERVEAU HYBRIDE ---
def get_strategic_response(prompt_text):
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt_text)
        return response.text, "gemini-2.5-pro (Max)"
    except:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt_text)
            return response.text, "gemini-2.5-flash (Fast)"
        except Exception as e:
            return f"❌ Erreur critique : {e}", "Aucun"

# --- 6. FONCTION EMAIL MAGIQUE ---
def create_mailto_link(idea, audit):
    """
    Génère un lien qui ouvre l'email du client avec tout le texte déjà rempli.
    """
    subject = "Demande d'aide - Analyse Architecte"
    
    # On prépare le corps du mail
    body = f"""Bonjour,

J'ai utilisé l'Architecte IA et voici le résultat obtenu.
J'aimerais votre avis d'expert humain dessus.

--- MON IDÉE ---
{idea}

--- L'AUDIT DE L'IA ---
{audit}

----------------
(Le client peut ajouter son message ici)
"""
    # On encode le texte pour qu'il passe dans une URL (les espaces deviennent %20, etc.)
    safe_subject = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)
    
    return f"mailto:{EMAIL_CONTACT}?subject={safe_subject}&body={safe_body}"

# --- 7. PROMPTS ---
PROMPT_AUDIT = """
RÔLE : Avocat du Diable & Stratège.
MISSION : Analyse sans pitié.
LIVRABLE :
1. 🛡️ **PRE-MORTEM** : 3 raisons fatales.
2. 📊 **MATRICE D.U.R.** (/10) : Douleur / Urgence / Reconnu.
3. 🏁 **VERDICT** : GO / NO-GO / PIVOT (En majuscules).
PROJET : {user_idea}
"""

PROMPT_PIVOT = """
RÔLE : Expert Innovation.
MISSION : 5 Pivots radicaux.
PROJET : {user_idea}
"""

PROMPT_PLAN = """
RÔLE : Chef de projet Commando.
OBJECTIF : Première vente J+7.
LIVRABLE : Plan d'action.
STRATÉGIE : {selected_angle}
"""

# --- 8. INTERFACE ---
def main():
    st.title("🏗️ L'Architecte")
    st.caption("v5.0 - Email Contextuel")

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
        user_idea = st.text_area("Votre idée :", height=120)
        
        if st.button("Lancer l'Audit 💥"):
            if user_idea:
                with st.spinner("Analyse des risques..."):
                    res, model_name = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    st.session_state.audit = res
                    st.session_state.model_used = model_name
                    st.session_state.idea = user_idea
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2 : RÉSULTAT + EMAIL CONTEXTUEL
    elif st.session_state.step == 2:
        st.caption(f"Cerveau : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        # --- LOGIQUE INTELLIGENTE ---
        verdict_negatif = "NO-GO" in st.session_state.audit or "PIVOT" in st.session_state.audit
        
        # Création du lien email personnalisé
        link = create_mailto_link(st.session_state.idea, st.session_state.audit)
        
        st.markdown("---")
        
        if verdict_negatif:
            st.error("🚨 **ALERTE : PROJET À RISQUE**")
            st.write("L'IA a détecté des failles critiques. Ne restez pas seul avec ce diagnostic.")
            # Bouton Email Rouge
            st.link_button("📧 Envoyer ce rapport à l'Architecte (Humain)", link)
        else:
            st.success("✅ **SIGNAL VERT**")
            st.write("Le potentiel est là. Vous voulez accélérer la mise en œuvre ?")
            # Bouton Email Vert
            st.link_button("🚀 Envoyer mon dossier pour validation", link)
            
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Pivoter (IA)"):
                with st.spinner("Recherche..."):
                    res, _ = get_strategic_response(PROMPT_PIVOT.format(user_idea=st.session_state.idea))
                    st.session_state.pivot = res
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("📋 Plan d'Action (IA)"):
                st.session_state.choix = st.session_state.idea
                st.session_state.step = 4
                st.rerun()
        
        if st.button("Nouvelle Analyse"):
            st.session_state.step = 1
            st.rerun()

    # ETAPE 3 : PIVOTS
    elif st.session_state.step == 3:
        st.markdown(st.session_state.pivot)
        choix = st.text_input("Choix :")
        if st.button("Générer Plan"):
            st.session_state.choix = choix
            st.session_state.step = 4
            st.rerun()

    # ETAPE 4 : PLAN
    elif st.session_state.step == 4:
        st.subheader("Plan Tactique")
        if not st.session_state.plan:
            with st.spinner("Rédaction..."):
                res, _ = get_strategic_response(PROMPT_PLAN.format(selected_angle=st.session_state.choix))
                st.session_state.plan = res
        
        st.markdown(st.session_state.plan)
        st.download_button("Télécharger", st.session_state.plan, "Plan.md")
        
        # Rappel Email à la fin
        st.info("Besoin d'aide pour exécuter ?")
        # On régénère le lien avec le plan cette fois
        final_link = create_mailto_link(st.session_state.choix, st.session_state.plan)
        st.link_button("📧 Envoyer le plan à l'équipe", final_link)
        
        if st.button("Recommencer"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
