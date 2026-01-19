import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid # <--- AJOUT CRITIQUE POUR GÉNÉRER DES CODES UNIQUES

# --- CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🧠", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] 
    
    # --- VOS CODES GOOGLE FORM (INTEGRÉS) ---
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    
    # MOTEUR : On reste sur l'alias stable pour éviter les erreurs 404
    model = genai.GenerativeModel('gemini-pro')

except Exception as e:
    st.error(f"❌ Erreur Config : {e}")
    st.stop()

# --- GESTION ÉTAT (SESSION) ---
if "user" not in st.session_state: st.session_state.user = None
if "current_page" not in st.session_state: st.session_state.current_page = 1
if "project_data" not in st.session_state: 
    st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- FONCTIONS ---

def verifier_et_connecter(email_saisi):
    """
    CORRECTION MAJEURE : Utilisation d'un UUID pour l'access_code.
    Cela empêche l'erreur 'Duplicate Key' dans Supabase.
    """
    email_propre = str(email_saisi).strip().lower()
    try:
        # 1. On cherche si l'email existe déjà
        recherche = supabase.table("users").select("*").eq("email", email_propre).execute()
        
        if recherche.data:
            return recherche.data[0]
        else:
            # 2. CRÉATION DU COMPTE
            # Au lieu de mettre "WAITING_MAKE" (qui bloque au 2eme user),
            # on génère un code unique que Make pourra utiliser.
            unique_code = str(uuid.uuid4())
            
            nouveau_compte = {
                "email": email_propre,
                "credits": 3,
                "access_code": unique_code # <--- ICI C'EST UNIQUE MAINTENANT
            }
            creation = supabase.table("users").insert(nouveau_compte).execute()
            if creation.data: return creation.data[0]
            
    except Exception as e:
        # Si malgré tout ça plante, on essaie de récupérer l'user (race condition)
        try:
             recherche = supabase.table("users").select("*").eq("email", email_propre).execute()
             if recherche.data: return recherche.data[0]
        except:
            st.error(f"Erreur technique : {e}")
    return None

def debiter_1_credit(utilisateur):
    email_cible = utilisateur["email"]
    # Lecture optimiste
    credits_actuels = st.session_state.user.get("credits", 0)
    nouveau_solde = max(0, credits_actuels - 1)
    
    # Update Session
    st.session_state.user["credits"] = nouveau_solde
    
    # Update DB
    try:
        supabase.table("users").update({"credits": nouveau_solde}).eq("email", email_cible).execute()
    except: pass

def generate_form_link():
    """Génère le lien Google Form pré-rempli"""
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.project_data.get("idea", "")
    audit = st.session_state.project_data.get("analysis", "")[:1500]
    if len(st.session_state.project_data.get("analysis", "")) > 1500: audit += "..."
    
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: audit}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    st.session_state.project_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.current_page = 1
    st.rerun()

def save_json():
    return json.dumps({"step": st.session_state.current_page, "data": st.session_state.project_data}, indent=4)

def load_json(f):
    try:
        d = json.load(f)
        # On ne charge que les données pour éviter les bugs de navigation
        clean_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean_data.update(d.get("data", {}))
        st.session_state.project_data = clean_data
        st.session_state.current_page = 1 # On remet au début pour voir les données
        st.success("Dossier chargé !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Fichier invalide")

# --- LOGIN ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=150)
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

# --- APP ---
user = st.session_state.user
credits = user.get("credits", 0)

# SIDEBAR
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.write(f"👤 **{user.get('email')}**")

    if credits > 0:
        st.metric("Crédits Dispo", credits)
    else:
        st.error("Crédits Épuisés")
        st.link_button("💳 Recharger", LINK_RECHARGE, type="primary")
    
    st.divider()
    st.info("💎 **Expert Humain**")
    st.link_button("Réserver Audit (Pré-rempli)", generate_form_link(), type="primary", use_container_width=True)

    st.divider()
    st.markdown("### 🧭 Navigation")
    
    # Navigation par boutons (Plus stable que le radio button pour éviter les boucles)
    if st.button("1. Analyse"): 
        st.session_state.current_page = 1
        st.rerun()
    if st.session_state.project_data["analysis"] and st.button("2. Pivots"): 
        st.session_state.current_page = 2
        st.rerun()
    if st.session_state.project_data["pivots"] and st.button("3. GPS"): 
        st.session_state.current_page = 3
        st.rerun()
        
    st.divider()
    if st.button("✨ Nouvelle Analyse", use_container_width=True):
        reset_project()

    st.download_button("💾 Sauvegarder", save_json(), "projet.json", use_container_width=True)
    up = st.file_uploader("📂 Charger", type="json")
    if up: load_json(up)
    
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# CONTENU PRINCIPAL
st.title("🧠 Stratège IA")
st.progress(st.session_state.current_page / 3)

# PHASE 1
if st.session_state.current_page == 1:
    st.subheader("1️⃣ Analyse Crash-Test")
    
    if st.session_state.project_data["analysis"]:
        st.info(f"Sujet : {st.session_state.project_data['idea']}")
        st.markdown(st.session_state.project_data["analysis"])
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Passer aux Pivots ➡️", type="primary"):
                st.session_state.current_page = 2
                st.rerun()
        with c2:
            with st.expander("Modifier et Relancer (1 crédit)"):
                n = st.text_area("Correction :", value=st.session_state.project_data["idea"])
                if st.button("Relancer l'analyse"):
                    if credits > 0:
                        st.session_state.project_data["idea"] = n
                        with st.spinner("Analyse V2..."):
                            try:
                                st.session_state.project_data["analysis"] = model.generate_content(f"Analyse critique: {n}").text
                                st.session_state.project_data["pivots"] = ""
                                st.session_state.project_data["gps"] = ""
                                debiter_1_credit(user)
                                st.rerun()
                            except Exception as e: st.error(f"Erreur IA: {e}")
                    else: st.error("Solde nul")
    else:
        if credits > 0:
            t = st.text_area("Décrivez votre idée de business :", height=150)
            if st.button("Lancer l'Analyse (1 crédit)", type="primary"):
                if t:
                    st.session_state.project_data["idea"] = t
                    with st.spinner("Analyse en cours..."):
                        try:
                            # Prompt initial
                            st.session_state.project_data["analysis"] = model.generate_content(f"Analyse critique business: {t}").text
                            st.session_state.current_page = 2
                            debiter_1_credit(user)
                            st.rerun()
                        except Exception as e: st.error(f"Erreur IA: {e}")
        else: st.warning("Veuillez recharger vos crédits.")

# PHASE 2
elif st.session_state.current_page == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    
    if not st.session_state.project_data["pivots"]:
        with st.spinner("Recherche de pivots..."):
            try:
                res = model.generate_content(f"3 Pivots business pour: {st.session_state.project_data['idea']}").text
                st.session_state.project_data["pivots"] = res
                st.rerun()
            except Exception as e:
                st.error(f"Erreur IA: {e}")
                st.stop()

    st.markdown(st.session_state.project_data["pivots"])
    st.divider()
    
    ops = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    # Récupération sécurisée du choix
    cur_choice = st.session_state.project_data.get("choice")
    idx = 0
    if cur_choice in ops: idx = ops.index(cur_choice)
    
    c = st.radio("Sur quelle stratégie part-on ?", ops, index=idx)
    
    if st.button("Valider ce choix et Générer le GPS", type="primary"):
        st.session_state.project_data["choice"] = c
        st.session_state.project_data["gps"] = ""
        st.session_state.current_page = 3
        st.rerun()

# PHASE 3
elif st.session_state.current_page == 3:
    st.subheader("3️⃣ GPS : Plan d'Action")
    
    f_sub = f"{st.session_state.project_data['idea']} ({st.session_state.project_data['choice']})"
    st.info(f"🎯 **Cible validée :** {f_sub}")
    
    if not st.session_state.project_data["gps"]:
        with st.spinner("Calcul de l'itinéraire..."):
            try:
                res = model.generate_content(f"Plan d'action COO pour: {f_sub}").text
                st.session_state.project_data["gps"] = res
                st.rerun()
            except Exception as e: st.error(f"Erreur IA: {e}")

    if st.session_state.project_data["gps"]:
        st.markdown(st.session_state.project_data["gps"])
        st.divider()
        st.success("Plan Terminé.")
        st.link_button("💎 Réserver Audit (Pré-rempli)", generate_form_link(), type="primary")
