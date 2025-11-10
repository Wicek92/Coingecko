import streamlit as st

st.title("📈 Tableau de bord")
st.write("Ici, tu peux afficher des graphiques ou des indicateurs.")


import streamlit as st
import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta

# --- CONFIG PAGE ---
st.set_page_config(page_title="📊 Crypto Tracker avec RSI", layout="wide")

st.title("📈 Suivi des Cryptomonnaies avec RSI (API CoinGecko)")
st.write("Données en temps réel + RSI (Relative Strength Index).")

# --- RÉCUPÉRATION DES DONNÉES COINGECKO ---
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
        st.error("Erreur lors de la récupération du marché.")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_historical_prices(coin_id="bitcoin", vs_currency="usd", days=14):
    """Récupère les prix journaliers d'une crypto pour calculer le RSI"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"
    res = requests.get(url)
    if res.status_code == 200:
        prices = pd.DataFrame(res.json()["prices"], columns=["timestamp", "price"])
        prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
        return prices
    else:
        return pd.DataFrame()

# --- CALCUL DU RSI ---
def compute_rsi(prices, period=14):
    delta = prices["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    prices["RSI"] = 100 - (100 / (1 + rs))
    return prices

# --- UI ---
col1, col2 = st.columns(2)
with col1:
    currency = st.selectbox("💵 Devise :", ["usd", "eur"])
with col2:
    limit = st.slider("📊 Nombre de cryptos :", 5, 30, 10)

market_data = get_market_data(currency, limit)

if not market_data.empty:
    st.subheader("🏦 Données du marché")
    st.dataframe(market_data[["name", "symbol", "current_price", "market_cap", "price_change_percentage_24h"]])

    selected_coin = st.selectbox("📈 Sélectionne une crypto pour voir son RSI :", market_data["id"].tolist())

    prices = get_historical_prices(selected_coin, currency, 30)
    if not prices.empty:
        prices = compute_rsi(prices)
        st.line_chart(prices.set_index("timestamp")[["price"]], height=200)
        st.line_chart(prices.set_index("timestamp")[["RSI"]], height=200)

        current_rsi = prices["RSI"].iloc[-1]
        st.metric(label=f"RSI actuel ({selected_coin})", value=f"{current_rsi:.2f}")

        if current_rsi > 70:
            st.warning("⚠️ RSI > 70 → Surachat potentiel")
        elif current_rsi < 30:
            st.info("💡 RSI < 30 → Survente potentielle")
        else:
            st.success("✅ RSI neutre (zone équilibrée)")
else:
    st.warning("Aucune donnée disponible.")

