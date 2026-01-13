import streamlit as st
import google.generativeai as genai
import urllib.parse 

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="L'Architecte (Pro)", page_icon="🏗️", layout="centered")

# --- 🔴 VOTRE EMAIL ICI 🔴 ---
EMAIL_CONTACT = "votre-email@gmail.com" 
# -----------------------------

if st.sidebar.button("♻️ RESET COMPLET"):
    st.session_state.clear()
    st.rerun()

# --- 2. INITIALISATION ---
defaults = {'logged_in': False, 'step': 1, 'audit': "", 'summary': "", 'model_used': "En attente", 
            'idea': "", 'pivot': "", 'plan': "", 'choix': ""}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 3. CONNEXION ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ Pas de Clé API.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

# --- 4. FONCTIONS IA (CERVEAU + RÉSUMEUR) ---

def get_strategic_response(prompt_text):
    """Le Cerveau Principal (Audit Détaillé)"""
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt_text)
        return response.text, "gemini-2.5-pro"
    except:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt_text)
            return response.text, "gemini-2.5-flash"
        except Exception as e:
            return f"❌ Erreur : {e}", "Aucun"

def get_email_summary(full_audit_text):
    """
    L'Agent Résumeur : Transforme l'audit long en un email court et percutant.
    Utilise le modèle Flash pour aller très vite.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt_summary = f"""
        Tâche : Résume cet audit stratégique en un email court pour un consultant.
        Contraintes :
        - Maximum 10-12 lignes.
        - Pas de markdown (gras/italique) car c'est pour un lien mailto.
        - Reste factuel et direct.
        - Structure : 1. Le Verdict, 2. Les 3 risques majeurs identifiés.
        
        TEXTE SOURCE :
        {full_audit_text}
        """
        
        response = model.generate_content(prompt_summary)
        return response.text
    except:
        return "Résumé indisponible. Voir l'audit complet."

# --- 5. FONCTION LINK (PROPRE) ---
def create_mailto_link(idea, summary):
    subject = "SOS Architecte - Demande d'avis"
    
    # On nettoie l'idée pour qu'elle soit courte dans le mail
    safe_idea = idea[:200] + "..." if len(idea) > 200 else idea

    body = f"""Bonjour,

J'ai besoin d'un regard humain sur mon projet.

--- MON IDÉE ---
{safe_idea}

--- RÉSUMÉ DE L'AUDIT IA ---
{summary}

----------------
(J'aimerais savoir si je dois pivoter ou persévérer...)
"""
    safe_subject = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)
    
    return f"mailto:{EMAIL_CONTACT}?subject={safe_subject}&body={safe_body}"

# --- 6. PROMPTS ---
PROMPT_AUDIT = """
RÔLE : Avocat du Diable & Stratège.
MISSION : Analyse sans pitié.
LIVRABLE :
1. 🏁 **VERDICT** : GO / NO-GO / PIVOT (Majuscules).
2. 🛡️ **PRE-MORTEM** : 3 raisons fatales.
3. 📊 **MATRICE D.U.R.** (/10).
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

# --- 7. INTERFACE ---
def main():
    st.title("🏗️ L'Architecte")
    st.caption("v7.0 - Email Summary Agent")

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
                # 1. On lance l'Audit complet (Lourd)
                with st.spinner("1/2 Analyse des risques..."):
                    audit_res, model_name = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    st.session_state.audit = audit_res
                    st.session_state.model_used = model_name
                    st.session_state.idea = user_idea
                
                # 2. On lance le Résumé Email (Léger)
                with st.spinner("2/2 Préparation du rapport email..."):
                    summary_res = get_email_summary(audit_res)
                    st.session_state.summary = summary_res
                    
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2 : RÉSULTAT
    elif st.session_state.step == 2:
        st.caption(f"Cerveau : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        # --- LOGIQUE INTELLIGENTE ---
        # On utilise le RÉSUMÉ pour le lien mail, pas le texte entier
        link = create_mailto_link(st.session_state.idea, st.session_state.summary)
        
        verdict_negatif = "NO-GO" in st.session_state.audit or "PIVOT" in st.session_state.audit
        
        st.markdown("---")
        
        if verdict_negatif:
            st.error("🚨 **ALERTE PROJET**")
            st.write("Le diagnostic est sévère.")
            st.link_button("📧 Envoyer le rapport (Résumé) à l'Architecte", link)
        else:
            st.success("✅ **POTENTIEL DÉTECTÉ**")
            st.write("Le projet est solide.")
            st.link_button("🚀 Envoyer pour validation (Résumé)", link)
            
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
                
                # On génère aussi un petit résumé du plan pour le mail final
                st.session_state.summary = get_email_summary(res)
        
        st.markdown(st.session_state.plan)
        st.download_button("Télécharger", st.session_state.plan, "Plan.md")
        
        final_link = create_mailto_link(st.session_state.choix, st.session_state.summary)
        st.info("Besoin d'aide ?")
        st.link_button("📧 Envoyer le plan à l'équipe", final_link)
        
        if st.button("Recommencer"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
