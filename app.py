import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🚀", layout="wide")

try:
    # Récupération des secrets
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] 
    LINK_AUDIT = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    
    # Initialisation des clients
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"❌ Erreur Config : {e}")
    st.stop()

# --- 2. GESTION DE L'ÉTAT (SESSION) ---
if "user" not in st.session_state: st.session_state.user = None
if "step_unlocked" not in st.session_state: st.session_state.step_unlocked = 1
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"
if "project_data" not in st.session_state: 
    st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- 3. FONCTIONS CRITIQUES (COEUR DU SYSTÈME) ---

def handle_login_signup(email):
    """
    Gestion stricte : 
    1. Si l'email existe -> On charge le compte (pas de cadeaux).
    2. Si nouveau -> On crée la ligne avec un code temporaire pour satisfaire Supabase
       et déclencher l'automatisation Make.
    """
    email = str(email).strip().lower()
    
    try:
        # A. VÉRIFICATION D'ANTÉRIORITÉ (Anti-Triche)
        existing = supabase.table("users").select("*").eq("email", email).execute()
        
        if existing.data and len(existing.data) > 0:
            # L'utilisateur existe déjà : on le retourne tel quel (avec son solde actuel)
            return existing.data[0]
        
        else:
            # B. CRÉATION (Signal pour Make)
            # On met "WAITING_MAKE" pour satisfaire la contrainte NOT NULL de la base de données
            # Make détectera cette nouvelle ligne et fera son travail (emailing, génération code, etc.)
            new_user_data = {
                "email": email,
                "credits": 3,              # Crédits de bienvenue
                "access_code": "WAITING_MAKE" # Placeholder technique indispensable
            }
            
            created = supabase.table("users").insert(new_user_data).execute()
            
            if created.data:
                return created.data[0]
                
    except Exception as e:
        st.error(f"Erreur de communication Base de Données : {e}")
    return None

def debit_credits_secure(current_user):
    """
    Débite 1 crédit sur l'email (Clé unique).
    Met à jour l'interface immédiatement.
    """
    email = current_user["email"]
    
    # 1. Update Session (Interface fluide)
    current_val = st.session_state.user["credits"]
    new_val = max(0, current_val - 1)
    st.session_state.user["credits"] = new_val
    
    # 2. Update DB (Arrière-plan)
    try:
        supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
    except: pass

def save_json():
    return json.dumps({"step": st.session_state.step_unlocked, "data": st.session_state.project_data})

def load_json(f):
    try:
        d = json.load(f)
        st.session_state.step_unlocked = d.get("step", 1)
        st.session_state.project_data = d.get("data", {})
        st.session_state.current_view = "1. Analyse"
        st.rerun()
    except: pass

# --- 4. ÉCRAN DE DÉMARRAGE (EMAIL SEUL) ---
if not st.session_state.user:
    st.title("🚀 Stratège IA")
    st.markdown("### Espace de Travail")
    st.write("Entrez votre email pour accéder à vos dossiers ou démarrer un essai.")
    
    c1, c2 = st.columns([3, 1])
    with c1:
        email_input = st.text_input("Email professionnel :", placeholder="exemple@entreprise.com")
    with c2:
        st.write("")
        st.write("")
        if st.button("Accéder / Démarrer", use_container_width=True):
            if email_input and "@" in email_input:
                with st.spinner("Connexion sécurisée..."):
                    u = handle_login_signup(email_input)
                    if u:
                        st.session_state.user = u
                        st.rerun()
            else:
                st.warning("Format d'email incorrect.")
    st.stop()

# --- 5. APPLICATION (INTERFACE CONNECTÉE) ---
user = st.session_state.user
credits = user.get("credits", 0)

# === BARRE LATÉRALE ===
with st.sidebar:
    st.header("Compte")
    st.caption(f"👤 {user['email']}")
    
    if credits > 0:
        st.metric("Crédits Dispo", credits)
        st.success("✅ Actif")
    else:
        st.metric("Crédits", 0)
        st.error("❌ Épuisé")
        st.markdown("Pour continuer, rechargez votre compte.")
        st.link_button("💳 Recharger (Accès Illimité)", LINK_RECHARGE, type="primary")
    
    st.divider()
    # Navigation Dynamique
    opts = ["1. Analyse"]
    if st.session_state.step_unlocked >= 2: opts.append("2. Pivots")
    if st.session_state.step_unlocked >= 3: opts.append("3. GPS")
    
    try: idx = opts.index(st.session_state.current_view)
    except: idx = 0
    nav = st.radio("Navigation :", opts, index=idx)
    
    if nav != st.session_state.current_view:
        st.session_state.current_view = nav
        st.rerun()
        
    st.divider()
    st.download_button("💾 Sauvegarder JSON", save_json(), "projet_strategie.json")
    up = st.file_uploader("📂 Charger JSON", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# === CONTENU CENTRAL ===
st.title("🧠 Stratège IA")
step_n = int(st.session_state.current_view.split(".")[0])
st.progress(step_n / 3)

# --- VUE 1 : ANALYSE ---
if step_n == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    
    # A. Affichage résultat existant
    if st.session_state.project_data["analysis"]:
        st.info(f"Projet analysé : {st.session_state.project_data['idea']}")
        st.markdown(st.session_state.project_data["analysis"])
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➡️ Passer à l'étape 2 (Pivots)", type="primary"):
                st.session_state.step_unlocked = max(st.session_state.step_unlocked, 2)
                st.session_state.current_view = "2. Pivots"
                st.rerun()
        with c2:
            with st.expander("Modifier & Relancer (Coût: 1 crédit)"):
                new_i = st.text_area("Version corrigée :", value=st.session_state.project_data["idea"])
                if st.button("Relancer l'analyse"):
                    if credits > 0:
                        st.session_state.project_data["idea"] = new_i
                        # Reset des étapes suivantes pour cohérence
                        st.session_state.project_data["pivots"] = ""
                        st.session_state.project_data["gps"] = ""
                        
                        with st.spinner("Analyse V2..."):
                            res = model.generate_content(f"Analyse critique business de : {new_i}. Format Markdown.")
                            st.session_state.project_data["analysis"] = res.text
                            debit_credits_secure(user)
                            st.rerun()
                    else: st.error("Crédits insuffisants.")

    # B. Formulaire nouveau projet
    else:
        if credits > 0:
            txt = st.text_area("Décrivez votre idée de business :", height=150)
            if st.button("Lancer l'Analyse (1 crédit)"):
                if txt:
                    st.session_state.project_data["idea"] = txt
                    with st.spinner("L'IA réfléchit..."):
                        p = f"Rôle: Expert Business Stratège. Tâche: Analyse critique sans concession de '{txt}'. Output: 1.Macro, 2.Failles, 3.Verdict. Format Markdown."
                        res = model.generate_content(p)
                        st.session_state.project_data["analysis"] = res.text
                        st.session_state.step_unlocked = 2
                        debit_credits_secure(user)
                        st.rerun()
        else:
            st.warning("⚠️ Votre solde de crédits est épuisé.")
            st.markdown(f"👉 **[Cliquez ici pour obtenir un accès complet]({LINK_RECHARGE})**")

# --- VUE 2 : PIVOTS ---
elif step_n == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    
    # Auto-génération
    if not st.session_state.project_data["pivots"]:
        with st.spinner("Recherche de modèles économiques alternatifs..."):
            res = model.generate_content(f"Propose 3 pivots business radicaux et rentables pour : {st.session_state.project_data['idea']}")
            st.session_state.project_data["pivots"] = res.text
            st.rerun()
            
    st.markdown(st.session_state.project_data["pivots"])
    st.divider()
    
    # Sélection
    opts_p = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    try: i = opts_p.index(st.session_state.project_data["choice"])
    except: i = 0
    
    ch = st.radio("Quelle stratégie choisissez-vous ?", opts_p, index=i)
    
    if st.button("Valider et Générer le Plan d'Action"):
        st.session_state.project_data["choice"] = ch
        st.session_state.project_data["gps"] = "" # On efface le GPS pour forcer le recalcul
        st.session_state.step_unlocked = 3
        st.session_state.current_view = "3. GPS"
        st.rerun()

# --- VUE 3 : GPS ---
elif step_n == 3:
    st.subheader("3️⃣ GPS (Plan d'Exécution)")
    fin = f"{st.session_state.project_data['idea']} (Stratégie: {st.session_state.project_data['choice']})"
    st.info(f"📍 Destination : {fin}")
    
    if not st.session_state.project_data["gps"]:
        if st.button("Calculer l'itinéraire"):
            with st.spinner("Calcul du plan d'action COO..."):
                res = model.generate_content(f"Agis comme un COO. Donne un plan d'action concret pour : {fin}. Objectifs 90j, Roadmap 30j.")
                st.session_state.project_data["gps"] = res.text
                st.rerun()
                
    if st.session_state.project_data["gps"]:
        st.markdown(st.session_state.project_data["gps"])
        st.divider()
        
        c_audit, c_new = st.columns(2)
        with c_audit:
            st.link_button("💎 Demander un Audit Humain", LINK_AUDIT, type="primary")
        with c_new:
            if st.button("🔄 Nouveau Projet (Reset)"):
                st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
                st.session_state.step_unlocked = 1
                st.session_state.current_view = "1. Analyse"
                st.rerun()
                
