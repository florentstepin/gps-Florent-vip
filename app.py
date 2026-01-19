import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid # <--- L'ingrédient secret pour l'unicité

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🎯", layout="wide")

try:
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"]
    
    # Vos codes Google Form (Intégrés)
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    
    # Modèle stable 
    model = genai.GenerativeModel('gemini-2.5-pro')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- 2. INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "current_page" not in st.session_state: st.session_state.current_page = 1
if "project" not in st.session_state:
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- 3. FONCTIONS ---

def login_user(email):
    """
    Gère la connexion.
    CORRECTION : Génère un UUID unique pour l'access_code à la création.
    """
    email = str(email).strip().lower()
    try:
        # 1. Recherche si existe déjà
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        
        # 2. Création avec CODE UNIQUE
        # On remplace "WAITING_MAKE" par un vrai code unique
        unique_code = str(uuid.uuid4())
        
        new = {
            "email": email, 
            "credits": 3, 
            "access_code": unique_code # <--- La clé du succès
        }
        res = supabase.table("users").insert(new).execute()
        if res.data: return res.data[0]
    except Exception as e:
        # Si erreur (ex: race condition), on tente de relire
        try:
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data: return res.data[0]
        except: 
            st.error(f"Erreur technique (Login): {e}")
    return None

def consume_credit():
    if st.session_state.user:
        email = st.session_state.user['email']
        new_val = max(0, st.session_state.user['credits'] - 1)
        try: supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
        except: pass
        st.session_state.user['credits'] = new_val

def generate_form_link():
    if not st.session_state.user: return BASE_FORM_URL
    email = st.session_state.user['email']
    idee = st.session_state.project.get("idea", "")
    audit = st.session_state.project.get("analysis", "")[:1500]
    if len(st.session_state.project.get("analysis", "")) > 1500: audit += "..."
    
    params = {ENTRY_EMAIL: email, ENTRY_IDEE: idee, ENTRY_AUDIT: audit}
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset_project():
    st.session_state.project = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.current_page = 1
    st.rerun()

def load_json(uploaded_file):
    try:
        data = json.load(uploaded_file)
        clean_data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
        clean_data.update(data.get("data", {}))
        st.session_state.project = clean_data
        st.session_state.current_page = 1
        st.success("Chargé !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Fichier invalide")

# --- 4. LOGIN ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🚀 Stratège IA")
        email_in = st.text_input("Email Professionnel")
        if st.button("Connexion", use_container_width=True):
            if "@" in email_in:
                u = login_user(email_in)
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
    st.link_button("Réserver Audit (Pré-rempli)", generate_form_link(), type="primary", use_container_width=True)
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
    json_str = json.dumps({"data": st.session_state.project}, indent=4)
    st.download_button("💾 Sauver JSON", json_str, "projet.json")
    up = st.file_uploader("📂 Charger JSON", type="json")
    if up: load_json(up)
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

st.title("🧠 Stratège IA")
st.progress(st.session_state.current_page / 3)

# PAGE 1
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
            with st.expander("Modifier (1 crédit)"):
                new_txt = st.text_area("Correction", value=st.session_state.project["idea"])
                if st.button("Relancer"):
                    if credits > 0:
                        st.session_state.project["idea"] = new_txt
                         # THINKING PHASE 1
                    with st.status("🕵️‍♂️ L'IA analyse votre projet...", expanded=True) as status:
                        st.write("Analyse du contexte macro-économique...")
                        time.sleep(1)
                        st.write("Recherche des failles de marché...")
                        time.sleep(1)
                        st.write("Vérification des biais cognitifs...")
                        st.session_state.project_data["analysis"] = model.generate_content(f"Analyse critique: {n}").text
                        status.update(label="✅ Analyse terminée !", state="complete", expanded=False)
                    # ----------------
                    st.session_state.project_data["pivots"] = ""
                    st.session_state.project_data["gps"] = ""
                    debiter_1_credit(user)
                    st.rerun()
                else: st.error("Solde nul")
    else:
        if credits > 0:
            idea_input = st.text_area("Votre idée :", height=150)
            if st.button("Lancer (1 crédit)", type="primary"):
                if idea_input:
                    st.session_state.project["idea"] = idea_input
                   # THINKING INITIAL
                    with st.status("🧠 Activation du Stratège IA...", expanded=True) as status:
                        st.write("Lecture de votre idée...")
                        time.sleep(0.5)
                        st.write("🔍 Scan des concurrents potentiels...")
                        time.sleep(1)
                        st.write("⚖️ Pesée des risques et opportunités...")
                        time.sleep(1)
                        st.write("📝 Rédaction du rapport...")
                        st.session_state.project_data["analysis"] = model.generate_content(f"Analyse critique: {t}").text
                        status.update(label="✅ Rapport généré !", state="complete", expanded=False)
                    # ----------------
                            st.session_state.project["analysis"] = res
                            consume_credit()
                            st.session_state.current_page = 2
                            st.rerun()
                        except Exception as e: st.error(f"Erreur IA: {e}")
        else: st.warning("Rechargez vos crédits")

# PAGE 2
elif st.session_state.current_page == 2:
    st.subheader("2️⃣ Pivots Stratégiques")
    if not st.session_state.project["pivots"]:
    # THINKING PHASE 2 (Renforcé)
        with st.status("💡 Recherche de Pivots en cours...", expanded=True) as status:
            st.write("🔄 Analyse des Business Models alternatifs...")
            time.sleep(1.5) # Temps de lecture
            st.write("🚀 Brainstorming des stratégies de scalabilité...")
            time.sleep(1.5)
            st.write("✍️ Formalisation des 3 options...")
            res = model.generate_content(f"3 Pivots pour: {st.session_state.project_data['idea']}").text
            st.session_state.project_data["pivots"] = res
            status.update(label="✅ 3 Stratégies trouvées !", state="complete", expanded=False)
        st.rerun()
        # ----------------
                st.session_state.project["pivots"] = res
                st.rerun()
            except Exception as e: 
                st.error(f"Erreur IA: {e}")
                st.stop()
    st.markdown(st.session_state.project["pivots"])
    st.divider()
    opts = ["Idée Initiale", "Pivot 1", "Pivot 2", "Pivot 3"]
    cur = st.session_state.project.get("choice")
    idx = opts.index(cur) if cur in opts else 0
    choice = st.radio("Choix :", opts, index=idx)
    if st.button("Valider ➡️", type="primary"):
        st.session_state.project["choice"] = choice
        st.session_state.project["gps"] = ""
        st.session_state.current_page = 3
        st.rerun()

# PAGE 3
elif st.session_state.current_page == 3:
    st.subheader("3️⃣ GPS")
    tgt = f"{st.session_state.project['idea']} ({st.session_state.project['choice']})"
    st.info(f"Objectif : {tgt}")
    if not st.session_state.project["gps"]:
     # THINKING PHASE 3
            with st.status("🗺️ Calcul de l'itinéraire...", expanded=True) as status:
                st.write("📅 Définition des objectifs à 90 jours...")
                time.sleep(1)
                st.write("🔨 Découpage en tâches hebdomadaires...")
                time.sleep(1)
                st.write("⚡ Identification des actions immédiates...")
                res = model.generate_content(f"Plan d'action COO: {f_sub}").text
                st.session_state.project_data["gps"] = res
                status.update(label="✅ Itinéraire prêt !", state="complete", expanded=False)
            st.rerun()
   
                res = model.generate_content(f"Plan d'action: {tgt}").text
                st.session_state.project["gps"] = res
                st.rerun()
            except Exception as e: st.error(f"Erreur IA: {e}")
    st.markdown(st.session_state.project["gps"])
    st.divider()
    st.success("Terminé.")
    st.link_button("💎 Réserver Audit (Pré-rempli)", generate_form_link(), type="primary")
