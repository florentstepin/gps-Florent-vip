import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🧠", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] 
    LINK_AUDIT = "https://docs.google.com/forms/d/1B93XGdlUzsSDKMQmGPDNcSK3hT91z_1Tvy3808UWS5A/viewform"
    
    # Configuration FORMULAIRE (À modifier avec VOS codes si besoin)
    BASE_FORM_URL = LINK_AUDIT
    
    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"❌ Erreur Config : {e}")
    st.stop()

# --- INITIALISATION SESSION (ROBUSTE) ---
if "user" not in st.session_state: st.session_state.user = None
if "step_unlocked" not in st.session_state: st.session_state.step_unlocked = 1
if "current_view" not in st.session_state: st.session_state.current_view = "1. Analyse"
# Structure de données vide par défaut
def get_empty_data():
    return {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

if "project_data" not in st.session_state: 
    st.session_state.project_data = get_empty_data()

# --- FONCTIONS CRITIQUES ---

def reset_app():
    """Efface TOUT et recharge l'application à zéro."""
    st.session_state.project_data = get_empty_data()
    st.session_state.step_unlocked = 1
    st.session_state.current_view = "1. Analyse"
    st.rerun()

def verifier_et_connecter(email_saisi):
    """Logique de connexion V23 : Priorité à la lecture existante"""
    email_propre = str(email_saisi).strip().lower()
    try:
        # 1. On cherche l'utilisateur
        recherche = supabase.table("users").select("*").eq("email", email_propre).execute()
        if recherche.data:
            # On retourne l'utilisateur existant (avec ses vrais crédits)
            return recherche.data[0]
        else:
            # 2. Création (Seulement si inexistant)
            nouveau_compte = {
                "email": email_propre,
                "credits": 3, # Force 3 crédits à la création
                "access_code": "WAITING_MAKE"
            }
            creation = supabase.table("users").insert(nouveau_compte).execute()
            if creation.data: return creation.data[0]
    except Exception as e:
        st.error(f"Erreur connexion : {e}")
    return None

def debiter_1_credit(utilisateur):
    """Débite et met à jour SESSION + DB"""
    email_cible = utilisateur["email"]
    # On récupère le solde actuel de la session pour être sûr
    credits_actuels = st.session_state.user.get("credits", 0)
    nouveau_solde = max(0, credits_actuels - 1)
    
    # 1. Update Session Immédiat
    st.session_state.user["credits"] = nouveau_solde
    
    # 2. Update DB
    try:
        supabase.table("users").update({"credits": nouveau_solde}).eq("email", email_cible).execute()
    except: pass

def save_json():
    return json.dumps({"step": st.session_state.step_unlocked, "data": st.session_state.project_data}, indent=4)

def load_json(f):
    try:
        d = json.load(f)
        # On écrase tout proprement
        st.session_state.step_unlocked = d.get("step", 1)
        st.session_state.project_data = d.get("data", {})
        st.session_state.current_view = "1. Analyse"
        st.success("Dossier chargé avec succès.")
        time.sleep(0.5)
        st.rerun()
    except: 
        st.error("Fichier invalide.")

def afficher_logo():
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("Stratège IA")

# --- LOGIN SCREEN ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        st.title("🚀 Stratège IA")
        st.write("Identifiez-vous par email professionnel.")
        
        saisie_email = st.text_input("Votre Email :", placeholder="exemple@business.com")
        if st.button("Accéder à l'espace", use_container_width=True):
            if saisie_email and "@" in saisie_email:
                with st.spinner("Connexion sécurisée..."):
                    compte = verifier_et_connecter(saisie_email)
                    if compte:
                        st.session_state.user = compte
                        st.rerun()
            else: st.warning("Email invalide.")
    st.stop()

# --- APPLICATION ---
user = st.session_state.user
credits = user.get("credits", 0)

# === SIDEBAR ===
with st.sidebar:
    afficher_logo()
    st.caption(f"Compte : {user.get('email')}")
    
    if credits > 0:
        st.metric("Crédits Dispo", credits)
    else:
        st.error("Crédits Épuisés")
        st.link_button("💳 Recharger", LINK_RECHARGE, type="primary")
    
    st.divider()
    
    # --- ZONE EXPERT ---
    st.info("💎 **Expertise Humaine**")
    st.link_button("Réserver un Audit Humain", LINK_AUDIT, type="primary", use_container_width=True)
    
    # KIT COPIER-COLLER (Affichage conditionnel)
    if st.session_state.project_data.get("idea"):
        with st.expander("📝 Infos pour le formulaire"):
            st.caption("1. Copiez l'idée :")
            st.code(st.session_state.project_data["idea"], language="text")
            if st.session_state.project_data.get("analysis"):
                st.caption("2. Copiez l'audit IA :")
                resume = st.session_state.project_data["analysis"][:4000]
                st.code(resume, language="text")

    st.divider()
    
    # NAVIGATION
    st.markdown("### 🧭 Navigation")
    opts = ["1. Analyse"]
    if st.session_state.step_unlocked >= 2: opts.append("2. Pivots")
    if st.session_state.step_unlocked >= 3: opts.append("3. GPS")
    
    try: idx = opts.index(st.session_state.current_view)
    except: idx = 0
    nav = st.radio("Étapes :", opts, index=idx, label_visibility="collapsed")
    
    if nav != st.session_state.current_view:
        st.session_state.current_view = nav
        st.rerun()
        
    st.divider()
    
    # BOUTON "NOUVELLE ANALYSE" (Avec Reset Total)
    if st.button("✨ Nouvelle Analyse", type="secondary", use_container_width=True):
        reset_app()

    st.download_button("💾 Sauvegarder JSON", save_json(), "projet.json", use_container_width=True)
    up = st.file_uploader("📂 Charger JSON", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# === CONTENU CENTRAL ===
st.title("🧠 Stratège IA")
step_n = int(st.session_state.current_view.split(".")[0])
st.progress(step_n / 3)

# PHASE 1 : ANALYSE
if step_n == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    
    # A. Mode Résultats
    if st.session_state.project_data.get("analysis"):
        st.info(f"Sujet : {st.session_state.project_data['idea']}")
        st.markdown(st.session_state.project_data["analysis"])
        
        if st.button("Passer à l'étape suivante (Pivots) ➡️", type="primary"):
            st.session_state.step_unlocked = max(st.session_state.step_unlocked, 2)
            st.session_state.current_view = "2. Pivots"
            st.rerun()
            
        with st.expander("Modifier et Relancer (1 crédit)"):
            n = st.text_area("Correction :", value=st.session_state.project_data["idea"])
            if st.button("Relancer l'analyse"):
                if credits > 0:
                    st.session_state.project_data["idea"] = n
                    # THINKING
                    with st.status("🕵️‍♂️ L'IA analyse votre projet...", expanded=True) as status:
                        st.write("Analyse du contexte macro-économique...")
                        time.sleep(1)
                        st.write("Recherche des failles de marché...")
                        time.sleep(1)
                        st.session_state.project_data["analysis"] = model.generate_content(f"Analyse critique: {n}").text
                        status.update(label="✅ Analyse terminée !", state="complete", expanded=False)
                    
                    # Reset suite
                    st.session_state.project_data["pivots"] = ""
                    st.session_state.project_data["gps"] = ""
                    debiter_1_credit(user)
                    st.rerun()
                else: st.error("Solde nul")
    
    # B. Mode Formulaire Vierge
    else:
        if credits > 0:
            t = st.text_area("Décrivez votre idée de business :", height=150, key="input_idea_main")
            if st.button("Lancer l'Analyse (1 crédit)", type="primary"):
                if t:
                    st.session_state.project_data["idea"] = t
                    # THINKING
                    with st.status("🧠 Activation du Stratège IA...", expanded=True) as status:
                        st.write("Lecture de votre idée...")
                        time.sleep(0.5)
                        st.write("🔍 Scan des concurrents...")
                        time.sleep(1)
                        st.write("📝 Rédaction du rapport...")
                        st.session_state.project_data["analysis"] = model.generate_content(f"Analyse critique: {t}").text
                        status.update(label="✅ Rapport généré !", state="complete", expanded=False)
                    
                    st.session_state.step_unlocked = 2
                    debiter_1_credit(user)
                    st.rerun()
        else: st.warning("Veuillez recharger vos crédits.")

# PHASE 2 : PIVOTS
elif step_n == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    st.info(f"📌 **Projet :** {st.session_state.project_data.get('idea')}")
    
    if not st.session_state.project_data.get("pivots"):
        with st.status("💡 Recherche de Pivots en cours...", expanded=True) as status:
            st.write("🔄 Analyse des Business Models alternatifs...")
            time.sleep(1.5)
            st.write("🚀 Brainstorming des stratégies de scalabilité...")
            time.sleep(1.5)
            st.write("✍️ Formalisation des 3 options...")
            res = model.generate_content(f"3 Pivots business pour: {st.session_state.project_data['idea']}").text
            st.session_state.project_data["pivots"] = res
            status.update(label="✅ 3 Stratégies trouvées !", state="complete", expanded=False)
        st.rerun()

    st.markdown(st.session_state.project_data["pivots"])
    st.divider()
    
    st.markdown("### Faire un choix")
    ops = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    try: i = ops.index(st.session_state.project_data.get("choice"))
    except: i = 0
    c = st.radio("Sur quelle stratégie part-on ?", ops, index=i)
    
    if st.button("Valider ce choix et Générer le GPS", type="primary"):
        st.session_state.project_data["choice"] = c
        st.session_state.project_data["gps"] = "" # Reset GPS
        st.session_state.step_unlocked = 3
        st.session_state.current_view = "3. GPS"
        st.rerun()

# PHASE 3 : GPS
elif step_n == 3:
    st.subheader("3️⃣ GPS : Plan d'Action")
    f_sub = f"{st.session_state.project_data['idea']} ({st.session_state.project_data['choice']})"
    st.info(f"🎯 **Cible validée :** {f_sub}")
    
    if not st.session_state.project_data.get("gps"):
        if st.button("Calculer l'itinéraire"):
            with st.status("🗺️ Calcul de l'itinéraire...", expanded=True) as status:
                st.write("📅 Définition des objectifs à 90 jours...")
                time.sleep(1)
                st.write("⚡ Identification des actions immédiates...")
                res = model.generate_content(f"Plan d'action COO: {f_sub}").text
                st.session_state.project_data["gps"] = res
                status.update(label="✅ Itinéraire prêt !", state="complete", expanded=False)
            st.rerun()

    if st.session_state.project_data.get("gps"):
        st.markdown(st.session_state.project_data["gps"])
        st.divider()
        st.success("Plan généré.")
        st.link_button("💎 Réserver mon Audit de mise en œuvre", LINK_AUDIT, type="primary")
