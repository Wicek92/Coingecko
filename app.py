import streamlit as st

st.title("🚀 Ma première application Streamlit")
st.write("Bravo ! Python et Streamlit fonctionnent sur ta machine 🎉")

name = st.text_input("Quel est ton prénom ?")
if name:
    st.success(f"Enchanté, {name} 😄")



import streamlit as st
import pandas as pd
 
# Créez un dataframe d'exemple
data = pd.DataFrame({
  'Fruits': ['Pommes', 'Oranges', 'Bananes', 'Raisins'],
  'Quantité': [15, 25, 35, 45]
})
 
# Créez un graphique à barres
st.bar_chart(data)