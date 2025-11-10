import streamlit as st

st.title("⚙️ Paramètres")
st.write("Page de configuration ou de préférences.")


import streamlit as st
import pandas as pd
import requests
import numpy as np
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="📊 CoinGecko + RSI", layout="wide")
st.title("📈 Suivi des Cryptos avec RSI (API CoinGecko)")
st.write("Ce tableau affiche les prix en temps réel et le RSI calculé sur 14 jours.")

# --- 1️⃣ FONCTIONS UTILITAIRES ---
@st.cache_data(ttl=300)
def get_market_data(vs_currency="usd", per_page=10):
    url = (
        f"https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency={vs_currency}&order=market_cap_desc&per_page={per_page}&page=1&sparkline=false"
    )
    res = requests.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error("Erreur lors de la récupération des données.")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_historical_prices(coin_id, vs_currency="usd", days=14):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
    res = requests.get(url)
    if res.status_code == 200:
        prices = pd.DataFrame(res.json()["prices"], columns=["timestamp", "price"])
        prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
        return prices
    else:
        return pd.DataFrame()

def compute_rsi(prices, period=14):
    """Calcule le RSI à partir d’une série de prix"""
    if prices.empty or len(prices) < period:
        return np.nan
    delta = prices["price"].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]  # Dernière valeur

# --- 2️⃣ INTERFACE UTILISATEUR ---
col1, col2 = st.columns(2)
with col1:
    currency = st.selectbox("💵 Devise :", ["usd", "eur"])
with col2:
    limit = st.slider("📊 Nombre de cryptos :", 5, 30, 10)

# --- 3️⃣ RÉCUPÉRATION DES DONNÉES ---
market_data = get_market_data(currency, limit)

# --- 4️⃣ AJOUT DU RSI POUR CHAQUE CRYPTO ---
rsi_values = []
if not market_data.empty:
    progress = st.progress(0)
    for i, coin in enumerate(market_data["id"]):
        prices = get_historical_prices(coin, currency, 14)
        rsi = compute_rsi(prices)
        rsi_values.append(rsi)
        progress.progress((i + 1) / len(market_data))
    progress.empty()
    market_data["RSI"] = rsi_values

    # --- 5️⃣ TABLEAU FINAL ---
    display_data = market_data[
        ["name", "symbol", "current_price", "market_cap", "price_change_percentage_24h", "RSI"]
    ].rename(
        columns={
            "name": "Nom",
            "symbol": "Symbole",
            "current_price": f"Prix ({currency.upper()})",
            "market_cap": "Capitalisation",
            "price_change_percentage_24h": "% 24h",
        }
    )

    # Coloration conditionnelle du RSI
    def color_rsi(val):
        if pd.isna(val):
            return ""
        if val > 70:
            return "background-color: rgba(255, 100, 100, 0.3)"  # rouge clair
        elif val < 30:
            return "background-color: rgba(100, 255, 100, 0.3)"  # vert clair
        else:
            return ""

    st.subheader("📊 Tableau du marché avec RSI (14 jours)")
    st.dataframe(display_data.style.applymap(color_rsi, subset=["RSI"]), use_container_width=True)

    st.caption("⚠️ RSI > 70 = surachat | RSI < 30 = survente | Calcul basé sur les 14 derniers jours.")
else:
    st.warning("Aucune donnée disponible.")

