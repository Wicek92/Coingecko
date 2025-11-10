import streamlit as st

st.title("📊 Analyse des données")
st.write("Voici la page d'analyse.")



import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="📊 Crypto Tracker - CoinGecko", layout="wide")

st.title("📈 Suivi des Cryptomonnaies (API CoinGecko)")
st.write("Données en temps réel depuis [CoinGecko](https://www.coingecko.com).")

# --- CHARGEMENT DES DONNÉES DEPUIS COINGECKO ---
@st.cache_data(ttl=300)
def get_crypto_data(vs_currency="usd", per_page=20):
    """Récupère les prix des cryptos via l'API CoinGecko"""
    url = (
        f"https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency={vs_currency}&order=market_cap_desc&per_page={per_page}&page=1&sparkline=false"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Erreur lors de la récupération des données.")
        return pd.DataFrame()

# --- INTERFACE UTILISATEUR ---
col1, col2 = st.columns(2)
with col1:
    currency = st.selectbox("💵 Devise :", ["usd", "eur", "btc"])
with col2:
    limit = st.slider("📊 Nombre de cryptos affichées :", 5, 50, 20)

# --- AFFICHAGE DES DONNÉES ---
data = get_crypto_data(vs_currency=currency, per_page=limit)

if not data.empty:
    data_display = data[["name", "symbol", "current_price", "market_cap", "price_change_percentage_24h"]]
    data_display = data_display.rename(
        columns={
            "name": "Nom",
            "symbol": "Symbole",
            "current_price": f"Prix ({currency.upper()})",
            "market_cap": "Capitalisation",
            "price_change_percentage_24h": "% Variation 24h",
        }
    )
    st.dataframe(data_display, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Top 10 par capitalisation")
    st.bar_chart(data_display.head(10).set_index("Nom")["Capitalisation"])

    st.caption(f"⏱️ Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}")

else:
    st.warning("Aucune donnée à afficher.")
