# 4_₿_Crypto_ETFs.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# === CONFIG PAGE ===
st.set_page_config(
    page_title="Crypto + CW8 + LQQQ",
    page_icon="₿",
    layout="wide"
)

# === ACTIFS ===
CRYPTOS = {"Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana", "SUI": "sui"}
ETFS = {"CW8": "CW8.PA", "LQQQ": "LQQ.PA"}

# === DONNÉES CRYPTO (CoinGecko) ===
@st.cache_data(ttl=45)
def get_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': ','.join(CRYPTOS.values()),
        'price_change_percentage': '24h,7d,30d',
        'order': 'market_cap_desc'
    }
    try:
        data = requests.get(url, params=params, timeout=10).json()
        return data
    except:
        st.error("CoinGecko HS")
        return []

# === DONNÉES ETF (yfinance avec protection) ===
@st.cache_data(ttl=45)
def get_etfs():
    try:
        import yfinance as yf
        result = {}
        for name, ticker in ETFS.items():
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) < 2:
                result[name] = {"price": "N/A", "24h": 0.0}
                continue
            price = round(hist["Close"].iloc[-1], 2)
            change_24h = round((hist["Close"].iloc[-1] / hist["Close"].iloc[-2] - 1) * 100, 2)
            result[name] = {"price": price, "24h": change_24h}
        return result
    except Exception as e:
        st.warning(f"ETF désactivés (yfinance manquant ou erreur)\nInstalle avec : pip install yfinance")
        return {}

# === BOUCLE PRINCIPALE ===
placeholder = st.empty()

while True:
    with placeholder.container():
        st.title("₿ Crypto + ETF (CW8 • LQQQ) Live")
        st.markdown(f"**Mise à jour :** {datetime.now().strftime('%H:%M:%S')}")

        # --- Récupération données ---
        crypto_data = get_crypto()
        etf_data = get_etfs()

        # --- Construction du tableau ---
        rows = []

        # Cryptos
        for coin in crypto_data:
            name = [k for k, v in CRYPTOS.items() if v == coin["id"]][0]
            rows.append({
                "Actif": f"**{name}**",
                "Prix": f"${coin['current_price']:,.2f}",
                "24h": coin['price_change_percentage_24h'],
                "7d": coin.get('price_change_percentage_7d_in_currency', 0),
                "30d": coin.get('price_change_percentage_30d_in_currency', 0),
                "Type": "Crypto"
            })

        # ETFs
        for name, d in etf_data.items():
            rows.append({
                "Actif": f"**{name}** (ETF)",
                "Prix": f"€{d['price']}" if d['price'] != "N/A" else "N/A",
                "24h": d['24h'],
                "7d": 0.0,
                "30d": 0.0,
                "Type": "ETF"
            })

        if not rows:
            st.error("Aucune donnée récupérée")
            time.sleep(10)
            continue

        df = pd.DataFrame(rows)

        # === FONCTION DE COULEUR (sans bug d'index) ===
        def color_negative_red(val):
            if isinstance(val, (int, float)) and val != 0:
                color = "lime" if val > 0 else "red"
                return f'color: {color}; font-weight: bold'
            return ''

        # Application du style UNIQUEMENT sur les colonnes numériques
        styled_df = df.style \
            .applymap(color_negative_red, subset=["24h", "7d", "30d"]) \
            .format({
                "24h": "{:+.2f}%",
                "7d": "{:+.2f}%",
                "30d": "{:+.2f}%"
            })

        # === AFFICHAGE FINAL (PLUS DE KEYERROR) ===
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

        # 6 cartes en haut
        cols = st.columns(6)
        for i in range(min(6, len(df))):
            with cols[i]:
                row = df.iloc[i]
                st.metric(
                    label=row["Actif"].replace("**", "").replace(" (ETF)", ""),
                    value=row["Prix"],
                    delta=f"{row['24h']:+.2f}%" if row['24h'] != 0 else None
                )

    # === AUTO REFRESH ===
    time.sleep(45)
    st.rerun()