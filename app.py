import feedparser
import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
import plotly.express as px

# --- FUNÇÃO DE NOTÍCIAS (CORRIGIDA) ---
def carregar_noticias():
    # RSS do GE focado em Copa do Mundo / Futebol Internacional
    url_rss = "https://ge.globo.com/servico/semantico/editorias/video/esporte/futebol/futebol-internacional/feed.rss"
    try:
        feed = feedparser.parse(url_rss)
        if feed.entries:
            for entry in feed.entries[:3]: # Mostra as 3 notícias mais recentes
                with st.expander(f"📌 {entry.title}"):
                    st.write(entry.summary[:200] + "...")
                    st.markdown(f"[Leia a matéria completa]({entry.link})")
        else:
            st.info("Nenhuma atualização nova no momento. Volte em breve!")
    except Exception:
        st.error("Erro ao carregar notícias dinâmicas.")

# ---------------------------------------------------------
# Configuração da Página e Cores (Design Copa 2026)
# ---------------------------------------------------------
st.set_page_config(page_title="World Cup 2026 Hub", page_icon="🏆", layout="wide")

# CSS customizado para estética da Copa 2026
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
# Engenharia de Dados: Ingestão e Processamento
# ---------------------------------------------------------
DATA_URL = "dados_copa.json" 

@st.cache_data(ttl=600)
def carregar_dados(url):
    try:
        if url.startswith("http"):
            response = requests.get(url)
            return response.json()
        else:
            with open(url, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def calcular_classificacao(selecoes, jogos):
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
                tabela[t1]['PTS'] += 3
                tabela[t1]['V'] += 1
                tabela[t2]['D'] += 1
            elif p2 > p1:
                tabela[t2]['PTS'] += 3
                tabela[t2]['V'] += 1
                tabela[t1]['D'] += 1
            else:
                tabela[t1]['PTS'] += 1
                tabela[t2]['PTS'] += 1
                tabela[t1]['E'] += 1
                tabela[t2]['E'] += 1
    for t in tabela.values():
        t['SG'] = t['GP'] - t['GC']
    df = pd.DataFrame.from_dict(tabela, orient='index').reset_index()
    df.rename(columns={'index': 'Seleção'}, inplace=True)
    df = df.sort_values(by=['Grupo', 'PTS', 'SG', 'GP'], ascending=[True, False, False, False])
    return df

# ---------------------------------------------------------
# Sidebar: Controles de Aplicação
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://i.pinimg.com/1200x/2f/3b/60/2f3b607f2525dd613034cd05ef8f53bc.jpg", width=200)
    st.markdown("### Controle de Dados")
    if st.button("🔄 Atualizar Dados Agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("Desenvolvido por Eduardo Neves | Segurança da Informação")

# Carregamento de Dados
dados = carregar_dados(DATA_URL)
if not dados:
    st.stop()

df_classificacao = calcular_classificacao(dados['selecoes'], dados['jogos'])
df_jogos = pd.DataFrame(dados['jogos'])

# ---------------------------------------------------------
# Interface Principal: Módulos / Abas
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
        st.markdown(f"""
            <div class="metric-card">
                <h1 style='color: #FF004D !important; font-size: 4rem; margin: 0;'>{faltam}</h1>
                <h3 style='margin: 0; color: white !important;'>Dias para a Copa</h3>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.subheader("Últimas Atualizações")
        carregar_noticias()
        
# --- ABA 2: GRUPOS E CLASSIFICAÇÃO ---
with aba2:
    st.header("Classificação por Grupos")
    grupos = sorted(df_classificacao['Grupo'].unique())
    
    # Mapeamento para nomes completos das colunas
    nomes_completos = {
        'Seleção': 'Seleção',
        'PTS': 'Pontos',
        'J': 'Jogos',
        'V': 'Vitórias',
        'E': 'Empates',
        'D': 'Derrotas',
        'GP': 'Gols Pró',
        'GC': 'Gols Contra',
        'SG': 'Saldo de Gols'
    }

    for grupo in grupos:
        st.subheader(f"Grupo {grupo}")
        # Filtra os dados do grupo atual e renomeia
        df_g = df_classificacao[df_classificacao['Grupo'] == grupo].drop(columns=['Grupo'])
        df_g = df_g.rename(columns=nomes_completos)
        
        # Reseta o index para começar de 1
        df_g.index = range(1, len(df_g) + 1)
        
        # Configuração avançada: Centraliza o conteúdo E o cabeçalho
        # Usamos st.column_config.TextColumn para a Seleção e NumberColumn para os pontos
        config_centralizada = {}
        for col in df_g.columns:
            if col == 'Seleção':
                config_centralizada[col] = st.column_config.TextColumn(label=col, alignment="center")
            else:
                config_centralizada[col] = st.column_config.NumberColumn(label=col, alignment="center")
        
        # Exibe a tabela
        st.dataframe(
            df_g, 
            use_container_width=True, 
            column_config=config_centralizada
        )
        st.divider()
        
# --- ABA 3: TABELA DE JOGOS ---
with aba3:
    st.header("Tabela Completa de Jogos")
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        filtro_grupo = st.multiselect("Filtrar por Grupo:", options=sorted(df_jogos['grupo'].dropna().unique()))
    with col_filtro2:
        filtro_selecao = st.text_input("Buscar Seleção:")
    df_filtrado = df_jogos.copy()
    if filtro_grupo:
        df_filtrado = df_filtrado[df_filtrado['grupo'].isin(filtro_grupo)]
    if filtro_selecao:
        mask = df_filtrado['time1'].str.contains(filtro_selecao, case=False) | df_filtrado['time2'].str.contains(filtro_selecao, case=False)
        df_filtrado = df_filtrado[mask]
    for _, row in df_filtrado.iterrows():
        placar_str = f"{int(row['placar1'])} x {int(row['placar2'])}" if pd.notnull(row['placar1']) else "vs"
        st.markdown(f"**{row['data']}** | {row['fase']} (Grupo {row['grupo']})")
        st.markdown(f"### 🇺🇳 {row['time1']} `{placar_str}` {row['time2']} 🇺🇳")
        st.divider()

# --- ABA 4: ONDE ASSISTIR ---
def renderizar_botao_link(nome, url, key):
    if url and str(url).strip() != "":
        st.link_button(f"▶ {nome}", url, use_container_width=True)
    else:
        st.button(f"⏸ {nome} (Em breve)", key=key, disabled=True, use_container_width=True)

with aba4:
    st.header("Transmissões Ao Vivo (Multi-Source)")
    for idx, row in df_jogos.iterrows():
        st.subheader(f"{row['time1']} vs {row['time2']}")
        st.caption(f"Data: {row['data']}")
        links = row.get("links", {})
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: renderizar_botao_link("CazéTV", links.get("cazetv"), f"caze_{idx}")
        with c2: renderizar_botao_link("GE", links.get("ge"), f"ge_{idx}")
        with c3: renderizar_botao_link("SporTV", links.get("sportv"), f"sportv_{idx}")
        with c4: renderizar_botao_link("ESPN", links.get("espn"), f"espn_{idx}")
        with c5: renderizar_botao_link("Disney+", links.get("disney"), f"disney_{idx}")
        st.divider()

# --- ABA 5: FAVORITOS E ODDS ---
with aba5:
    st.header("Probabilidade de Título e Odds Reais")
    
    # Transformando os dados em DataFrame
    df_probs = pd.DataFrame(dados['probabilidades'])
    
    # Ordenando pelos favoritos (maior chance)
    df_probs = df_probs.sort_values(by="chance", ascending=False)

    # Criando métricas em colunas para os 3 principais favoritos
    top3 = df_probs.head(3)
    cols = st.columns(3)
    for i, (index, row) in enumerate(top3.iterrows()):
        with cols[i]:
            st.markdown(f"""
                <div class="metric-card">
                    <h3 style='margin:0;'>{row['time']}</h3>
                    <p style='margin:0; font-size: 0.9rem;'>Chance: {row['chance']}%</p>
                    <h2 style='color: #00FF87 !important; margin:0;'>Odd: {row.get('odd', 'N/A')}</h2>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Gráfico elegante com as Odds aparecendo no passar do mouse
    fig = px.bar(
        df_probs, x="chance", y="time", orientation='h', 
        title="Chances de Título (Probabilidade Computada)",
        labels={"chance": "Chances (%)", "time": "Seleção"},
        color="chance", 
        hover_data={"odd": True}, # Mostra a Odd quando passa o mouse
        color_continuous_scale=["#4B0082", "#FF004D", "#00FF87"]
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)
