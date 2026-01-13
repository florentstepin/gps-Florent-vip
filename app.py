import streamlit as st
import google.generativeai as genai
import urllib.parse
import sqlite3
import uuid

# --- 1. CONFIGURATION ---
FORM_URL = "https://docs.google.com/forms/d/e/VOTRE_ID_DE_FORMULAIRE/viewform"
ENTRY_ID_EMAIL = "121343077"
ENTRY_ID_IDEA =  "1974870243"
ENTRY_ID_AUDIT = "1147735867"
EMAIL_CONTACT = "photos.studio.ia@gmail.com"

# VOTRE CODE MAÎTRE (Vérifiez qu'il correspond exactement à votre URL)
MASTER_CODE = "BOSS-2026" 
# ------------------------

st.set_page_config(page_title="L'Architecte", page_icon="🏗️", layout="centered")

# --- 2. BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (access_code TEXT PRIMARY KEY, credits INT, total_runs INT)''')
    conn.commit()
    conn.close()

def get_user_credits(code):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute("SELECT credits, total_runs FROM users WHERE access_code=?", (code,))
    result = c.fetchone()
    conn.close()
    return result

def decrement_credits(code):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits - 1, total_runs = total_runs + 1 WHERE access_code=?", (code,))
    conn.commit()
    conn.close()

def create_new_user(credits=50):
    conn = sqlite3.connect('clients.db')
    c = conn.cursor()
    new_code = "KEY-" + str(uuid.uuid4())[:8].upper()
    c.execute("INSERT INTO users VALUES (?, ?, 0)", (new_code, credits))
    conn.commit()
    conn.close()
    return new_code

init_db()

# --- 3. SESSION ---
defaults = {'logged_in': False, 'is_admin': False, 'user_code': None, 'credits_left': 0, 'total_runs': 0,
            'step': 1, 'audit': "", 'summary': "", 'idea': "", 'plan': "", 'pivot': ""}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 4. IA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("❌ Pas de Clé API.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")
    st.stop()

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
        prompt = f"Résume ceci en 15 lignes pour formulaire contact. Pas de markdown.\nTEXTE: {full_audit_text}"
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Voir rapport."

def create_google_form_link(idea, audit_summary):
    safe_idea = urllib.parse.quote(idea[:500])
    safe_audit = urllib.parse.quote(audit_summary)
    return f"{FORM_URL}?entry.{ENTRY_ID_IDEA}={safe_idea}&entry.{ENTRY_ID_AUDIT}={safe_audit}"

# PROMPTS
PROMPT_AUDIT = "RÔLE : Avocat du Diable. LIVRABLE : 1. VERDICT, 2. Risques, 3. Matrice DUR. PROJET : {user_idea}"
PROMPT_PIVOT = "RÔLE : Innovation. MISSION : 5 Pivots radicaux. PROJET : {user_idea}"
PROMPT_PLAN = "RÔLE : Chef de projet. OBJECTIF : Vente J+7. LIVRABLE : Plan d'action. STRATÉGIE : {selected_angle}"

# --- 5. LOGIQUE DE CONNEXION ---
def attempt_login(code_input):
    # On nettoie le code (espaces, majuscules forcées)
    clean_code = str(code_input).strip()
    
    # DEBUG : Voir ce que l'ordi reçoit vraiment
    # st.write(f"Debug: Code reçu = '{clean_code}' vs Master = '{MASTER_CODE}'") 

    # GOD MODE
    if clean_code == MASTER_CODE:
        st.session_state.logged_in = True
        st.session_state.is_admin = True
        st.session_state.user_code = "ADMIN"
        st.session_state.credits_left = 999999
        return True, "Admin connecté"
    
    # CLIENT MODE
    user_data = get_user_credits(clean_code)
    if user_data:
        credits, runs = user_data
        if credits > 0:
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.session_state.user_code = clean_code
            st.session_state.credits_left = credits
            st.session_state.total_runs = runs
            return True, "Client connecté"
        else:
            return False, "🔒 Crédits épuisés."
    else:
        return False, f"❌ Code inconnu : {clean_code}"

# --- 6. INTERFACE PRINCIPALE ---
def main():
    
    st.title("🏗️ L'Architecte")

    # A. DÉTECTION URL RENFORCÉE
    if not st.session_state.logged_in:
        try:
            # On tente de récupérer le code (nouvelle méthode)
            url_code = st.query_params.get("code", None)
            
            # Si vide, on tente l'ancienne méthode (au cas où)
            if not url_code:
                try:
                    params = st.experimental_get_query_params()
                    url_code = params.get("code", [None])[0]
                except:
                    pass

            if url_code:
                success, msg = attempt_login(url_code)
                if success:
                    st.success(f"🔓 Connexion auto : {msg}")
                    st.rerun()
                else:
                    # Affiche l'erreur si le code URL est rejeté (très utile pour débugger)
                    st.warning(f"⚠️ Lien détecté mais connexion échouée : {msg}")
        except Exception as e:
            # En cas de crash bizarre sur les URL
            st.caption(f"Info chargement : {e}")

    # B. ÉCRAN DE CONNEXION MANUEL
    if not st.session_state.logged_in:
        with st.form("login"):
            st.markdown("### Identification")
            code_input = st.text_input("Code d'Accès", placeholder="Collez votre code ici...")
            if st.form_submit_button("Entrer"):
                success, msg = attempt_login(code_input)
                if success:
                    st.rerun()
                else:
                    st.error(msg)
        st.stop()

    # C. APPLICATION CONNECTÉE
    
    # SIDEBAR
    with st.sidebar:
        if st.session_state.is_admin:
            st.header("👑 God Mode")
            st.subheader("Générateur de Codes")
            if st.button("Créer Code Client (50 crédits)"):
                new_code = create_new_user(50)
                st.code(new_code, language=None)
                
                # Générateur de lien magique
                # Astuce : On récupère l'URL actuelle du navigateur si possible, sinon on met un placeholder
                st.caption("Lien à envoyer :")
                st.code(f"https://[VOTRE-APP].streamlit.app/?code={new_code}", language=None)
                st.success("Code ajouté !")
        else:
            st.header("Mon Espace")
            st.info(f"Code : {st.session_state.user_code}")
            st.metric("Crédits restants", st.session_state.credits_left)
        
        st.divider()
        if st.button("Déconnexion"):
            st.session_state.clear()
            st.rerun()

    # SUITE DE L'APP...
    is_client = not st.session_state.is_admin
    is_last_free_trial = (is_client and st.session_state.total_runs == 2) 

    if st.session_state.step == 1:
        st.subheader("Audit Stratégique")
        
        if is_client and st.session_state.total_runs < 3:
            st.info(f"🌱 Essai Gratuit : {st.session_state.total_runs + 1}/3")
        
        user_idea = st.text_area("Votre idée :", height=120)
        launch_btn = st.button("Lancer l'Audit")

        confirm = True
        if is_last_free_trial:
            st.warning("⚠️ DERNIER ESSAI GRATUIT")
            st.error("En validant, vous renoncez à la garantie de remboursement.")
            confirm = st.checkbox("J'accepte ces conditions.")

        if launch_btn:
            if not confirm:
                st.toast("Cochez la case pour continuer.")
            elif user_idea:
                if is_client:
                    decrement_credits(st.session_state.user_code)
                    st.session_state.credits_left -= 1
                    st.session_state.total_runs += 1
                
                with st.spinner("Analyse..."):
                    audit, model = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    st.session_state.audit = audit
                    st.session_state.model_used = model
                    st.session_state.idea = user_idea
                    st.session_state.summary = get_email_summary(audit)
                    st.session_state.step = 2
                    st.rerun()

    elif st.session_state.step == 2:
        st.caption(f"Cerveau : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        verdict_negatif = "NO-GO" in st.session_state.audit or "PIVOT" in st.session_state.audit
        form_link = create_google_form_link(st.session_state.idea, st.session_state.summary)
        
        st.markdown("---")
        if verdict_negatif:
            st.error("🚨 **PROJET À RISQUE**")
            st.link_button("📤 Envoyer le dossier", form_link)
        else:
            st.success("✅ **POTENTIEL CONFIRMÉ**")
            st.link_button("🚀 Candidater", form_link)
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Pivoter"):
                with st.spinner("Recherche..."):
                    res, _ = get_strategic_response(PROMPT_PIVOT.format(user_idea=st.session_state.idea))
                    st.session_state.pivot = res
                    st.session_state.step = 3
                    st.rerun()
        with col2:
            if st.button("📋 Plan d'Action"):
                st.session_state.choix = st.session_state.idea
                st.session_state.step = 4
                st.rerun()
        
        if
