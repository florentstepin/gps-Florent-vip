import streamlit as st

st.set_page_config(page_title="Stratège IA - Déménagement", page_icon="🧠")

st.markdown("""
    <style>
    .redirect-box {
        padding: 30px;
        border-radius: 15px;
        background-color: #f0f2f6;
        border: 2px solid #7f5af0;
        text-align: center;
    }
    .btn-pro {
        background-color: #7f5af0 !important;
        color: white !important;
        padding: 15px 25px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.2rem;
    }
    </style>
    <div class="redirect-box">
        <h1>🚀 Stratège IA passe en version PRO !</h1>
        <p>Nous avons déménagé pour vous offrir plus de puissance, de stabilité et de nouvelles fonctionnalités.</p>
        <br>
        <a href="https://stratege-ia-beta.streamlit.app/" class="btn-pro">Accéder à la V2.5 Pro (Cliquez ici)</a>
        <br><br>
        <p><i>Vos crédits ont été conservés et mis à jour sur la nouvelle plateforme.</i></p>
    </div>
""", unsafe_allow_html=True)
