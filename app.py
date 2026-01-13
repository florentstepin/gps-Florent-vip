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

# VOTRE CODE MAÎTRE
MASTER_CODE = "BOSS-2026" 
# ------------------------

st.set_page_config(page_title="L'Architecte", page_icon="🏗️", layout="centered")

# --- 2. FONCTIONS SYSTÈME ---
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

# --- 3. SESSION ---
init_db()
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
        # st.error("❌ Pas de Clé API.") # Désactivé pour le debug URL
        pass
except:
    pass

def get_strategic_response(prompt_text):
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt_text)
        return response.text, "gemini-2.5-pro"
    except:
        return "Erreur IA", "Aucun"

def get_email_summary(full_audit_text):
    return "Résumé..."

def create_google_form_link(idea, audit_summary):
    return f"{FORM_URL}"

PROMPT_AUDIT = "..." 
PROMPT_PIVOT = "..."
PROMPT_PLAN = "..."

# --- 5. LOGIQUE LOGIN ---
def attempt_login(code_input):
    clean_code = str(code_input).strip().replace("'", "").replace('"', "")
    
    if clean_code == MASTER_CODE:
        st.session_state.logged_in = True
        st.session_state.is_admin = True
        st.session_state.user_code = "ADMIN"
        st.session_state.credits_left = 999999
        return True, "Admin connecté"
    
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
    return False, f"Code inconnu ({clean_code})"

# --- 6. MAIN AVEC RAYONS X ---
def main():
    
    # === ZONE RAYONS X (DEBUG) ===
    # Affiche TOUT ce que l'application voit dans l'URL
    st.write("--- MODE DEBUG ACTIF ---")
    
    # 1. On récupère les params bruts
    query_params = st.query_params
    st.write(f"🔍 **Contenu brut de l'URL :** `{query_params}`")
    
    # 2. On cherche spécifiquement 'code'
    url_code = query_params.get("code", None)
    st.write(f"🎯 **Code extrait :** `{url_code}`")
    
    st.write(f"🔑 **Code Maître attendu :** `{MASTER_CODE}`")
    st.write("--------------------------")

    # === TENTATIVE AUTO ===
    if not st.session_state.logged_in and url_code:
        success, msg = attempt_login(url_code)
        if success:
            st.success(f"✅ SUCCÈS : {msg}")
            st.button("👉 CLIQUEZ ICI POUR ENTRER", on_click=st.rerun)
            # On arrête tout ici pour forcer le clic
            st.stop()
        else:
            st.error(f"❌ ÉCHEC : {msg}")

    # === ECRAN LOGIN MANUEL ===
    if not st.session_state.logged_in:
        st.title("🏗️ L'Architecte")
        with st.form("login"):
            st.markdown("### Identification")
            code_input = st.text_input("Code d'Accès")
            if st.form_submit_button("Entrer"):
                success, msg = attempt_login(code_input)
                if success:
                    st.rerun()
                else:
                    st.error(msg)
        st.stop()

    # === APPLICATION NORMALE ===
    # (Si on arrive ici, c'est qu'on est connecté)
    
    with st.sidebar:
        st.success("CONNECTÉ ✅")
        if st.session_state.is_admin:
            st.write("👑 **MODE GOD**")
            if st.button("Générer Code"):
                new_code = create_new_user(50)
                st.code(f"https://gps-florent-vip.streamlit.app/?code={new_code}")
        else:
            st.write(f"Client : {st.session_state.user_code}")
        
        if st.button("Déconnexion"):
            st.session_state.clear()
            st.rerun()

    st.title("🏗️ L'Architecte (Connecté)")
    st.write("Bienvenue dans l'espace sécurisé.")
    
    # ... Je simplifie l'affichage pour le test ...
    st.info("Le test de connexion est réussi. Si vous voyez ça, l'auto-login fonctionne.")

if __name__ == "__main__":
    main()
