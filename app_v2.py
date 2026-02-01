import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid 

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🧠", layout="wide")

# Custom CSS pour passer du rouge au Violet Stratège
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #7f5af0; color: white; border: none; }
    div.stButton > button:hover { background-color: #6246ea; color: white; }
    /* Style pour les messages d'info */
    .stAlert { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. RÉCUPÉRATION DES SECRETS & CONNEXIONS ---
try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Configuration Google Form
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.570709531"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"Erreur de configuration (Vérifiez vos Secrets) : {e}")
    st.stop()

# --- 3. INITIALISATION DES VARIABLES ---
if "user" not in st.session_state: st.session_state.user = None
if "project" not in st.session_state:
    st.session_state.project = {
        "idea": "", "context": "", "analysis": "", 
        "pivots": "", "gps": "", "choice": None
    }

# --- 4. FONCTIONS UTILES ---
def login_user(email):
    email = str(email).strip().lower()
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        unique_code = str(uuid.uuid4())
        new = {"email": email, "credits": 2, "access_code": unique_code}        
        res = supabase.table("users").insert(new).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Erreur connexion : {e}")
        return None

def consume_credit():
    if st.session_state.user:
        email = st.session_state.user['email']
        new_val = max(0, st.session_state.user['credits'] - 1)
        try: 
            supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
            st.session_state.user['credits'] = new_val
        except: pass

def load_json(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.project.update(data.get("data", {}))
        st.success("Session restaurée ! Explorez les onglets.")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors de l'import : {e}")

def generate_form_link():
    if not st.session_state.user: return BASE_FORM_URL
    p = st.session_state.project
    
    # Résumé condensé pour le formulaire (max 1500 car.)
    resume = f"--- DOSSIER V2 ---\nIDÉE: {p['idea']}\n\nCONTEXTE: {p.get('context','')}\n\n"
    resume += f"ANALYSE: {p['analysis'][:300]}...\n\nGPS: {p['gps'][:300]}..."
    
    params = {
        ENTRY_EMAIL: st.session_state.user['email'],
        ENTRY_IDEE: p['idea'],
        ENTRY_AUDIT: resume
    }
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

# --- 5. AUTHENTIFICATION ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        st.title("🚀 Accès Stratège IA")
        email_in = st.text_input("Saisissez votre e-mail professionnel")
        if st.button("Se connecter / Créer un compte", use_container_width=True):
            if "@" in email_in:
                u = login_user(email_in)
                if u: 
                    st.session_state.user = u
                    st.rerun()
            else: st.warning("Veuillez entrer un email valide.")
    st.stop()

user = st.session_state.user
credits = user.get("credits", 0)

# --- 6. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    
    # Carte profil
    st.markdown(f"""
    <div style='background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px;'>
        <div style='font-size: 0.8em; opacity: 0.7;'>Session active :</div>
        <div style='font-weight: bold; font-size: 0.9em; overflow: hidden;'>{user['email']}</div>
        <div style='margin-top: 10px; font-weight: bold; color: #7f5af0; font-size: 1.2em;'>🎯 {credits} Crédits</div>
    </div>
    """, unsafe_allow_html=True)

    # Guide de survie par onglets
    with st.popover("❓ Guide de Survie & Méthode", use_container_width=True):
        t_tech, t_meth, t_sauve = st.tabs(["💻 Tech", "🧠 Méthode", "💾 Sauvegarde"])
        with t_tech:
            st.markdown("**⚠️ PAS DE F5** : N'actualisez jamais pendant une analyse.\n\n**Écran** : Gardez votre mobile allumé.")
        with t_meth:
            st.markdown("**Carburant** : Donnez 5-10 lignes de détails.\n\n**Cible** : Soyez précis (ex: 'PME du bâtiment').")
        with t_sauve:
            st.markdown("**JSON** : Exportez pour sauvegarder gratuitement.\n\n**Import** : Rechargez vos dossiers sans payer.")

    st.link_button("⚡ Recharger mes crédits", LINK_RECHARGE, type="primary", use_container_width=True)
    st.divider()

    # Gestion des données
    with st.expander("📂 Gestion de Session", expanded=False):
        json_str = json.dumps({"data": st.session_state.project}, indent=4)
        st.download_button("💾 Exporter JSON", json_str, "projet_stratege.json", use_container_width=True)
        
        up = st.file_uploader("📥 Importer un JSON", type="json")
        if up: load_json(up)
        
        if st.button("✨ Nouveau Projet", use_container_width=True):
            st.session_state.project = {"idea": "", "context": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
            st.rerun()

    # High Ticket (Lien intelligent)
    with st.expander("💎 Expertise Humaine", expanded=True):
        st.markdown("<p style='font-size:0.85em; opacity:0.8;'>Transférez ce dossier à Florent pour un audit approfondi.</p>", unsafe_allow_html=True)
        st.link_button("🚀 Réserver mon Audit", generate_form_link(), use_container_width=True)

    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 7. CORPS DE L'APPLICATION (ONGLETS) ---
st.title("🧠 Stratège IA")

tab1, tab2, tab3 = st.tabs(["🔍 1. Analyse Crash-Test", "💡 2. Pivots Stratégiques", "🗺️ 3. Plan d'Action GPS"])

with tab1:
    if st.session_state.project["analysis"]:
        st.success(f"📌 Analyse du projet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
    else:
        st.info("👋 **Étape 1 : Évaluer les risques.** Décrivez votre idée et votre contexte pour démarrer.")
        col_idea, col_ctx = st.columns(2)
        with col_idea:
            idea_input = st.text_area("Votre idée en quelques phrases :", height=180, placeholder="Ex: Créer une plateforme de mise en relation pour...")
        with col_ctx:
            context_input = st.text_area("Votre contexte (Cible, Budget, Ressources) :", height=180, placeholder="Ex: Solo-preneur, 1500€ de budget, expertise en marketing...")
        
        if st.button("Lancer l'Analyse Crash-Test (1 crédit)", use_container_width=True):
            if idea_input and credits > 0:
                with st.status("🕵️‍♂️ L'IA analyse la viabilité de votre projet...", expanded=True):
                    try:
                        prompt = f"Analyse critique business: {idea_input}\nContexte: {context_input}\nStructure: SWOT, Risques majeurs, Viabilité réelle."
                        res = model.generate_content(prompt).text
                        st.session_state.project.update({"idea": idea_input, "context": context_input, "analysis": res})
                        consume_credit()
                        st.rerun()
                    except Exception as e: st.error(f"Erreur : {e}")
            elif credits <= 0: st.error("Crédits insuffisants. Veuillez recharger dans la barre latérale.")
            else: st.warning("Veuillez décrire votre idée avant de lancer.")

with tab2:
    if not st.session_state.project["analysis"]:
        st.warning("⚠️ Veuillez d'abord réaliser l'étape 1 (Analyse).")
    elif st.session_state.project["pivots"]:
        st.markdown(st.session_state.project["pivots"])
        if st.button("Passer à la création du GPS ➡️", use_container_width=True):
            st.session_state.project["choice"] = "Validé"
            st.rerun()
    else:
        if st.button("Générer 3 Pivots Stratégiques (1 crédit)", use_container_width=True):
            with st.status("💡 Recherche d'angles d'attaque alternatifs...", expanded=True):
                try:
                    res = model.generate_content(f"3 Pivots business pour: {st.session_state.project['idea']}").text
                    st.session_state.project["pivots"] = res
                    consume_credit()
                    st.rerun()
                except Exception as e: st.error(f"Erreur : {e}")

with tab3:
    if not st.session_state.project["choice"]:
        st.warning("⚠️ Veuillez valider l'étape 2 (Pivots) pour générer votre GPS.")
    elif st.session_state.project["gps"]:
        st.markdown(st.session_state.project["gps"])
        st.success("✅ Votre feuille de route est prête. Pensez à l'exporter en JSON !")
    else:
        if st.button("Générer le Plan d'Action GPS (1 crédit)", use_container_width=True):
            with st.status("🗺️ Séquençage des étapes opérationnelles...", expanded=True):
                try:
                    prompt_gps = f"Plan d'action GPS détaillé pour le projet : {st.session_state.project['idea']}\nContexte: {st.session_state.project['context']}"
                    res = model.generate_content(prompt_gps).text
                    st.session_state.project["gps"] = res
                    consume_credit()
                    st.rerun()
                except Exception as e: st.error(f"Erreur : {e}")
