# 🏆 Hub Oficial - Copa do Mundo 2026

Este é um Web App interativo desenvolvido para centralizar todas as informações da Copa do Mundo de 2026. O projeto foca em oferecer uma experiência fluida para o usuário, com dados em tempo real sobre grupos, classificação e guias de transmissão.

## 🚀 Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Framework Web:** [Streamlit](https://streamlit.io/)
* **Manipulação de Dados:** Pandas
* **Estrutura de Dados:** JSON (Arquitetura desacoplada para atualizações dinâmicas)

## 🛠️ Funcionalidades
* **Dashboard Geral:** Contagem regressiva e notícias integradas.
* **Grupos e Classificação:** Tabelas automáticas com cálculo de pontos, vitórias e saldo de gols.
* **Guia Multi-Source:** Links diretos para transmissões oficiais (CazéTV, Globo, SporTV, ESPN e Disney+).
* **Modo Escuro (Dark Mode):** Interface otimizada para visualização técnica e moderna.

## 📂 Arquitetura do Projeto
O diferencial deste projeto é a separação entre lógica e dados:
* `app.py`: Contém toda a lógica de interface e processamento.
* `dados_copa.json`: Banco de dados flexível que permite atualizar resultados e links sem mexer no código principal.
* `requirements.txt`: Gerenciamento profissional de dependências.

## 🔧 Como rodar o projeto localmente
1. Clone este repositório.
2. Certifique-se de ter o Python instalado.
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
