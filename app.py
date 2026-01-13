import streamlit as st
import google.generativeai as genai

st.title("🕵️ Détective API")

# 1. Connexion
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        st.success("✅ Clé trouvée.")
    else:
        st.error("Pas de clé dans les secrets.")
        st.stop()
except Exception as e:
    st.error(f"Erreur config : {e}")

# 2. Lister ce que Google nous autorise
st.write("### Modèles accessibles avec cette clé :")
try:
    liste_modeles = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            liste_modeles.append(m.name)
            st.code(m.name)
    
    # 3. Analyse du résultat
    st.divider()
    if "models/gemini-1.5-pro" in liste_modeles:
        st.success("🎉 VICTOIRE ! Le modèle PRO est disponible. Le problème venait d'une faute de frappe dans le code précédent.")
    elif "models/gemini-pro" in liste_modeles:
         st.warning("⚠️ Bizarre : Seul l'ancien 'gemini-pro' est là. Le compte n'est pas vu comme Premium.")
    else:
        st.error("❌ ÉCHEC : Aucun modèle Pro détecté. Votre clé est toujours sur le projet Gratuit/Limité.")

except Exception as e:
    st.error(f"Erreur lors du scan : {e}")
