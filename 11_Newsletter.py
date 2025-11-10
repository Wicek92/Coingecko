import streamlit as st
import feedparser
import requests
from openai import OpenAI
from datetime import datetime

# === PAGE CONFIG ===
st.set_page_config(page_title="📰 Résumé Grok Crypto", page_icon="🤖", layout="centered")

st.title("🤖 Grok résume Google News Crypto pour toi")
st.markdown("**Les 20 dernières news → 1 résumé intelligent en 5 secondes**")

# === SIDEBAR : TA CLÉ API ===
with st.sidebar:
    st.header("🔑 Ta clé API Grok")
    api_key = st.text_input("XAI_API_KEY", type="password", help="Va sur https://x.ai/api")
    if api_key:
        st.success("Clé chargée !")

# === CHOIX DU THÈME ===
theme = st.selectbox("Choisis ton thème :", 
                     ["Bitcoin & Cryptomonnaies", "IA & Tech", "France", "Monde", "Personnalisé"])

themes = {
    "Bitcoin & Cryptomonnaies": "bitcoin+OR+cryptomonnaie+OR+ethereum+OR+solana",
    "IA & Tech": "intelligence+artificielle+OR+IA+OR+grok+OR+openai",
    "France": "when:1d",  # dernières 24h France
    "Monde": "",
    "Personnalisé": st.text_input("Ton mot-clé :", "bitcoin") if theme == "Personnalisé" else ""
}

query = themes[theme]

# === BOUTON MAGIQUE ===
if st.button("🚀 Lancer le résumé Grok", type="primary"):
    if not api_key:
        st.error("Met ta clé API dans la sidebar !")
    else:
        with st.spinner("Je récupère les news sur Google..."):
            # RSS Google News France
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries[:20]:
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                    "summary": entry.summary[:500] if 'summary' in entry else ""
                })
        
        if not articles:
            st.error("Aucune news trouvée 😅 Réessaie avec un autre thème")
        else:
            with st.spinner("Grok 4 analyse tout ça (5 secondes)..."):
                # Prépare le texte pour Grok
                news_text = "\n\n".join([
                    f"{i+1}. {a['title']}\nLien: {a['link']}\nDate: {a['published']}\nRésumé: {a['summary']}"
                    for i, a in enumerate(articles)
                ])
                
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.x.ai/v1"
                )
                
                response = client.chat.completions.create(
                    model="grok-4",
                    messages=[
                        {"role": "system", "content": "Tu es Grok, l'IA la plus intelligente du monde. Résume en français, clair, avec des bullet points, les points clés, les tendances, et ce qu'il faut retenir pour un trader crypto. Sois direct et fun."},
                        {"role": "user", "content": f"Résume ces 20 dernières news crypto en un résumé puissant :\n\n{news_text}"}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                
                resume = response.choices[0].message.content
                
                st.success("Résumé Grok prêt ! 🎉")
                st.markdown(f"### 🤖 **Résumé par Grok 4** - {datetime.now().strftime('%d/%m %H:%H')}")
                st.markdown(resume)
                
                with st.expander("Voir les 20 sources brutes"):
                    for a in articles:
                        st.markdown(f"- **{a['title']}**  \n  [{a['published']}]({a['link']})")