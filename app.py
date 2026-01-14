import streamlit as st
import google.generativeai as genai
import urllib.parse
import uuid
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
FORM_URL = "https://docs.google.com/forms/d/e/VOTRE_ID_DE_FORMULAIRE/viewform"
ENTRY_ID_EMAIL = "121343077"
ENTRY_ID_IDEA =  "1974870243"
ENTRY_ID_AUDIT = "1147735867"
EMAIL_CONTACT = "photos.studio.ia@gmail.com"
MASTER_CODE = "BOSS-2026" 

st.set_page_config(page_title="L'Architecte", page_icon="🏗️", layout="centered")

# --- 2. CONNEXION SUPABASE (BDD EXTERNE & ROBUSTE) ---
# On initialise la connexion une seule fois pour gagner du temps
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

if not supabase:
    st.error("🚨 Erreur critique : Base de données non connectée. Vérifiez les secrets.")
    st.stop()

# --- FONCTIONS BDD ---

def get_user_credits(code):
    """Récupère les infos client depuis Supabase"""
    try:
        # On cherche dans la table 'users', la ligne où access_code = code
        response = supabase.table("users").select("*").eq("access_code", code).execute()
        
        # Si on trouve un résultat
        if response.data and len(response.data) > 0:
            user = response.data[0]
            return user['credits'], user['total_runs']
        return None
    except Exception as e:
        st.error(f"Erreur DB: {e}")
        return None

def decrement_credits(code):
    """Enlève 1 crédit et ajoute 1 run"""
    try:
        # On récupère d'abord les valeurs actuelles pour être sûr
        current_credits, current_runs = get_user_credits(code)
        
        # On met à jour
        supabase.table("users").update({
            "credits": current_credits - 1,
            "total_runs": current_runs + 1
        }).eq("access_code", code).execute()
    except Exception as e:
        st.error(f"Erreur update DB: {e}")

def create_new_user(credits=50):
    """Crée un nouveau code dans Supabase"""
    new_code = "KEY-" + str(uuid.uuid4())[:8].upper()
    try:
        data = {
            "access_code": new_code,
            "credits": credits,
            "total_runs": 0
        }
        supabase.table("users").insert(data).execute()
        return new_code
    except Exception as e:
        st.error(f"Erreur création user: {e}")
        return "Erreur"

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

PROMPT_AUDIT = "RÔLE : Avocat du Diable. LIVRABLE : 1. VERDICT (GO/NO-GO), 2. Risques Fatals, 3. Matrice DUR. PROJET : {user_idea}"
PROMPT_PIVOT = "RÔLE : Innovation. MISSION : 5 Pivots radicaux. PROJET : {user_idea}"
PROMPT_PLAN = "RÔLE : Chef de projet. OBJECTIF : Vente J+7. LIVRABLE : Plan d'action. STRATÉGIE : {selected_angle}"

# --- 5. LOGIQUE DE CONNEXION ---
def attempt_login(code_input):
    clean_code = str(code_input).strip().replace("'", "").replace('"', "")
    
    # CAS ADMIN
    if clean_code == MASTER_CODE:
        st.session_state.logged_in = True
        st.session_state.is_admin = True
        st.session_state.user_code = "ADMIN"
        st.session_state.credits_left = 999999
        return True, "Admin connecté"
    
    # CAS CLIENT
    result = get_user_credits(clean_code) # Appel Supabase
    if result:
        credits, runs = result
        if credits > 0:
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.session_state.user_code = clean_code
            st.session_state.credits_left = credits
            st.session_state.total_runs = runs
            return True, "Client connecté"
        else:
            return False, "🔒 Crédits épuisés."
    
    return False, "Code inconnu"

# --- 6. INTERFACE PRINCIPALE ---
def main():
    
    # A. TENTATIVE AUTO
    if not st.session_state.logged_in:
        try:
            url_code = None
            if "code" in st.query_params:
                url_code = st.query_params["code"]
            elif len(st.query_params) > 0:
                 val = list(st.query_params.values())[0]
                 url_code = val if isinstance(val, str) else val[0]
            
            if url_code:
                success, msg = attempt_login(url_code)
                if success:
                    st.toast(f"🔓 {msg}")
                    st.rerun()
        except:
            pass

    st.title("🏗️ L'Architecte")

    # B. LOGIN MANUEL
    if not st.session_state.logged_in:
        with st.form("login"):
            st.markdown("### Identification")
            code_input = st.text_input("Code d'Accès", placeholder="Entrez votre clé...")
            if st.form_submit_button("Entrer"):
                success, msg = attempt_login(code_input)
                if success:
                    st.rerun()
                else:
                    st.error(msg)
        st.stop()

    # C. APP CONNECTÉE
    with st.sidebar:
        if st.session_state.is_admin:
            st.header("👑 God Mode")
            st.success("Base de données : Supabase 🟢")
            st.divider()
            
            st.subheader("Générateur de Codes")
            if st.button("Créer Code Client (50 crédits)"):
                new_code = create_new_user(50)
                st.write("Code généré :")
                st.code(new_code, language=None)
                st.write("👇 **Lien client :**")
                # Remplacez [VOTRE-APP] par le vrai nom de votre sous-domaine
                st.code(f"https://[VOTRE-APP].streamlit.app/?code={new_code}", language=None)
                st.success("Sauvegardé dans le Cloud !")
                
        else:
            st.header("Mon Espace")
            st.info(f"Code : {st.session_state.user_code}")
            st.metric("Crédits restants", st.session_state.credits_left)
        
        st.divider()
        if st.button("Déconnexion"):
            st.session_state.clear()
            st.rerun()

    is_client = not st.session_state.is_admin
    is_last_free_trial = (is_client and st.session_state.total_runs == 2) 

    # ETAPE 1 : AUDIT
    if st.session_state.step == 1:
        st.subheader("Audit Stratégique")
        if is_client and st.session_state.total_runs < 3:
            st.info(f"🌱 Essai Gratuit : {st.session_state.total_runs + 1}/3")
        
        user_idea = st.text_area("Votre idée :", height=120)
        launch_btn = st.button("Lancer l'Audit")

        confirm = True
        if is_last_free_trial:
            st.warning("⚠️ DERNIER ESSAI GRATUIT")
            st.error("En validant, vous renoncez au remboursement.")
            confirm = st.checkbox("J'accepte.")

        if launch_btn:
            if not confirm:
                st.toast("Confirmez la case.")
            elif user_idea:
                if is_client:
                    decrement_credits(st.session_state.user_code)
                    st.session_state.credits_left -= 1
                    st.session_state.total_runs += 1
                
                with st.spinner("Analyse en cours..."):
                    audit, model = get_strategic_response(PROMPT_AUDIT.format(user_idea=user_idea))
                    st.session_state.audit = audit
                    st.session_state.model_used = model
                    st.session_state.idea = user_idea
                    st.session_state.summary = get_email_summary(audit)
                    st.session_state.step = 2
                    st.rerun()

    # ETAPE 2 : RÉSULTAT
    elif st.session_state.step == 2:
        st.caption(f"Cerveau : {st.session_state.model_used}")
        st.markdown(st.session_state.audit)
        
        verdict_negatif = "NO-GO" in st.session_state.audit or "PIVOT" in st.session_state.audit
        form_link = create_google_form_link(st.session_state.idea, st.session_state.summary)
        
        st.markdown("---")
        if verdict_negatif:
            st.error("🚨 **RISQUE ÉLEVÉ DÉTECTÉ**")
            st.link_button("📤 Envoyer le dossier pour arbitrage", form_link)
        else:
            st.success("✅ **POTENTIEL CONFIRMÉ**")
            st.link_button("🚀 Candidater pour l'accompagnement", form_link)
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Pivoter (IA)"):
                with st.spinner("Recherche de pivots..."):
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

    # ETAPE 3 & 4 (Le reste est identique...)
    elif st.session_state.step == 3:
        st.markdown(st.session_state.pivot)
        choix = st.text_input("Quelle option choisissez-vous ?")
        if st.button("Générer le Plan"):
            st.session_state.choix = choix
            st.session_state.step = 4
            st.rerun()

    elif st.session_state.step == 4:
        st.subheader("Plan Tactique")
        if not st.session_state.plan:
            with st.spinner("Rédaction du plan..."):
                res, _ = get_strategic_response(PROMPT_PLAN.format(selected_angle=st.session_state.choix))
                st.session_state.plan = res
                st.session_state.summary = get_email_summary(res)
        
        st.markdown(st.session_state.plan)
        st.download_button("Télécharger le Plan", st.session_state.plan, "Plan.md")
        
        plan_link = create_google_form_link(st.session_state.choix, st.session_state.summary)
        st.link_button("📤 Envoyer ce plan à l'équipe", plan_link)
        
        if st.button("Recommencer"):
            st.session_state.step = 1
            st.rerun()

if __name__ == "__main__":
    main()
