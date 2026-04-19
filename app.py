import streamlit as st
import pandas as pd
import requests
import json
from google.cloud import storage
from google.oauth2 import service_account
import feedparser
import plotly.express as px
from datetime import datetime

# LINHAS DE TESTE (Adicione estas)
if "gcp_service_account" in st.secrets:
    st.sidebar.success("✅ Segredos do Google encontrados!")
else:
    st.sidebar.error("❌ Segredos do Google NÃO encontrados nos Secrets!")

# ---------------------------------------------------------
# FUNÇÕES DE APOIO E INTEGRAÇÃO (GCP, API E DADOS)
# ---------------------------------------------------------

@st.cache_resource  # Alterado de cache_data para cache_resource
def autenticar_gcp():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("❌ Seção [gcp_service_account] não encontrada.")
            return None
        
        creds_info = dict(st.secrets["gcp_service_account"])
        
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        return storage.Client(credentials=credentials, project=creds_info.get("project_id"))
        
    except Exception as e:
        st.error(f"❌ Erro na autenticação: {str(e)}")
        return None
    
@st.cache_data(ttl=600)
def carregar_dados_cloud():
    client = autenticar_gcp()
    if client:
        try:
            # Tenta acessar o bucket e o arquivo
            bucket = client.get_bucket('hub-copa-dados-eduardo')
            blob = bucket.blob('dados_copa.json')
            
            # Verifica se o arquivo existe antes de baixar
            if not blob.exists():
                st.error("❌ O arquivo 'dados_copa.json' não existe no bucket 'hub-copa-dados-eduardo'.")
                return None
                
            conteudo = blob.download_as_text()
            return json.loads(conteudo)
        except Exception as e:
            st.error(f"❌ Erro ao acessar o Bucket: {str(e)}")
            return None
    return None

def buscar_dados_api():
    """Busca dados em tempo real da API-Sports."""
    try:
        if "API_KEY" not in st.secrets:
            return None
            
        api_key = st.secrets["API_KEY"]
        url = "https://v3.football.api-sports.io/fixtures?league=1&season=2026"
        
        headers = {
            'x-apisports-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('response'):
            return data['response']
    except Exception:
        pass
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
    except Exception:
        st.error("Erro ao carregar notícias.")

def calcular_classificacao(selecoes, jogos):
    """Processa placares e gera a tabela de pontos com nomes flexíveis."""
    tabela = {s['nome']: {'Grupo': s['grupo'], 'PTS': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0} for s in selecoes}
    
    for jogo in jogos:
        # Tenta pegar os nomes das chaves, caso variem entre 'time1' ou 'equipe1'
        t1 = jogo.get('time1') or jogo.get('equipe1') or jogo.get('mandante')
        t2 = jogo.get('time2') or jogo.get('equipe2') or jogo.get('visitante')
        p1 = jogo.get('placar1')
        p2 = jogo.get('placar2')
        
        # Só processa se encontrou os times e os placares não são nulos
        if t1 and t2 and p1 is not None and p2 is not None:
            tabela[t1]['J'] += 1; tabela[t2]['J'] += 1
            tabela[t1]['GP'] += p1; tabela[t1]['GC'] += p2
            tabela[t2]['GP'] += p2; tabela[t2]['GC'] += p1
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

def buscar_odds():
    import requests
    import pandas as pd
    import streamlit as st
    
    # 1. Busca a chave do seu "cofre" local (secrets.toml)
    api_key = st.secrets.get("ODDS_API_KEY")
    
    # 2. Lista expandida: Copa e Premier League (que sempre tem dados ativos)
    esportes = ["soccer_fifa_world_cup_winner", "soccer_brazil_campeonato"]
    
    for esporte in esportes:
        url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds/?apiKey={api_key}&regions=eu&markets=h2h"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"📡 Testando esporte: {esporte} | Status: {response.status_code}") # Log no terminal
            
            dados = response.json()
            
            if response.status_code == 200 and dados:
                odds_lista = []
                # Navegação robusta no JSON
                bookmakers = dados[0].get('bookmakers', [])
                if not bookmakers: continue
                
                markets = bookmakers[0].get('markets', [])
                if not markets: continue
                
                outcomes = markets[0].get('outcomes', [])
                
                for outcome in outcomes:
                    odds_lista.append({
                        'time': outcome['name'],
                        'chance': round(100 / outcome['price'], 2)
                    })
                
                if odds_lista:
                    df = pd.DataFrame(odds_lista).drop_duplicates(subset=['time'])
                    print(f"✅ Sucesso! Encontradas {len(df)} odds para {esporte}")
                    return df.sort_values('chance', ascending=False).head(15)
            else:
                print(f"⚠️ API retornou lista vazia ou erro para {esporte}")
                
        except Exception as e:
            print(f"💥 Erro na requisição para {esporte}: {e}")
            continue
            
    # Se chegar aqui, o backup indica que nada foi encontrado na API
    print("🚨 Usando dados de BACKUP (API falhou)")
    return pd.DataFrame([
        {'time': 'Brasil (Backup)', 'chance': 18.5}, 
        {'time': 'França (Backup)', 'chance': 16.0}
    ])
# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ---------------------------------------------------------
st.set_page_config(page_title="World Cup 2026 Hub", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    :root { --neon-green: #00FF87; --magenta: #FF004D; --purple: #4B0082; }
    .stApp { background-color: #0d0d0d; color: #ffffff; }
    h1, h2, h3 { color: #00FF87 !important; font-family: 'Arial Black', sans-serif; }
    .metric-card { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 5px solid #FF004D; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CARREGAMENTO PRINCIPAL
# ---------------------------------------------------------

dados_api = None
df_jogos = pd.DataFrame() 
df_classificacao = pd.DataFrame()

dados = carregar_dados_cloud()
dados_api = buscar_dados_api()

if not dados or 'selecoes' not in dados or 'jogos' not in dados:
    st.warning("⚠️ Os dados da Copa ainda não foram gerados ou estão no formato incorreto.")
    st.info("Verifique se o seu robô no Cloud Run já salvou o arquivo 'dados_copa.json' no Bucket.")
    st.stop() 

df_classificacao = calcular_classificacao(dados['selecoes'], dados['jogos'])
df_jogos = pd.DataFrame(dados['jogos'])

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://i.pinimg.com/1200x/2f/3b/60/2f3b607f2525dd613034cd05ef8f53bc.jpg", width=200)
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if dados_api:
        st.success("Conectado à API-Sports (Live)")
    st.caption("Desenvolvido por Eduardo Neves")

# ---------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------
st.title("🏆 Hub Oficial - Copa do Mundo 2026")

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📍 Visão Geral", "📊 Grupos", "📅 Tabela de Jogos", "📺 Onde Assistir", "📈 Favoritos e Odds"
])

with aba1:
    st.header("Contagem Regressiva e Notícias")
    col1, col2 = st.columns([1, 2])
    with col1:
        data_copa = datetime(2026, 6, 11)
        faltam = (data_copa - datetime.now()).days
        st.markdown(f'<div class="metric-card"><h1 style="color:#FF004D!important;font-size:4rem;margin:0;">{faltam}</h1><h3 style="margin:0;color:white!important;">Dias para a Copa</h3></div>', unsafe_allow_html=True)
    with col2:
        carregar_noticias()

with aba2:
    st.header("Classificação por Grupos")
    nomes_col = {'PTS':'Pts','J':'J','V':'V','E':'E','D':'D','GP':'GP','GC':'GC','SG':'SG'}
    for grupo in sorted(df_classificacao['Grupo'].unique()):
        st.subheader(f"Grupo {grupo}")
        df_g = df_classificacao[df_classificacao['Grupo'] == grupo].drop(columns=['Grupo']).rename(columns=nomes_col)
        st.dataframe(df_g, use_container_width=True)

with aba3:
    st.header("Tabela de Jogos")
    for _, row in df_jogos.iterrows():
        # Busca os valores com segurança usando .get()
        p1 = row.get('placar1')
        p2 = row.get('placar2')
        t1 = row.get('time1') or row.get('equipe1') or "Time A"
        t2 = row.get('time2') or row.get('equipe2') or "Time B"
        data_jogo = row.get('data') or "Data a definir"

            # Formata o placar apenas se houver números
    if pd.notnull(p1) and pd.notnull(p2):
        placar = f"{int(p1)} x {int(p2)}"
    else:
        placar = "vs"
                
    st.write(f"**{data_jogo}** | {t1} `{placar}` {t2}")
    st.divider()

with aba4:
        st.header("Onde Assistir")
        for _, row in df_jogos.iterrows():
            # Busca os nomes dos times com plano B (fallback)
            t1 = row.get('time1') or row.get('equipe1') or "Time A"
            t2 = row.get('time2') or row.get('equipe2') or "Time B"
            
            st.subheader(f"{t1} vs {t2}")
            
            # Busca o dicionário de links, se não houver, retorna vazio {}
            links = row.get("links", {})
            
            # Só cria as colunas se houver algum link para mostrar
            if links:
                cols = st.columns(3)
                if links.get("cazetv"): 
                    cols[0].link_button("▶️ CazéTV", links["cazetv"])
                if links.get("ge"): 
                    cols[1].link_button("▶️ GE", links["ge"])
                if links.get("sportv"): 
                    cols[2].link_button("▶️ SporTV", links["sportv"])
            else:
                st.info("Transmissões ainda não confirmadas para este jogo.")
            st.divider()

with aba5:
            st.header("Favoritos e Odds")
            
            resultado = buscar_odds() 
            
            if isinstance(resultado, tuple):
                df_odds, esporte_nome = resultado
            else:
                df_odds = resultado
                esporte_nome = "Copa Do Mundo"

            if df_odds is not None and not df_odds.empty:
                # --- DICIONÁRIO DE TRADUÇÃO ---
                traducoes = {
                    'Draw': 'Empate',
                    'France': 'França',
                    'Brazil': 'Brasil',
                    'South Africa': 'África do Sul',
                    'Mexico': 'México',
                    'Argentina': 'Argentina',
                    'Germany': 'Alemanha',
                    'England': 'Inglaterra',
                    'Spain': 'Espanha',
                    'Italy': 'Itália'
                }

                traducoes_esportes = {
                'soccer_fifa_world_cup_winner': 'Campeão da Copa do Mundo 2026',
                'soccer_brazil_campeonato': 'Brasileirão Série A'
                }
                
                df_odds['time'] = df_odds['time'].map(traducoes).fillna(df_odds['time'])

                st.write(f"Odds atualizadas em tempo real via **The Odds API**.")
                
                import plotly.express as px
                
                titulo_formatado = esporte_nome.replace('_', ' ').title()
                titulo_final = f"Chances de Vitória (%) - {titulo_formatado}"

                fig = px.bar(
                    df_odds, 
                    x='chance', 
                    y='time', 
                    orientation='h',
                    title=titulo_final,
                    color='chance',
                    text='chance',
                    color_continuous_scale='Viridis',
                    # MUDANÇA AQUI: De 'Chance de Título' para 'Chance de Vitória'
                    labels={'chance': 'Chance de Vitória (%)', 'time': 'Equipe'}
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%', 
                    textposition='outside',
                    cliponaxis=False
                )

                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    margin=dict(t=50, l=0, r=50, b=0),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Não foi possível carregar as odds no momento.")