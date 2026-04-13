import streamlit as st
import pandas as pd
import json
import requests
import feedparser
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------
# FUNÇÕES DE APOIO E INTEGRAÇÃO (API E DADOS)
# ---------------------------------------------------------

def buscar_dados_api():
    try:
        if "API_KEY" not in st.secrets:
            st.sidebar.error("Chave API_KEY não encontrada nos Secrets!")
            return None
            
        api_key = st.secrets["API_KEY"]
        url = "https://v3.football.api-sports.io/fixtures?league=1&season=2026"
        
        headers = {
            'x-apisports-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # LOG DE DEPURAÇÃO PARA VOCÊ VER NO NAVEGADOR
        if data.get('errors'):
            st.sidebar.error(f"Erro da API: {data['errors']}")
            return None
            
        if data.get('response'):
            return data['response']
        else:
            st.sidebar.info("API conectada, mas sem jogos para 2026 ainda.")
            return None

    except Exception as e:
        st.sidebar.warning(f"Falha na conexão: {e}")
    return None

def carregar_noticias():
    """RSS do GE focado em Futebol Internacional."""
    url_rss = "https://ge.globo.com/servico/semantico/editorias/video/esporte/futebol/futebol-internacional/feed.rss"
    try:
        feed = feedparser.parse(url_rss)
        if feed.entries:
            for entry in feed.entries[:3]:
                with st.expander(f"📌 {entry.title}"):
                    st.write(entry.summary[:200] + "...")
                    st.markdown(f"[Leia a matéria completa]({entry.link})")
        else:
            st.info("Nenhuma atualização nova no momento.")
    except Exception:
        st.error("Erro ao carregar notícias dinâmicas.")

@st.cache_data(ttl=600)
def carregar_dados_locais(caminho):
    """Carrega o backup/base do arquivo JSON."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de backup: {e}")
        return None

def calcular_classificacao(selecoes, jogos):
    """Processa placares e gera a tabela de pontos."""
    tabela = {s['nome']: {'Grupo': s['grupo'], 'PTS': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0} for s in selecoes}
    for jogo in jogos:
        t1, t2 = jogo['time1'], jogo['time2']
        p1, p2 = jogo['placar1'], jogo['placar2']
        if p1 is not None and p2 is not None:
            tabela[t1]['J'] += 1
            tabela[t2]['J'] += 1
            tabela[t1]['GP'] += p1
            tabela[t1]['GC'] += p2
            tabela[t2]['GP'] += p2
            tabela[t2]['GC'] += p1
            if p1 > p2:
                tabela[t1]['PTS'] += 3; tabela[t1]['V'] += 1; tabela[t2]['D'] += 1
            elif p2 > p1:
                tabela[t2]['PTS'] += 3; tabela[t2]['V'] += 1; tabela[t1]['D'] += 1
            else:
                tabela[t1]['PTS'] += 1; tabela[t2]['PTS'] += 1; tabela[t1]['E'] += 1; tabela[t2]['E'] += 1
    for t in tabela.values():
        t['SG'] = t['GP'] - t['GC']
    df = pd.DataFrame.from_dict(tabela, orient='index').reset_index()
    df.rename(columns={'index': 'Seleção'}, inplace=True)
    return df.sort_values(by=['Grupo', 'PTS', 'SG', 'GP'], ascending=[True, False, False, False])

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ---------------------------------------------------------
st.set_page_config(page_title="World Cup 2026 Hub", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    :root {
        --neon-green: #00FF87;
        --magenta: #FF004D;
        --purple: #4B0082;
    }
    .stApp { background-color: #0d0d0d; color: #ffffff; }
    h1, h2, h3 { color: #00FF87 !important; font-family: 'Arial Black', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1a1a; border-radius: 5px; color: white; padding: 10px 20px;}
    .stTabs [aria-selected="true"] { background-color: #4B0082 !important; color: #00FF87 !important; border-bottom: 3px solid #FF004D; }
    .metric-card { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 5px solid #FF004D; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CARREGAMENTO DE DADOS (HÍBRIDO: API + JSON)
# ---------------------------------------------------------
dados = carregar_dados_locais("dados_copa.json")
dados_api = buscar_dados_api()

if not dados:
    st.stop()

# Aqui, no futuro, faremos o "merge" dos placares da API no dicionário 'dados'
df_classificacao = calcular_classificacao(dados['selecoes'], dados['jogos'])
df_jogos = pd.DataFrame(dados['jogos'])

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://i.pinimg.com/1200x/2f/3b/60/2f3b607f2525dd613034cd05ef8f53bc.jpg", width=200)
    if st.button("🔄 Atualizar Tudo", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if dados_api:
        st.success("Conectado à API-Sports")
    st.caption("Desenvolvido por Eduardo Neves")

# ---------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------
st.title("🏆 Hub Oficial - Copa do Mundo 2026")

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📍 Visão Geral", "📊 Grupos", "📅 Tabela de Jogos", "📺 Onde Assistir", "📈 Favoritos e Odds"
])

# --- ABA 1: VISÃO GERAL ---
with aba1:
    st.header("Contagem Regressiva e Notícias")
    col1, col2 = st.columns([1, 2])
    with col1:
        data_copa = datetime(2026, 6, 11)
        faltam = (data_copa - datetime.now()).days
        st.markdown(f'<div class="metric-card"><h1 style="color:#FF004D!important;font-size:4rem;margin:0;">{faltam}</h1><h3 style="margin:0;color:white!important;">Dias para a Copa</h3></div>', unsafe_allow_html=True)
    with col2:
        carregar_noticias()

# --- ABA 2: GRUPOS ---
with aba2:
    st.header("Classificação por Grupos")
    nomes_col = {'PTS':'Pontos','J':'Jogos','V':'Vitórias','E':'Empates','D':'Derrotas','GP':'Gols Pró','GC':'Gols Contra','SG':'Saldo de Gols'}
    for grupo in sorted(df_classificacao['Grupo'].unique()):
        st.subheader(f"Grupo {grupo}")
        df_g = df_classificacao[df_classificacao['Grupo'] == grupo].drop(columns=['Grupo']).rename(columns=nomes_col)
        df_g.index = range(1, len(df_g) + 1)
        st.dataframe(df_g, use_container_width=True, column_config={col: st.column_config.Column(alignment="center") for col in df_g.columns})
        st.divider()

# --- ABA 3: TABELA DE JOGOS ---
with aba3:
    st.header("Jogos")
    for _, row in df_jogos.iterrows():
        placar = f"{int(row['placar1'])} x {int(row['placar2'])}" if pd.notnull(row['placar1']) else "vs"
        st.markdown(f"**{row['data']}** | {row['time1']} `{placar}` {row['time2']}")
        st.divider()

# --- ABA 4: ONDE ASSISTIR ---
with aba4:
    st.header("Transmissões")
    for idx, row in df_jogos.iterrows():
        st.subheader(f"{row['time1']} vs {row['time2']}")
        links = row.get("links", {})
        cols = st.columns(5)
        canais = [("CazéTV", "cazetv"), ("GE", "ge"), ("SporTV", "sportv"), ("ESPN", "espn"), ("Disney+", "disney")]
        for i, (nome, key) in enumerate(canais):
            url = links.get(key)
            if url: cols[i].link_button(f"▶ {nome}", url, use_container_width=True)
            else: cols[i].button(f"⏸ {nome}", disabled=True, use_container_width=True, key=f"{key}_{idx}")

# --- ABA 5: FAVORITOS E ODDS ---
with aba5:
    st.header("Favoritos")
    df_probs = pd.DataFrame(dados['probabilidades']).sort_values(by="chance", ascending=False)
    cols = st.columns(3)
    for i, row in df_probs.head(3).iterrows():
        with cols[i]:
            st.markdown(f'<div class="metric-card"><h3>{row["time"]}</h3><p>Chance: {row["chance"]}%</p><h2 style="color:#00FF87!important;">Odd: {row.get("odd", "N/A")}</h2></div>', unsafe_allow_html=True)
    
    fig = px.bar(df_probs, x="chance", y="time", orientation='h', color="chance", color_continuous_scale=["#4B0082", "#FF004D", "#00FF87"])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)
