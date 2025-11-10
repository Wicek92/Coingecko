import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime as dt

# --------------------------------------------------
# 🎯 CONFIGURATION DE BASE
# --------------------------------------------------
st.set_page_config(page_title="Dashboard Crypto", layout="wide")

st.title("📊 Tableau de bord Crypto complet")
st.caption("Suivi en temps réel des cryptos principales avec indicateurs techniques")

COINS = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "solana": "Solana",
    "sui": "Sui"
}
CURRENCY = "usd"

# --------------------------------------------------
# ⚙️ FONCTIONS
# --------------------------------------------------
@st.cache_data(ttl=300)
def get_market_data():
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency={CURRENCY}&ids={','.join(COINS.keys())}&sparkline=false"
    )
    r = requests.get(url)
    data = pd.DataFrame(r.json())
    data = data[["id", "name", "symbol", "current_price", "price_change_percentage_24h",
                 "market_cap", "total_volume"]]
    return data

@st.cache_data(ttl=3600)
def get_historical_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={CURRENCY}&days={days}"
    r = requests.get(url)
    prices = pd.DataFrame(r.json()["prices"], columns=["timestamp", "price"])
    prices["date"] = pd.to_datetime(prices["timestamp"], unit="ms")
    return prices

# RSI
def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# EMA
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# MACD
def compute_macd(prices):
    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)
    macd = ema12 - ema26
    signal = ema(macd, 9)
    return macd, signal

# Bollinger Bands
def compute_bollinger(prices, window=20):
    sma = prices.rolling(window).mean()
    std = prices.rolling(window).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return sma, upper, lower, std

# --------------------------------------------------
# 📈 RÉCUPÉRATION DES DONNÉES
# --------------------------------------------------
data = get_market_data()

resultats = []
for coin in COINS.keys():
    prices = get_historical_prices(coin, days=30)
    prices["RSI"] = compute_rsi(prices["price"])
    macd, signal = compute_macd(prices["price"])
    sma, upper, lower, std = compute_bollinger(prices["price"])

    resultats.append({
        "Nom": COINS[coin],
        "Prix (USD)": data.loc[data["id"] == coin, "current_price"].values[0],
        "Var 24h (%)": data.loc[data["id"] == coin, "price_change_percentage_24h"].values[0],
        "Capitalisation": data.loc[data["id"] == coin, "market_cap"].values[0],
        "Volume": data.loc[data["id"] == coin, "total_volume"].values[0],
        "RSI (14j)": prices["RSI"].iloc[-1],
        "EMA 9": ema(prices["price"], 9).iloc[-1],
        "EMA 26": ema(prices["price"], 26).iloc[-1],
        "MACD": macd.iloc[-1],
        "Signal MACD": signal.iloc[-1],
        "Volatilité (σ)": std.iloc[-1],
        "Bande sup.": upper.iloc[-1],
        "Bande inf.": lower.iloc[-1],
    })

df = pd.DataFrame(resultats)

# --------------------------------------------------
# 💹 AFFICHAGE DU TABLEAU
# --------------------------------------------------
st.subheader("📊 Données techniques (USD)")
st.dataframe(
    df.style.format({
        "Prix (USD)": "{:,.2f}",
        "Var 24h (%)": "{:.2f}%",
        "Capitalisation": "{:,.0f}",
        "Volume": "{:,.0f}",
        "RSI (14j)": "{:.2f}",
        "EMA 9": "{:,.2f}",
        "EMA 26": "{:,.2f}",
        "MACD": "{:.2f}",
        "Signal MACD": "{:.2f}",
        "Volatilité (σ)": "{:.2f}",
        "Bande sup.": "{:,.2f}",
        "Bande inf.": "{:,.2f}",
    }),
    use_container_width=True,
)

# --------------------------------------------------
# 🧠 EXPLICATIONS
# --------------------------------------------------
st.markdown("## 🧩 Explications des indicateurs")

with st.expander("🔸 RSI (Relative Strength Index)"):
    st.markdown("""
    - Le **RSI** mesure la force du mouvement du prix.
    - **RSI > 70** → zone de surachat (possible correction).
    - **RSI < 30** → zone de survente (possible rebond).
    - C’est un indicateur de **momentum**.
    """)

with st.expander("🔸 EMA (Moyenne mobile exponentielle)"):
    st.markdown("""
    - La **EMA** lisse les variations du prix en donnant plus d’importance aux données récentes.
    - **EMA 9** = tendance court terme.
    - **EMA 26** = tendance moyen terme.
    - Si EMA9 > EMA26 → tendance haussière.
    """)

with st.expander("🔸 MACD (Moving Average Convergence Divergence)"):
    st.markdown("""
    - Compare deux EMA (12 et 26).
    - **MACD > Signal** → momentum haussier.
    - **MACD < Signal** → momentum baissier.
    - Utilisé pour détecter les changements de tendance.
    """)

with st.expander("🔸 Bandes de Bollinger"):
    st.markdown("""
    - Indiquent la **volatilité** du marché.
    - Bande supérieure = zone de surachat.
    - Bande inférieure = zone de survente.
    - Plus les bandes sont **larges**, plus la volatilité est forte.
    """)

with st.expander("🔸 Volatilité (écart-type)"):
    st.markdown("""
    - Mesure à quel point les prix varient autour de leur moyenne.
    - Une forte volatilité = mouvements rapides (opportunités, mais plus de risque).
    """)

st.caption("💡 Données issues de CoinGecko, mises à jour automatiquement toutes les 5 minutes.")