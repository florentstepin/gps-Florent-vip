import streamlit as st

st.set_page_config(page_title="Diagnostic Secrets", page_icon="🕵️‍♂️")

st.title("🕵️‍♂️ Inspecteur de Secrets")

st.write("J'analyse le contenu de votre fichier Secrets...")

# Liste des clés obligatoires pour l'application
required_keys = ["GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "LIEN_RECHARGE"]
missing_keys = []

# 1. Vérification brute
try:
    # On affiche toutes les clés trouvées (sans afficher les mots de passe pour sécurité)
    found_keys = list(st.secrets.keys())
    
    if not found_keys:
        st.error("❌ RÉSULTAT : Le coffre-fort est VIDE ou illisible.")
    else:
        st.write("---")
        st.subheader("Ce que je trouve dans le coffre :")
        for key in found_keys:
            # On vérifie si la valeur est vide ou non
            value_preview = str(st.secrets[key])[:5] + "..." if st.secrets[key] else "VIDE"
            st.info(f"🔑 Clé : **'{key}'** (Valeur détectée : {value_preview})")
            
        st.write("---")
        
        # 2. Vérification des manquants
        for req in required_keys:
            if req not in found_keys:
                missing_keys.append(req)
        
        if missing_keys:
            st.error(f"❌ IL MANQUE CES CLÉS PRÉCISES : {missing_keys}")
            st.warning("Vérifiez l'orthographe exacte dans vos Secrets (majuscules, espaces).")
        else:
            st.success("✅ TOUT EST PARFAIT ! Toutes les clés sont présentes.")
            st.balloons()
            st.markdown("👉 **Vous pouvez maintenant remettre le code complet de l'application.**")

except Exception as e:
    st.error(f"Erreur critique de lecture : {e}")
    st.write("Le format TOML est probablement encore invalide (guillemets manquants ?).")
