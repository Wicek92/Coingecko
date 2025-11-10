# app.py
"""
Streamlit app pour afficher des statistiques sur le CBBI (Crypto Bitcoin Bull Run Index).
- Tente l’API JSON publique
- Si échec, effectue un scrapping HTML pour extraire la valeur “Confidence”
- Affiche score actuel, graphiques historiques (si données JSON complètes), tableau & export CSV
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Dict, Any
from bs4 import BeautifulSoup

CBBI_JSON_URL = "https://colintalkscrypto.com/cbbi/data/latest.json"
CBBI_WEB_URL = "https://colintalkscrypto.com/cbbi/"

st.set_page_config(page_title="CBBI — Statistiques", layout="wide")

@st.cache_data(ttl=300)
def fetch_cbbi_data() -> Dict[str, Any]:
    """Récupère les données CBBI via JSON ou fallback HTML scrapping."""
    # 1) tentative API JSON
    try:
        resp = requests.get(CBBI_JSON_URL, headers={"Accept": "application/json"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        st.warning(f"API JSON inaccessible : {e}. On tente le scrapping web …")

    # 2) fallback scrapping HTML
    try:
        resp2 = requests.get(CBBI_WEB_URL, timeout=10)
        resp2.raise_for_status()
        soup = BeautifulSoup(resp2.text, "html.parser")
        # chercher un élément contenant la valeur « Confidence »
        # Note : ce sélecteur peut nécessiter ajustement selon le HTML réel
        elem = soup.select_one("h1.title.confidence-score-value") or soup.select_one("div.confidence-score-value") or soup.find(string="Confidence").find_next()
        if elem:
            # nettoyer le texte pour obtenir un float
            text = elem.text.strip().replace(",", "").replace("%", "")
            val = float(text)
            # créer un JSON minimal
            return {"Confidence": {"fallback": val}}
        else:
            st.error("Élément « Confidence » introuvable dans le HTML.")
            return {}
    except Exception as e2:
        st.error(f"Scrapping web échoué aussi : {e2}")
        return {}

def build_dataframe_from_section(section: Dict[str, Any], name: str) -> pd.Series:
    idx = []
    vals = []
    for k, v in section.items():
        try:
            ts = int(k)
            dt = datetime.utcfromtimestamp(ts)
        except Exception:
            try:
                dt = pd.to_datetime(k)
            except Exception:
                continue
        idx.append(dt)
        vals.append(v)
    if not idx:
        return pd.Series(dtype=float, name=name)
    s = pd.Series(data=vals, index=pd.DatetimeIndex(idx), name=name).sort_index()
    return s

def build_master_df(json_data: Dict[str, Any]) -> pd.DataFrame:
    series_list = []
    for key, val in json_data.items():
        if isinstance(val, dict):
            s = build_dataframe_from_section(val, name=key)
            if not s.empty:
                series_list.append(s)
    if not series_list:
        return pd.DataFrame()
    df = pd.concat(series_list, axis=1)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# UI
st.title("CBBI — Statistiques & Visualisation")
st.markdown("Source des données : Colin Talks Crypto (CBBI). L'application récupère le JSON public du CBBI et/ou effectue un scrapping de secours. Ce n’est pas un conseil financier.")

with st.spinner("Récupération des données…"):
    data = fetch_cbbi_data()

if not data:
    st.stop()

df = build_master_df(data)

# Afficher score de confiance actuel
latest_cols = {}
if "Confidence" in data and isinstance(data["Confidence"], dict):
    try:
        # si la clé est un timestamp
        keys = [int(k) for k in data["Confidence"].keys()]
        keys.sort()
        last_ts = keys[-1]
        last_val = data["Confidence"].get(str(last_ts))
        latest_cols["Confidence"] = (last_val, datetime.utcfromtimestamp(last_ts))
    except Exception:
        # fallback “fallback” key
        if "fallback" in data["Confidence"]:
            latest_cols["Confidence"] = (data["Confidence"]["fallback"], None)

# Autres variables si présentes (ex: Price)
if "Price" in data and isinstance(data["Price"], dict):
    try:
        keys = [int(k) for k in data["Price"].keys()]
        keys.sort()
        last_ts = keys[-1]
        last_val = data["Price"].get(str(last_ts))
        latest_cols["Price"] = (last_val, datetime.utcfromtimestamp(last_ts))
    except Exception:
        pass

col1, col2, col3 = st.columns([1,1,2])
with col1:
    if "Confidence" in latest_cols:
        val, dt = latest_cols["Confidence"]
        st.metric("CBBI — Confidence (latest)", f"{val}")
        if dt:
            st.caption(f"Timestamp (UTC): {dt.isoformat()}")
    else:
        st.write("Confidence : non disponible")

with col2:
    if "Price" in latest_cols:
        price, pdt = latest_cols["Price"]
        st.metric("BTC Price (latest)", f"{price}")
        st.caption(f"Timestamp (UTC): {pdt.isoformat()}")
    else:
        st.write("Price : non disponible")

with col3:
    st.markdown("**Sections trouvées dans le JSON**")
    st.write(sorted(list(data.keys())))

st.markdown("---")

if df.empty:
    st.info("Aucune série temporelle détectée dans le JSON récupéré.")
else:
    st.subheader("Graphiques historiques")
    cols = list(df.columns)
    default_to_plot = [c for c in ["Confidence", "Price"] if c in cols]
    to_plot = st.multiselect("Choisir les séries à tracer", options=cols, default=default_to_plot)
    if to_plot:
        for col in to_plot:
            fig = px.line(df, x=df.index, y=col, title=f"{col} — historique", labels={"x":"Date (UTC)", col:col})
            fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tableau : dernières valeurs")
    last_vals = df.ffill().iloc[-1:].T
    last_vals.columns = ["latest_value"]
    last_vals["latest_timestamp"] = last_vals.index.map(lambda _: df.index[-1])
    st.dataframe(last_vals)

    for possible in ("Components", "Component", "SubIndicators", "SubIndicatorsRaw"):
        if possible in data:
            st.subheader(f"{possible}")
            st.json(data[possible])

    csv = df.reset_index().rename(columns={"index":"datetime"}).to_csv(index=False)
    st.download_button("Télécharger CSV (toutes séries)", data=csv, file_name="cbbi_series.csv", mime="text/csv")

st.markdown("---")
st.caption("Données provenant du CBBI public — outil combinant plusieurs métriques on‐chain/techniques pour évaluer la confiance dans un pic de bull run. Ce n’est pas un conseil financier.")