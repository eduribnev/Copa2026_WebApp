import streamlit as st
import pandas as pd
import requests
import json
import os
import feedparser
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Hub Copa 2026", layout="wide")

# --- ESTILOS ---
def titulo_verde(texto):
    st.markdown(f"<h2 style='color: #00FF00;'>{texto}</h2>", unsafe_allow_html=True)

def sub_verde(texto):
    st.markdown(f"<h3 style='color: #00FF00;'>{texto}</h3>", unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=600)
def carregar_dados():
    caminho = 'dados_copa.json'
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return None
    return None

def buscar_odds():
    # 1. Carregamento seguro da chave via Secrets (Já validado no seu Desktop)
    try:
        api_key = st.secrets["ODDS_API_KEY"]
    except Exception:
        # Se você apagar o secrets.toml por engano, o app avisa sem quebrar
        return None 
    
    url = f"https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup_winner/odds/?apiKey={api_key}&regions=eu&markets=outrights"
    
    # Dicionário de traduções para manter o padrão visual
    traducoes = {
        "Argentina": "Argentina", "France": "França", "Brazil": "Brasil", 
        "England": "Inglaterra", "Spain": "Espanha", "Germany": "Alemanha", 
        "Japan": "Japão", "Portugal": "Portugal"
    }
    
    try:
        response = requests.get(url, timeout=10)
        
        # 2. Tratamento de status da API
        if response.status_code == 200:
            raw_data = response.json()
            if raw_data:
                # Extração segura seguindo a hierarquia do JSON da Odds API
                data = raw_data[0]['bookmakers'][0]['markets'][0]['outcomes']
                lista = [
                    {
                        'time': traducoes.get(o['name'], o['name']), 
                        'chance': round(100/o['price'], 2)
                    } for o in data
                ]
                # Retorna o Top 12 ordenado por maior probabilidade
                return pd.DataFrame(lista).sort_values('chance', ascending=False).head(12)
        
        # 3. Se o status for 401 (créditos esgotados), o Streamlit avisa o motivo real
        elif response.status_code == 401:
            st.warning("Aguardando renovação mensal de créditos da API (Próximo reset: 13/05).")
            return None
            
        return None

    except Exception as e:
        # Log técnico para o seu terminal no VS Code
        print(f"Erro de conexão na busca de Odds: {e}")
        return None

# --- INÍCIO DO APP ---
dados = carregar_dados()

if not dados:
    st.error("❌ Arquivo dados_copa.json não encontrado.")
    st.stop()

st.title("🏆 Hub Oficial - Copa do Mundo 2026")
aba1, aba2, aba3, aba4 = st.tabs(["📍 Visão Geral", "📊 Grupos", "📅 Tabela de Jogos", "📈 Favoritos e Odds"])

with aba1:
    titulo_verde("📍 Destaques")
    col1, col2 = st.columns([1, 2])
    with col1:
        dias = (datetime(2026, 6, 11) - datetime.now()).days
        st.metric("Dias para a Copa", f"{dias}")
    with col2:
        feed = feedparser.parse("https://news.google.com/rss/search?q=Copa+2026+FIFA&hl=pt-BR&gl=BR&ceid=BR:pt-419")
        for entry in feed.entries[:3]:
            st.markdown(f"✅ [{entry.title}]({entry.link})")

with aba2:
    titulo_verde("📊 Grupos (48 Seleções)")
    df_sel = pd.DataFrame(dados["selecoes"])
    grupos = sorted(df_sel['grupo'].unique())
    c1, c2 = st.columns(2)
    for i, g in enumerate(grupos):
        with c1 if i % 2 == 0 else c2:
            sub_verde(f"Grupo {g}")
            st.dataframe(df_sel[df_sel['grupo'] == g][['nome', 'PTS', 'SG']], hide_index=True, use_container_width=True)

with aba3:
    titulo_verde("📅 Tabela de Jogos")
    jogos = dados.get("jogos", [])
    with st.container(height=500):
        for j in jogos:
            col_info, col_link = st.columns([3, 1])
            with col_info:
                # Pegando os dados exatos do seu JSON
                st.write(f"**{j.get('data')}** | Grupo {j.get('grupo')} — **{j.get('time1')} vs {j.get('time2')}**")
            with col_link:
                # Recuperando os links que estavam faltando
                links = j.get("links", {})
                if links:
                    with st.popover("📺 Assistir"):
                        st.markdown(f"[CazéTV]({links.get('cazetv', '#')})")
                        st.markdown(f"[SporTV]({links.get('sportv', '#')})")
                        st.markdown(f"[Globo Esporte]({links.get('ge', '#')})")
            st.divider()

with aba4:
    titulo_verde("📈 Probabilidades de Título")
    df_odds = buscar_odds()
    if df_odds is not None:
        # Gráfico Plotly que respeita a ordem e cor verde neon
        fig = px.bar(df_odds.sort_values('chance', ascending=True), 
                     x='chance', y='time', orientation='h', text='chance',
                     color_discrete_sequence=['#00FF00'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          font_color="#00FF00", xaxis_title="Chance %", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        # Tabela de Odds
        df_tab = df_odds.copy()
        df_tab['Odd'] = (100 / df_tab['chance']).round(2)
        st.dataframe(df_tab, hide_index=True, use_container_width=True)
    else:
        st.info("Insira sua ODDS_API_KEY nos Secrets para ver as probabilidades reais.")