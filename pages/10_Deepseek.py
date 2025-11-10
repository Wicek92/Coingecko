import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Titre de l'application
st.title("Mon Application Streamlit")

# Texte
st.write("Bienvenue dans mon application Streamlit !")

# Entrée utilisateur
user_input = st.text_input("Entrez votre nom :")
if user_input:
    st.write(f"Bonjour, {user_input} !")

# Slider pour sélectionner une valeur
number = st.slider("Choisissez un nombre", 0, 100)
st.write(f"Vous avez choisi : {number}")

# Création d'un DataFrame
data = pd.DataFrame({
    'x': np.arange(1, 101),
    'y': np.random.randn(100).cumsum()
})

# Affichage du DataFrame
st.write("Voici un DataFrame aléatoire :")
st.dataframe(data)

# Graphique
st.write("Graphique linéaire :")
st.line_chart(data.set_index('x'))

# Bouton
if st.button("Cliquez-moi"):
    st.write("Vous avez cliqué sur le bouton !")

# Sélecteur de fichier
uploaded_file = st.file_uploader("Téléversez un fichier CSV", type="csv")
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write("Contenu du fichier :")
    st.write(data)

# Sidebar
st.sidebar.header("Paramètres")
option = st.sidebar.selectbox("Choisissez une option", ["Option 1", "Option 2", "Option 3"])
st.sidebar.write(f"Vous avez choisi : {option}")