import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid # VITAL POUR MAKE
import re   # <--- NOUVEAU : Pour nettoyer le texte (Regex)

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA V2", page_icon="🔴", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Vos codes Google Form
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    
    # MOTEUR VALIDÉ (2.5 PRO)
    model = genai.GenerativeModel('gemini-2.5-pro')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- 2. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_page" not in st.session_state: st.session_state.current_page = 1
if "user_note" not in st.session_state: st.session_state.user_note = "" # Stockage note client
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- 3. FONCTIONS ---

def login_user(email_recu):
    """Fonction avec MOUCHARDS pour piéger le bug"""
    
    # 1. Nettoyage
    email_propre = str(email_recu).strip().lower()
    
    # --- 🕵️‍♂️ MOUCHARD N°1 : Ce que Python a reçu ---
    st.error(f"🛑 MOUCHARD 1 : J'ai reçu du champ texte -> {email_propre}")
    
    try:
        # A. Vérification
        res = supabase.table("users").select("*").eq("email", email_propre).execute()
        if res.data: 
            st.success("Utilisateur trouvé en base !")
            return res.data[0]
        
        # B. Création
        unique_code = str(uuid.uuid4())
        
        new = {
            "email": email_propre, 
            "credits": 2, 
            "access_code": unique_code 
        }
        
        # --- 🕵️‍♂️ MOUCHARD N°2 : Ce que Python envoie à Supabase ---
        st.info(f"📤 MOUCHARD 2 : J'envoie ce paquet à Supabase -> {new}")
        
        res = supabase.table("users").insert(new).execute()
        
        if res.data: 
            st.balloons() # Si ça marche, ballons !
            return res.data[0]
        
    except Exception as e:
        # Filet de sécurité
        st.error(f"ERREUR CRITIQUE : {e}")
        try:
            res = supabase.table("users").select("*").eq("email", email_propre).execute()
            if res.data: return res.data[0]
        except: 
            pass
    return None
    
    try:
        # A. Vérification existant
        res = supabase.table("users").select("*").eq("email", email_propre).execute()
        if res.data: return res.data[0]
        
        # B. Création
        unique_code = str(uuid.uuid4())
        
        new = {
            "email": email_propre,  # <--- Utilise la variable nettoyée
            "credits": 2, 
            "access_code": unique_code 
        }
        res = supabase.table("users").insert(new).execute()
        if res.data: return res.data[0]
        
    except Exception as e:
        # Filet de sécurité
        try:
            res = supabase.table("users").select("*").eq("email", email_propre).execute()
            if res.data: return res.data[0]
        except: 
            st.error(f"Erreur Login: {e}")
    return None

def consume_credit():
    if st.session_state.user:
        email = st.session_state.user['email']
        new_val = max(0, st.session_state.user['credits'] - 1)
        try: supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
        except: pass
        st.session_state.user['credits'] = new_val

def clean_markdown(text):
    if not text: return ""
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'^\s*[\-\*]\s+', '- ', text, flags=re.MULTILINE)
    return text.strip()

def generate_form_link():
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.project.get("idea", "")
    note_client = st.session_state.user_note
    raw_audit = st.session_state.project.get("analysis", "")
    clean_audit = clean_markdown(raw_audit)
    
    final_content = f"--- PROJET ---\n{idee}\n\n"
    if note_client: final_content += f"--- NOTE ---\n{note_client}\n\n"
    final_content += f"--- AUDIT ---\n{clean_audit[:1200]}..."
    
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: final_content}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.user_note = ""
    st.session_state.current_page = 1
    st.rerun()

def load_json(uploaded_file):
    try:
        uploaded_file.seek(0)
        data = json.load(uploaded_file)
        clean_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean_data.update(data.get("data", {}))
        st.session_state.project = clean_data
        st.session_state.current_page = 1
        st.session_state.last_loaded_signature = f"{uploaded_file.name}_{uploaded_file.size}"
        st.success("Chargé !")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        st.error(f"Erreur JSON : {e}")

# --- 4. LOGIN ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        
        # CHAMP DE SAISIE
        saisie_utilisateur = st.text_input("Email Professionnel")
        
        if st.button("Connexion", use_container_width=True):
            if "@" in saisie_utilisateur:
                # APPEL DE LA FONCTION AVEC LA VARIABLE DE SAISIE
                u = login_user(saisie_utilisateur)
                if u:
                    st.session_state.user = u
                    st.rerun()
            else: st.warning("Email invalide")
    st.stop()

# --- 5. APP ---
user = st.session_state.user
credits = user.get("credits", 0)

with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.write(f"👤 **{user['email']}**")
    if credits > 0: st.metric("Crédits", credits)
    else: 
        st.error("0 Crédits")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")
    
    st.divider()
    st.info("💎 **Expert Humain**")
    
    # --- INPUT DE QUALIFICATION ---
    st.write("Une précision pour l'expert ?")
    st.session_state.user_note = st.text_area("Note optionnelle", 
                                              value=st.session_state.user_note, 
                                              height=70, 
                                              placeholder="Ex: Mon budget est de...",
                                              label_visibility="collapsed")
    
    # Le lien intègre maintenant la note et le texte nettoyé
    st.link_button("Réserver Audit (Pré-rempli)", generate_form_link(), type="primary", use_container_width=True)
    # ------------------------------

    st.divider()
    st.write("### 🧭 Navigation")
    if st.button("1. Analyse"): 
        st.session_state.current_page = 1
        st.rerun()
    if st.session_state.project["analysis"] and st.button("2. Pivots"): 
        st.session_state.current_page = 2
        st.rerun()
    if st.session_state.project["pivots"] and st.button("3. GPS"): 
        st.session_state.current_page = 3
        st.rerun()
    st.divider()
    if st.button("✨ Nouvelle Analyse"): reset_project()
    
    # JSON
    json_str = json.dumps({"data": st.session_state.project}, indent=4)
    st.download_button("💾 Sauver JSON", json_str, "projet_ia.json", mime="application/json")
    
    up = st.file_uploader("📂 Charger JSON", type="json", key="json_uploader")
    if up:
        signature = f"{up.name}_{up.size}"
        if st.session_state.get("last_loaded_signature") != signature:
            with st.spinner("Patientez pendant le téléchargement de votre dossier..."):
                load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

st.title("🧠 Stratège IA")
st.progress(st.session_state.current_page / 3)

# PAGE 1 : ANALYSE
if st.session_state.current_page == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    
    if st.session_state.project["analysis"]:
        st.info(f"Sujet : {st.session_state.project['idea']}")
        st.markdown(st.session_state.project["analysis"])
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Aller aux Pivots ➡️", type="primary"):
                st.session_state.current_page = 2
                st.rerun()
        with c2:
            with st.expander("Modifier et Relancer (1 crédit)"):
                new_txt = st.text_area("Correction", value=st.session_state.project["idea"])
                if st.button("Relancer"):
                    if credits > 0:
                        st.session_state.project["idea"] = new_txt
                        with st.status("🕵️‍♂️ L'Avocat du Diable analyse...", expanded=True) as status:
                            st.write("Analyse du contexte macro...")
                            time.sleep(1)
                            st.write("Recherche des failles critiques...")
                            time.sleep(1)
                            st.write("Vérification des biais...")
                            try:
                                res = model.generate_content(f"Analyse critique business (Avocat du Diable): {new_txt}").text
                                st.session_state.project["analysis"] = res
                                status.update(label="✅ Analyse terminée !", state="complete", expanded=False)
                                
                                st.session_state.project["pivots"] = ""
                                st.session_state.project["gps"] = ""
                                consume_credit()
                                st.rerun() 
                            except Exception as e:
                                status.update(label="❌ Erreur", state="error")
                                st.error(f"Erreur IA: {e}")
                    else: st.error("Pas de crédit")

    else:
        if credits > 0:
            idea_input = st.text_area("Votre idée :", height=150)
            if st.button("Lancer (1 crédit)", type="primary"):
                if idea_input:
                    st.session_state.project["idea"] = idea_input
                    with st.status("🧠 Activation Stratège IA...", expanded=True) as status:
                        st.write("Lecture de l'idée...")
                        time.sleep(0.5)
                        st.write("Scan des concurrents & Risques...")
                        time.sleep(1)
                        st.write("⚖️ Pesée des arguments...")
                        try:
                            res = model.generate_content(f"Analyse critique business (Avocat du Diable): {idea_input}").text
                            st.session_state.project["analysis"] = res
                            status.update(label="✅ Rapport généré !", state="complete", expanded=False)
                            
                            consume_credit()
                            st.rerun()
                        except Exception as e:
                             status.update(label="❌ Erreur", state="error")
                             st.error(f"Erreur IA: {e}")
        else: st.warning("Rechargez vos crédits")

# PAGE 2 : PIVOTS
elif st.session_state.current_page == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    
    if st.session_state.project["idea"]:
        st.info(f"📌 Projet : {st.session_state.project['idea']}")
    
    if not st.session_state.project["pivots"]:
        if credits > 0: 
            with st.status("💡 Recherche de Pivots en cours...", expanded=True) as status:
                st.write("🔄 Analyse des Business Models alternatifs...")
                time.sleep(1.5)
                st.write("🚀 Brainstorming des stratégies de scalabilité...")
                time.sleep(1.5)
                st.write("✍️ Formalisation des 3 options...")
                
                try:
                    res = model.generate_content(f"3 Pivots business créatifs pour: {st.session_state.project['idea']}").text
                    st.session_state.project["pivots"] = res
                    consume_credit()
                    status.update(label="✅ 3 Stratégies trouvées !", state="complete", expanded=False)
                    st.rerun()
                except Exception as e:
                    status.update(label="❌ Erreur", state="error")
                    st.error(f"Erreur IA: {e}")
                    st.stop()
        else:
            st.warning("⚠️ Crédits épuisés. Rechargez pour découvrir les Pivots Stratégiques.")
            st.link_button("💳 Recharger", LINK_RECHARGE, type="primary")
            st.stop()
        
    st.markdown(st.session_state.project["pivots"])
    st.divider()
    opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    cur = st.session_state.project.get("choice")
    idx = opts.index(cur) if cur in opts else 0
    choice = st.radio("Choix :", opts, index=idx)
    if st.button("Valider et Voir le GPS ➡️", type="primary"):
        st.session_state.project["choice"] = choice
        st.session_state.project["gps"] = ""
        st.session_state.current_page = 3
        st.rerun()

# PAGE 3 : GPS
elif st.session_state.current_page == 3:
    st.subheader("3️⃣ GPS")
    tgt = f"{st.session_state.project['idea']} ({st.session_state.project['choice']})"
    st.info(f"Objectif : {tgt}")
    
    if not st.session_state.project["gps"]:
        if credits > 0:
            with st.status("🗺️ Calcul itinéraire...", expanded=True) as status:
                st.write("📅 Définition des objectifs à 90 jours...")
                time.sleep(1)
                st.write("⚡ Identification des actions immédiates...")
                try:
                    res = model.generate_content(f"Plan d'action opérationnel (GPS) pour: {tgt}").text
                    st.session_state.project["gps"] = res
                    consume_credit()
                    status.update(label="✅ Itinéraire prêt !", state="complete", expanded=False)
                    st.rerun()
                except Exception as e:
                    status.update(label="❌ Erreur", state="error")
                    st.error(f"Erreur IA: {e}")
        else:
            st.warning("⚠️ Crédits épuisés. Rechargez pour obtenir votre Plan d'Action Détaillé (GPS).")
            st.link_button("💳 Recharger", LINK_RECHARGE, type="primary")
            st.stop()
        
    st.markdown(st.session_state.project["gps"])
    st.divider()
    st.success("Terminé.")
    st.link_button("💎 Réserver Audit (Pré-rempli)", generate_form_link(), type="primary")
