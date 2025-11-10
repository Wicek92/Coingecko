import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Tableau de bord Crypto", layout="wide")
st.title("💹 Tableau de bord Crypto — Analyse technique complète")
st.caption("Visualisation dynamique de Bitcoin, Ethereum, Solana et Sui (RSI, EMA, MACD, tendances)")

COINS = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "solana": "Solana",
    "sui": "Sui"
}
CURRENCY = "usd"

# --------------------------------------------------
# FONCTIONS
# --------------------------------------------------
@st.cache_data(ttl=300)
def get_market_data():
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={CURRENCY}&ids={','.join(COINS.keys())}&sparkline=false"
    return pd.DataFrame(requests.get(url).json())



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
    return 100 - (100 / (1 + rs))

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
# TABLEAU PRINCIPAL
# --------------------------------------------------
data = get_market_data()

# Calcul RSI + Tendance
tech_data = []
for coin_id, coin_name in COINS.items():
    prices = get_historical_prices(coin_id, 30)
    prices["RSI"] = compute_rsi(prices["price"])
    prices["EMA9"] = ema(prices["price"], 9)
    prices["EMA26"] = ema(prices["price"], 26)
    last = prices.iloc[-1]
    tendance = "Haussière" if last["EMA9"] > last["EMA26"] else "Baissière"
    couleur = "🟢" if tendance == "Haussière" else "🔴"
    rsi_val = round(last["RSI"], 2)
    macd, signal = compute_macd(prices["price"])
    tech_data.append({
        "Nom": coin_name,
        "Prix (USD)": data.loc[data["id"] == coin_id, "current_price"].values[0],
        "Variation 24h (%)": data.loc[data["id"] == coin_id, "price_change_percentage_24h"].values[0],
        "RSI": rsi_val,
        "Tendance": f"{couleur} {tendance}",
        "MACD": round(macd.iloc[-1], 2),
        "Signal": round(signal.iloc[-1], 2)
    })

df = pd.DataFrame(tech_data)
df = df[["Nom", "Prix (USD)", "Variation 24h (%)", "RSI", "MACD", "Signal", "Tendance"]]

def color_percent(val):
    color = "green" if val > 0 else "red"
    return f"color: {color}"

st.subheader("📊 Indicateurs techniques (24h / 7j / 30j)")
st.dataframe(
    df.style.format({
        "Prix (USD)": "{:,.2f}",
        "Variation 24h (%)": "{:+.2f}",
        "RSI": "{:.2f}",
        "MACD": "{:.2f}",
        "Signal": "{:.2f}"
    }).applymap(color_percent, subset=["Variation 24h (%)"]),
    use_container_width=True
)

st.markdown("---")

# --------------------------------------------------
# ANALYSE PAR CRYPTO
# --------------------------------------------------
for coin_id, coin_name in COINS.items():
    st.markdown(f"## 📈 {coin_name}")

    prices = get_historical_prices(coin_id, 30)
    prices["EMA9"] = ema(prices["price"], 9)
    prices["EMA26"] = ema(prices["price"], 26)
    prices["RSI"] = compute_rsi(prices["price"])
    prices["MACD"], prices["Signal"] = compute_macd(prices["price"])
    prices["SMA"], prices["Upper"], prices["Lower"], prices["Vol"] = compute_bollinger(prices["price"])

    current_price = prices["price"].iloc[-1]
    variation_24h = data.loc[data["id"] == coin_id, "price_change_percentage_24h"].values[0]
    rsi_now = prices["RSI"].iloc[-1]
    macd_now = prices["MACD"].iloc[-1]
    signal_now = prices["Signal"].iloc[-1]
    tendance = "🟢 **Tendance haussière**" if prices["EMA9"].iloc[-1] > prices["EMA26"].iloc[-1] else "🔴 **Tendance baissière**"
    rsi_txt = "⚠️ Surachat (>70)" if rsi_now > 70 else "💪 Survente (<30)" if rsi_now < 30 else "🟡 Neutre"

    # Résumé horizontal
    st.markdown(
        f"**Prix :** {current_price:,.2f} USD | "
        f"**Variation 24h :** {variation_24h:+.2f}% | "
        f"**RSI :** {rsi_now:.2f} → {rsi_txt} | "
        f"**MACD :** {macd_now:.2f} / {signal_now:.2f} | "
        f"{tendance}"
    )

    # Graphique principal
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["price"], mode="lines", name="Prix", line=dict(color="black", width=2)))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["EMA9"], mode="lines", name="EMA 9", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["EMA26"], mode="lines", name="EMA 26", line=dict(color="cyan")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["Upper"], mode="lines", name="Bande Supérieure", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=prices["date"], y=prices["Lower"], mode="lines", name="Bande Inférieure", line=dict(color="gray", dash="dot")))
    fig.update_layout(title=f"Évolution du prix — {coin_name}", template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)

    # RSI Graph
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=prices["date"], y=prices["RSI"], mode="lines", name="RSI", line=dict(color="green")))
    rsi_fig.add_hline(y=70, line_dash="dot", line_color="red")
    rsi_fig.add_hline(y=30, line_dash="dot", line_color="blue")
    rsi_fig.update_layout(title="RSI (14 jours)", template="plotly_dark", height=280)
    st.plotly_chart(rsi_fig, use_container_width=True)

    # MACD Graph
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Scatter(x=prices["date"], y=prices["MACD"], name="MACD", line=dict(color="orange")))
    macd_fig.add_trace(go.Scatter(x=prices["date"], y=prices["Signal"], name="Signal", line=dict(color="blue")))
    macd_fig.update_layout(title="MACD & Signal", template="plotly_dark", height=280)
    st.plotly_chart(macd_fig, use_container_width=True)

    st.markdown("---")

# --------------------------------------------------
# LÉGENDE
# --------------------------------------------------
st.markdown("""
### 🧭 Légende :
- **RSI (Relative Strength Index)** : momentum du marché  
  - RSI > 70 → surachat  
  - RSI < 30 → survente  
- **EMA (Exponential Moving Average)** : moyenne mobile exponentielle  
  - EMA9 > EMA26 → tendance haussière  
  - EMA9 < EMA26 → tendance baissière  
- **MACD (Moving Average Convergence Divergence)** : montre le momentum  
  - MACD > Signal → momentum haussier  
  - MACD < Signal → momentum baissier  
""")

st.caption("💡 Données actualisées automatiquement (API CoinGecko, toutes les 5 minutes)")
