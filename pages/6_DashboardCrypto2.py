import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

# --------------------------------------------------
# 🎯 CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Dashboard Crypto Complet", layout="wide")
st.title("💹 Tableau de bord Crypto — Analyse Technique")
st.caption("Données CoinGecko • Indicateurs : RSI, EMA, MACD, Bandes de Bollinger")

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
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={CURRENCY}&ids={','.join(COINS.keys())}&sparkline=false"
    r = requests.get(url)
    data = pd.DataFrame(r.json())
    return data

@st.cache_data(ttl=3600)
def get_historical_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={CURRENCY}&days={days}"
    r = requests.get(url)
    prices = pd.DataFrame(r.json()["prices"], columns=["timestamp", "price"])
    prices["date"] = pd.to_datetime(prices["timestamp"], unit="ms")
    return prices

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(prices):
    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)
    macd = ema12 - ema26
    signal = ema(macd, 9)
    return macd, signal

def compute_bollinger(prices, window=20):
    sma = prices.rolling(window).mean()
    std = prices.rolling(window).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return sma, upper, lower

# --------------------------------------------------
# 📈 TABLEAU DE DONNÉES
# --------------------------------------------------
data = get_market_data()
st.subheader("📊 Données principales (en USD)")

table = data[["name", "symbol", "current_price", "price_change_percentage_24h", "market_cap", "total_volume"]]
table.columns = ["Nom", "Symbole", "Prix (USD)", "Variation 24h (%)", "Capitalisation", "Volume"]

def color_percent(val):
    color = "green" if val > 0 else "red"
    return f"color: {color}"

st.dataframe(
    table.style.format({
        "Prix (USD)": "{:,.2f}",
        "Variation 24h (%)": "{:+.2f}",
        "Capitalisation": "{:,.0f}",
        "Volume": "{:,.0f}"
    }).applymap(color_percent, subset=["Variation 24h (%)"]),
    use_container_width=True
)

# --------------------------------------------------
# 📊 GRAPHIQUES DÉTAILLÉS
# --------------------------------------------------
st.markdown("## 📉 Visualisation technique détaillée")

for coin_id, coin_name in COINS.items():
    st.markdown(f"### 🪙 {coin_name}")
    prices = get_historical_prices(coin_id, 30)

    # Calculs indicateurs
    prices["EMA9"] = ema(prices["price"], 9)
    prices["EMA26"] = ema(prices["price"], 26)
    prices["RSI"] = compute_rsi(prices["price"])
    prices["MACD"], prices["Signal"] = compute_macd(prices["price"])
    prices["SMA"], prices["Upper"], prices["Lower"] = compute_bollinger(prices["price"])

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prices["date"], y=prices["price"], mode="lines", name="Prix", line=dict(color="white")))
        fig.add_trace(go.Scatter(x=prices["date"], y=prices["EMA9"], mode="lines", name="EMA 9", line=dict(color="orange")))
        fig.add_trace(go.Scatter(x=prices["date"], y=prices["EMA26"], mode="lines", name="EMA 26", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=prices["date"], y=prices["Upper"], mode="lines", name="Bande Supérieure", line=dict(color="lightgrey", dash="dot")))
        fig.add_trace(go.Scatter(x=prices["date"], y=prices["Lower"], mode="lines", name="Bande Inférieure", line=dict(color="lightgrey", dash="dot")))
        fig.update_layout(
            title=f"Prix & Indicateurs techniques ({coin_name})",
            xaxis_title="Date",
            yaxis_title="Prix (USD)",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("💰 Prix actuel (USD)", f"{prices['price'].iloc[-1]:,.2f}")
        st.metric("📈 Variation 24h", f"{data.loc[data['id']==coin_id, 'price_change_percentage_24h'].values[0]:+.2f}%")
        st.metric("💪 RSI (14j)", f"{prices['RSI'].iloc[-1]:.2f}")
        st.metric("⚡ MACD", f"{prices['MACD'].iloc[-1]:.2f}")
        st.metric("📉 Signal MACD", f"{prices['Signal'].iloc[-1]:.2f}")

    # Graphiques RSI et MACD
    rsi_chart = go.Figure()
    rsi_chart.add_trace(go.Scatter(x=prices["date"], y=prices["RSI"], mode="lines", name="RSI", line=dict(color="green")))
    rsi_chart.add_hline(y=70, line_dash="dot", line_color="red")
    rsi_chart.add_hline(y=30, line_dash="dot", line_color="blue")
    rsi_chart.update_layout(title="RSI (14 jours)", template="plotly_dark", height=200)
    st.plotly_chart(rsi_chart, use_container_width=True)

    macd_chart = go.Figure()
    macd_chart.add_trace(go.Scatter(x=prices["date"], y=prices["MACD"], name="MACD", line=dict(color="orange")))
    macd_chart.add_trace(go.Scatter(x=prices["date"], y=prices["Signal"], name="Signal", line=dict(color="blue")))
    macd_chart.update_layout(title="MACD & Signal", template="plotly_dark", height=200)
    st.plotly_chart(macd_chart, use_container_width=True)

    st.divider()

# --------------------------------------------------
# 🧠 EXPLICATIONS
# --------------------------------------------------
st.markdown("## 🧩 Explications des indicateurs techniques")

with st.expander("🔸 RSI (Relative Strength Index)"):
    st.markdown("""
    - Mesure la **force du momentum** d’un actif.
    - **RSI > 70** → surachat (correction probable)  
    - **RSI < 30** → survente (rebond possible)  
    """)

with st.expander("🔸 EMA (Moyenne mobile exponentielle)"):
    st.markdown("""
    - **EMA 9** = court terme ; **EMA 26** = moyen terme  
    - Si **EMA9 > EMA26** → tendance haussière  
    - Si **EMA9 < EMA26** → tendance baissière  
    """)

with st.expander("🔸 MACD (Moving Average Convergence Divergence)"):
    st.markdown("""
    - Compare deux moyennes mobiles (12 et 26 périodes).  
    - **MACD > Signal** = momentum haussier  
    - **MACD < Signal** = momentum baissier  
    - Indique les changements de dynamique.  
    """)

with st.expander("🔸 Bandes de Bollinger"):
    st.markdown("""
    - Mesurent la **volatilité**.  
    - Plus les bandes s’écartent, plus le marché est **instable**.  
    - Prix proche de la bande supérieure → **surachat**  
    - Prix proche de la bande inférieure → **survente**  
    """)

st.caption("💡 Données actualisées automatiquement via l’API CoinGecko (rafraîchissement ~5 min)")