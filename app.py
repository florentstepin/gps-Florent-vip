import streamlit as st
from supabase import create_client
import google.generativeai as genai
import json
import time
import os
import urllib.parse
import uuid

# --- CONFIGURATION ---
st.set_page_config(page_title="Stratège IA", page_icon="🧠", layout="wide")

try:
    # VOS CODES SECRETS
    API_GOOGLE = st.secrets["GOOGLE_API_KEY"]
    URL_SUPA = st.secrets["SUPABASE_URL"]
    KEY_SUPA = st.secrets["SUPABASE_KEY"]
    LINK_RECHARGE = st.secrets["LIEN_RECHARGE"] 
    
    # CONFIGURATION FORMULAIRE
    BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScKU17kIr4t_Wiwi6uTMd0a2CCUMtqOU0w_yEHb8uAXVfgCZw/viewform"
    ENTRY_EMAIL = "entry.121343077"
    ENTRY_IDEE  = "entry.1974870243"
    ENTRY_AUDIT = "entry.1147735867"

    supabase = create_client(URL_SUPA, KEY_SUPA)
    genai.configure(api_key=API_GOOGLE)
    model = genai.GenerativeModel('gemini-1.5-flash')

except Exception as e:
    st.error(f"Erreur Config: {e}")
    st.stop()

# --- ETAT ---
if "user" not in st.session_state: st.session_state.user = None
if "step" not in st.session_state: st.session_state.step = 1
if "view" not in st.session_state: st.session_state.view = "1. Analyse"
if "widget_key" not in st.session_state: st.session_state.widget_key = str(uuid.uuid4())
if "data" not in st.session_state: 
    st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}

# --- FONCTIONS ---
def force_refresh():
    if st.session_state.user:
        try:
            res = supabase.table("users").select("*").eq("email", st.session_state.user['email']).execute()
            if res.data: st.session_state.user = res.data[0]
        except: pass

def login(email):
    email = str(email).strip().lower()
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data: return res.data[0]
        new = {"email": email, "credits": 3, "access_code": "NOUVEAU"}
        res = supabase.table("users").insert(new).execute()
        if res.data: return res.data[0]
    except:
        try:
            res = supabase.table("users").select("*").eq("email", email).execute()
            if res.data: return res.data[0]
        except: pass
    return None

def debit():
    if not st.session_state.user: return
    email = st.session_state.user['email']
    new_val = max(0, st.session_state.user.get('credits', 0) - 1)
    try: supabase.table("users").update({"credits": new_val}).eq("email", email).execute()
    except: pass
    st.session_state.user['credits'] = new_val
    force_refresh()

def get_link():
    if not st.session_state.user: return BASE_FORM_URL
    audit = st.session_state.data.get("analysis", "")[:1800]
    if len(st.session_state.data.get("analysis", "")) > 1800: audit += "..."
    params = {
        ENTRY_EMAIL: st.session_state.user['email'],
        ENTRY_IDEE: st.session_state.data.get("idea", ""),
        ENTRY_AUDIT: audit
    }
    return f"{BASE_FORM_URL}?{urllib.parse.urlencode(params)}"

def reset():
    st.session_state.data = {"idea": "", "analysis": "", "pivots": "", "gps": "", "choice": None}
    st.session_state.step = 1
    st.session_state.view = "1. Analyse"
    st.session_state.widget_key = str(uuid.uuid4())
    st.rerun()

def load_json(f):
    try:
        d = json.load(f)
        st.session_state.step = d.get("step", 1)
        st.session_state.data = d.get("data", {})
        st.session_state.view = "1. Analyse"
        st.session_state.widget_key = str(uuid.uuid4())
        st.success("Chargé !")
        time.sleep(0.5)
        st.rerun()
    except: st.error("Erreur fichier")

# --- APP ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        st.title("🚀 Stratège IA")
        em = st.text_input("Email", placeholder="email@pro.com")
        if st.button("Connexion", use_container_width=True):
            if "@" in em:
                u = login(em)
                if u:
                    st.session_state.user = u
                    force_refresh()
                    st.rerun()
            else: st.warning("Email invalide")
    st.stop()

# DASHBOARD
user = st.session_state.user
creds = user.get("credits", 0)

with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    st.caption(f"👤 {user['email']}")
    if creds > 0: st.metric("Crédits", creds)
    else: 
        st.error("Épuisé")
        st.link_button("Recharger", LINK_RECHARGE, type="primary")
    st.divider()
    st.info("💎 **Expert Humain**")
    st.link_button("Réserver Audit", get_link(), type="primary", use_container_width=True)
    st.divider()
    opts = ["1. Analyse"]
    if st.session_state.step >= 2: opts.append("2. Pivots")
    if st.session_state.step >= 3: opts.append("3. GPS")
    try: idx = opts.index(st.session_state.view)
    except: idx = 0
    nav = st.radio("Menu", opts, index=idx)
    if nav != st.session_state.view:
        st.session_state.view = nav
        st.rerun()
    st.divider()
    if st.button("✨ Nouvelle Analyse", use_container_width=True): reset()
    st.download_button("💾 Sauver", json.dumps(st.session_state.data), "projet.json")
    up = st.file_uploader("📂 Charger", type="json")
    if up: load_json(up)
    if st.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

# PAGES
st.title("🧠 Stratège IA")
curr = int(st.session_state.view.split(".")[0])
st.progress(curr/3)

if curr == 1:
    st.subheader("1️⃣ Analyse")
    if st.session_state.data.get("analysis"):
        st.info(f"Sujet : {st.session_state.data.get('idea')}")
        st.markdown(st.session_state.data["analysis"])
        if st.button("Suite ➡️", type="primary"):
            st.session_state.step = max(st.session_state.step, 2)
            st.session_state.view = "2. Pivots"
            st.rerun()
        with st.expander("Correction (1 crédit)"):
            nk = f"edit_{st.session_state.widget_key}"
            nt = st.text_area("Edit", value=st.session_state.data.get("idea", ""), key=nk)
            if st.button("Relancer"):
                if creds > 0:
                    st.session_state.data["idea"] = nt
                    with st.spinner("Analyse..."):
                        res = model.generate_content(f"Analyse critique: {nt}").text
                        st.session_state.data["analysis"] = res
                        st.session_state.data["pivots"] = ""
                        st.session_state.data["gps"] = ""
                        debit()
                        st.rerun()
                else: st.error("Crédit insuffisant")
    else:
        if creds > 0:
            nk = f"new_{st.session_state.widget_key}"
            ut = st.text_area("Votre idée :", height=150, key=nk)
            if st.button("Analyser (1 crédit)", type="primary"):
                if ut:
                    st.session_state.data["idea"] = ut
                    with st.spinner("Analyse..."):
                        res = model.generate_content(f"Analyse critique: {ut}").text
                        st.session_state.data["analysis"] = res
                        st.session_state.step = 2
                        debit()
                        st.rerun()
        else: st.warning("Rechargez vos crédits")

elif curr == 2:
    st.subheader("2️⃣ Pivots")
    if not st.session_state.data.get("pivots"):
        with st.spinner("Recherche..."):
            res = model.generate_content(f"3 Pivots pour: {st.session_state.data['idea']}").text
            st.session_state.data["pivots"] = res
            st.rerun()
    st.markdown(st.session_state.data["pivots"])
    st.divider()
    ops = ["Initial", "Pivot 1", "Pivot 2", "Pivot 3"]
    try: i = ops.index(st.session_state.data.get("choice"))
    except: i = 0
    c = st.radio("Choix :", ops, index=i)
    if st.button("Valider"):
        st.session_state.data["choice"] = c
        st.session_state.data["gps"] = ""
        st.session_state.step = 3
        st.session_state.view = "3. GPS"
        st.rerun()

elif curr == 3:
    st.subheader("3️⃣ GPS")
    tgt = f"{st.session_state.data['idea']} ({st.session_state.data['choice']})"
    if not st.session_state.data.get("gps"):
        with st.spinner("Calcul..."):
            res = model.generate_content(f"Plan d'action: {tgt}").text
            st.session_state.data["gps"] = res
            st.rerun()
    st.markdown(st.session_state.data["gps"])
    st.divider()
    st.success("Terminé")
    st.link_button("💎 Réserver Audit", get_link(), type="primary")
