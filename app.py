import streamlit as st
import google.generativeai as genai
import urllib.parse 

# --- 1. CONFIGURATION GOOGLE FORM (A REMPLIR PAR VOUS) ---
# Copiez l'URL de base de votre formulaire (tout ce qui est avant le '?')
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"

# Mettez ici les numéros "entry.XXXXX" que vous avez trouvés à l'étape 1
# Attention : ne mettez QUE le numéro (ex: '12345678')
ENTRY_ID_EMAIL = "121343077"  # ID du champ pour l'Email client (Optionnel ou mettre un champ vide)
ENTRY_ID_IDEA =  "1974870243"  # ID du champ pour "L'Idée"
ENTRY_ID_AUDIT = "1147735867"  # ID du champ pour "L'Audit"

# Votre Email de contact (affiché en secours)
EMAIL_CONTACT = "photos.studio.ia@gmail.com"
# ---------------------------------------------------------

st.set_page_config(page_title="L'Architecte (Pro)", page_icon="🏗️", layout="centered")

if st.sidebar.button("♻️ RESET COMPLET"):
    st.session_state.clear()
    st.rerun()

# --- INITIALISATION ---
defaults = {'logged_in': False, 'step': 1, 'audit': "", 'summary': "", 'model_used': "En attente", 
            'idea': "", 'pivot': "", 'plan': "", 'choix': ""}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- CONNEXION ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ Pas de Clé API.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

# --- IA ---
def get_strategic_response(prompt_text):
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
    """On fait un résumé pour être sûr que ça rentre dans l'URL du Form"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Résume ceci en 15 lignes claires pour un formulaire de contact. Pas de markdown.\nTEXTE: {full_audit_text}"
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Voir rapport complet."

# --- FONCTION LIEN GOOGLE FORM ---
def create_google_form_link(idea, audit_summary):
    base = FORM_URL
    
    # On encode les textes pour l'URL
    safe_idea = urllib.parse.quote(idea[:500]) # On garde les 500 premiers caractères
    safe_audit = urllib.parse.quote(audit_summary)
    
    # On construit l'URL finale avec vos IDs
    # Structure : URL?entry.ID_IDEE=Texte&entry.ID_AUDIT=Texte
    link = f"{base}?entry.{ENTRY_ID_IDEA}={safe_idea}&entry.{ENTRY_ID_AUDIT}={safe_audit}"
    
    return link

# --- PROMPTS ---
PROMPT_AUDIT = """
RÔLE : Avocat du Diable.
LIVRABLE :
1. 🏁 **VERDICT** : GO / NO-GO / PIVOT (Majuscules).
2. 🛡️ **PRE-MORTEM** : 3 raisons fatales.
3. 📊 **MATRICE D.U.R.** (/10).
PROJET : {user_idea}
"""
PROMPT_PIVOT = "RÔLE : Innovation. MISSION : 5 Pivots radicaux. PROJET : {user_idea}"
PROMPT_PLAN = "RÔLE : Chef de projet. OBJECTIF : Vente J+7. LIVRABLE : Plan d'action. STRATÉGIE : {selected_angle}"

# --- INTERFACE ---
def main():
    st.title("🏗️ L'Architecte")
    st.caption("v11.0 - Google Form Connect")

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
        st.subheader("1. Le Crash-Test")
        user_idea = st.text_area("Votre idée :", height=120)
        
        if st.button("Lancer l'Audit 💥"):
            if user_idea:
                with st.spinner("Analyse..."):
                    audit, model = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    st.session_state.audit = audit
                    st.session_state.model_used = model
                    st.session_state.idea = user_idea
                    st.session_state.summary = get_email_summary(audit)
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2 : RÉSULTAT
    elif st.session_state.step == 2:
        st.caption(f"Cerveau : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        # --- BLOC GOOGLE FORM ---
        verdict_negatif = "NO-GO" in st.session_state.audit or "PIVOT" in st.session_state.audit
        form_link = create_google_form_link(st.session_state.idea, st.session_state.summary)
        
        st.markdown("---")
        
        if verdict_negatif:
            st.error("🚨 **PROJET À RISQUE**")
            st.write("Ne restez pas seul. Soumettez ce dossier pour analyse humaine.")
            st.link_button("📤 Envoyer le dossier à l'Architecte (Formulaire)", form_link)
        else:
            st.success("✅ **POTENTIEL CONFIRMÉ**")
            st.write("Passez à la vitesse supérieure.")
            st.link_button("🚀 Candidater pour l'accompagnement", form_link)
    
        st.caption("Cela ouvrira un formulaire Google pré-rempli avec votre idée et l'audit.")
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
                st.session_state.summary = get_email_summary(res)
        
        st.markdown(st.session_state.plan)
        st.download_button("Télécharger", st.session_state.plan, "Plan.md")
        
        st.info("Besoin d'aide ?")
        # Lien form pour le plan aussi
        plan_link = create_google_form_link(st.session_state.choix, st.session_state.summary)
        st.link_button("📤 Envoyer ce plan à l'équipe", plan_link)
        
        if st.button("Recommencer"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
