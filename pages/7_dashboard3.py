import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

# --------------------------------------------------
# 🎯 CONFIGURATION
# --------------------------------------------------
st.set_page_config(page_title="Dashboard Crypto Complet", layout="wide")
st.title("💹 Tableau de bord Crypto — Analyse Technique")
st.caption("Suivi des cryptos principales (BTC, ETH, SOL, SUI) avec indicateurs visuels et graphiques")

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
    return sma, upper, lower, std

# --------------------------------------------------
# 📈 TABLEAU DES DONNÉES
# --------------------------------------------------
data = get_market_data()

# Données principales
st.subheader("📊 Données de marché (USD)")
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

st.markdown("---")

# --------------------------------------------------
# 🔍 ANALYSE PAR CRYPTO
# --------------------------------------------------
for coin_id, coin_name in COINS.items():
    st.markdown(f"## 🪙 {coin_name}")

    prices = get_historical_prices(coin_id, 30)
    prices["EMA9"] = ema(prices["price"], 9)
    prices["EMA26"] = ema(prices["price"], 26)
    prices["RSI"] = compute_rsi(prices["price"])
    prices["MACD"], prices["Signal"] = compute_macd(prices["price"])
    prices["SMA"], prices["Upper"], prices["Lower"], prices["Vol"] = compute_bollinger(prices["price"])

    current_price = prices["price"].iloc[-1]
    variation_24h = data.loc[data["id"] == coin_id, "price_change_percentage_24h"].values[0]
    rsi_now = prices["RSI"].iloc[-1]
    ema9_now = prices["EMA9"].iloc[-1]
    ema26_now = prices["EMA26"].iloc[-1]
    macd_now = prices["MACD"].iloc[-1]
    signal_now = prices["Signal"].iloc[-1]
    vol_now = prices["Vol"].iloc[-1]

    # 🧭 Résumé visuel
    tendance = "🟢 **Haussière**" if ema9_now > ema26_now else "🔴 **Baissière**"
    rsi_etat = "⚠️ Surachat (>70)" if rsi_now > 70 else "💪 Survente (<30)" if rsi_now < 30 else "🟡 Neutre"
    macd_signal = "📈 Momentum haussier" if macd_now > signal_now else "📉 Momentum baissier"

    with st.container():
        st.markdown(f"""
        **Prix actuel :** {current_price:,.2f} USD  
        **Variation 24h :** {variation_24h:+.2f}%  
        **Tendance EMA :** {tendance}  
        **RSI :** {rsi_now:.2f} → {rsi_etat}  
        **MACD :** {macd_now:.2f} / Signal {signal_now:.2f} → {macd_signal}  
        **Volatilité :** {vol_now:.2f}
        """)
    
    # 📊 Graphique principal : Prix + EMA + Bollinger
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["price"], mode="lines", name="Prix", line=dict(color="black")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["EMA9"], mode="lines", name="EMA 9", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["EMA26"], mode="lines", name="EMA 26", line=dict(color="cyan")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["Upper"], mode="lines", name="Bande Supérieure", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["Lower"], mode="lines", name="Bande Inférieure", line=dict(color="gray", dash="dot")))
    fig.update_layout(title=f"Évolution du prix de {coin_name}", template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)

    # RSI Chart
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=prices["date"], y=prices["RSI"], mode="lines", name="RSI", line=dict(color="green")))
    rsi_fig.add_hline(y=70, line_dash="dot", line_color="red")
    rsi_fig.add_hline(y=30, line_dash="dot", line_color="blue")
    rsi_fig.update_layout(title="RSI (14 jours)", template="plotly_dark", height=600)
    st.plotly_chart(rsi_fig, use_container_width=True)

    # MACD Chart
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Scatter(x=prices["date"], y=prices["MACD"], name="MACD", line=dict(color="orange")))
    macd_fig.add_trace(go.Scatter(x=prices["date"], y=prices["Signal"], name="Signal", line=dict(color="blue")))
    macd_fig.update_layout(title="MACD & Signal", template="plotly_dark", height=600)
    st.plotly_chart(macd_fig, use_container_width=True)

    st.markdown("---")

# --------------------------------------------------
# 🧠 LÉGENDE
# --------------------------------------------------
st.markdown("""
### 🧭 Légende des indicateurs :
- **RSI (Relative Strength Index)** : mesure le momentum.  
  - RSI > 70 → surachat  
  - RSI < 30 → survente  
- **EMA (Exponential Moving Average)** : moyenne mobile.  
  - EMA9 > EMA26 → tendance haussière  
  - EMA9 < EMA26 → tendance baissière  
- **MACD (Moving Average Convergence Divergence)** : indique le momentum haussier/baissier.  
- **Bandes de Bollinger** : mesurent la volatilité.  
""")

st.caption("💡 Données actualisées automatiquement via l’API CoinGecko (toutes les 5 minutes).")