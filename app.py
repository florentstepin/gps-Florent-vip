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

# --- 4. FONCTIONS IA ---
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
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt_summary = f"""
        Tâche : Résume cet audit en un email ultra-court pour un humain.
        Contraintes : 10 lignes MAX. Pas de gras/italique. Style direct.
        TEXTE : {full_audit_text}
        """
        response = model.generate_content(prompt_summary)
        return response.text
    except:
        return "Voir l'audit complet ci-joint."

# --- 5. NOYAU TECHNIQUE (LIENS & BOUTONS HTML) ---

def create_mailto_link(idea, summary):
    subject = "SOS Architecte - Demande d'avis"
    safe_idea = idea[:200] + "..." if len(idea) > 200 else idea
    
    body = f"""Bonjour,
J'ai besoin d'un regard humain sur mon projet.

--- MON IDÉE ---
{safe_idea}

--- RÉSUMÉ IA ---
{summary}

----------------
(Votre message...)
"""
    return f"mailto:{EMAIL_CONTACT}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

def afficher_bouton_email(texte, lien, couleur="#FF4B4B"):
    """
    Crée un bouton HTML qui force l'ouverture dans la même fenêtre (target='_self')
    pour éviter le bug 'about:blank'.
    """
    html_code = f"""
    <a href="{lien}" target="_self" style="text-decoration: none;">
        <div style="
            background-color: {couleur};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            font-family: sans-serif;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: 0.3s;
        ">
            {texte}
        </div>
    </a>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# --- 6. PROMPTS ---
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

# --- 7. INTERFACE ---
def main():
    st.title("🏗️ L'Architecte")
    st.caption("v8.0 - Boutons HTML Natifs")

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
                with st.spinner("Analyse + Résumé..."):
                    # IA 1 : Audit
                    audit, model = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    st.session_state.audit = audit
                    st.session_state.model_used = model
                    st.session_state.idea = user_idea
                    
                    # IA 2 : Résumé Email
                    st.session_state.summary = get_email_summary(audit)
                    
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2 : RÉSULTAT
    elif st.session_state.step == 2:
        st.caption(f"Cerveau : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        # --- BOUTONS HTML ---
        link = create_mailto_link(st.session_state.idea, st.session_state.summary)
        verdict_negatif = "NO-GO" in st.session_state.audit or "PIVOT" in st.session_state.audit
        
        st.markdown("---")
        if verdict_negatif:
            st.error("🚨 **ALERTE PROJET**")
            st.write("Le diagnostic est sévère.")
            # Bouton Rouge (#FF4B4B)
            afficher_bouton_email("📧 Envoyer le rapport (Résumé) à l'Architecte", link, "#FF4B4B")
        else:
            st.success("✅ **POTENTIEL DÉTECTÉ**")
            st.write("Le projet est solide.")
            # Bouton Vert (#00C853)
            afficher_bouton_email("🚀 Envoyer pour validation (Résumé)", link, "#00C853")
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
        
        final_link = create_mailto_link(st.session_state.choix, st.session_state.summary)
        st.info("Besoin d'aide ?")
        # Bouton Bleu (#2962FF)
        afficher_bouton_email("📧 Envoyer le plan à l'équipe", final_link, "#2962FF")
        
        if st.button("Recommencer"):
            st.session_state.clear()
            st.session_state.logged_in = True
            st.rerun()

if __name__ == "__main__":
    main()
