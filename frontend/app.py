"""
Vyron System - Frontend
Interface Streamlit para consumir a API FastAPI
"""
import os
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Vyron System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CONFIGURAÇÃO DE AMBIENTE (Nuvem vs Local)
# ============================================
# Se a variável API_URL existir (na nuvem), usa ela.
# Se não existir (no seu PC), usa http://127.0.0.1:8000
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

print(f"🚀 Frontend conectando em: {API_BASE_URL}")

# ============================================
# FUNÇÃO CENTRALIZADA DE REQUISIÇÕES
# ============================================

def make_request(method: str, endpoint: str, **kwargs):
    """
    ============================================================
    FUNÇÃO CENTRALIZADA - TODAS AS REQUISIÇÕES API
    ============================================================
    
    CORREÇÃO DEFINITIVA DE TIMEOUT:
    - Timeout padrão: 60 segundos (ambiente de desenvolvimento lento)
    - Try/except robusto para capturar todos os erros
    - Retorna (dados, erro) de forma consistente
    - Logs amigáveis para o usuário
    
    Args:
        method: 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'
        endpoint: '/projects/', '/ai/chat', etc.
        **kwargs: params, json, data, files, etc.
        
    Returns:
        tuple: (response_data, error_message)
            - response_data: dict ou None
            - error_message: string ou None
            
    Exemplos:
        data, error = make_request('GET', '/projects/', params={'limit': 10})
        data, error = make_request('POST', '/ai/chat', json={'query': 'Hello'})
    """
    # Garante timeout padrão de 60s (CRÍTICO para ambiente lento)
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 60
    
    # Monta URL completa
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        # Executa a requisição
        if method.upper() == 'GET':
            response = requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, **kwargs)
        elif method.upper() == 'PUT':
            response = requests.put(url, **kwargs)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, **kwargs)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, **kwargs)
        else:
            return None, f"❌ Método HTTP inválido: {method}"
        
        # Verifica se foi bem-sucedido
        response.raise_for_status()
        
        # Retorna dados
        try:
            return response.json(), None
        except:
            # Se não for JSON, retorna o conteúdo bruto
            return response.content, None
            
    except requests.exceptions.Timeout:
        return None, "⏱️ Timeout: A API demorou mais de 60 segundos para responder. Tente novamente."
        
    except requests.exceptions.ConnectionError:
        return None, "❌ Erro de Conexão: API não está respondendo. Verifique se está rodando em localhost:8000"
        
    except requests.exceptions.HTTPError as e:
        # Extrai mensagem de erro da API
        try:
            error_detail = e.response.json().get("detail", "Erro desconhecido")
        except:
            error_detail = f"Status {e.response.status_code}"
        return None, f"❌ Erro HTTP: {error_detail}"
        
    except Exception as e:
        return None, f"❌ Erro inesperado: {type(e).__name__} - {str(e)}"


# ============================================
# SISTEMA DE AUTENTICAÇÃO
# ============================================

def check_authentication():
    """
    Verifica se o usuário está autenticado.
    Retorna True se autenticado, False caso contrário.
    """
    return st.session_state.get("authenticated", False)


def show_login_page():
    """
    Exibe a página de login
    """
    # Estilo customizado para a página de login
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background-color: #f0f2f6;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            font-size: 2rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Container centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-header">🔐 Vyron System</div>', unsafe_allow_html=True)
        st.markdown("### Login")
        
        # Formulário de login
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("🚀 Entrar", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("❌ Por favor, preencha usuário e senha")
                else:
                    # Faz requisição para o backend
                    with st.spinner("🔄 Autenticando..."):
                        data, error = make_request(
                            'POST', 
                            '/login', 
                            json={"username": username, "password": password}
                        )
                    
                    if data and not error:
                        # Login bem-sucedido
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = data.get("username")
                        st.session_state["user_role"] = data.get("user_role")
                        st.session_state["token"] = data.get("token")
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        # Falha no login
                        st.error(f"❌ {error}")
        
        st.markdown("---")
        st.info("""
            **Primeiro acesso?**
            
            Execute o script `create_admin.py` para criar seu usuário administrador.
            
            ```bash
            python create_admin.py
            ```
        """)


def logout():
    """
    Realiza logout limpando o session state
    """
    for key in ["authenticated", "username", "user_role", "token"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ============================================
# VERIFICAÇÃO DE AUTENTICAÇÃO
# ============================================

# Verifica se o usuário está autenticado
if not check_authentication():
    # Não autenticado - mostra apenas a tela de login
    show_login_page()
    st.stop()  # Para a execução aqui

# Se chegou aqui, o usuário está autenticado
# Continua com a aplicação normal

# ============================================
# ESTILO CUSTOMIZADO
# ============================================

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializa session state para o chat
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar para navegação
st.sidebar.title("🚀 Vyron System")
st.sidebar.markdown("---")

# Informações do usuário logado
st.sidebar.info(f"""
    👤 **Usuário:** {st.session_state.get('username', 'N/A')}  
    🎭 **Perfil:** {st.session_state.get('user_role', 'N/A').upper()}
""")

# Botão de logout
if st.sidebar.button("🚪 Sair", use_container_width=True):
    logout()

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard Financeiro", "📋 Gestão Visual", "🤖 Agency Brain", "✍️ Lançamentos Manuais"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
    **Vyron System v1.1 | Enterprise AI ERP**
    
    Sistema Inteligente de Gestão Empresarial
    
    🔗 API: localhost:8000
""")

# ============================================
# TESTE DE CONEXÃO COM API
# ============================================

api_health, api_error = make_request('GET', '/', timeout=5)
if api_health and not api_error:
    st.sidebar.success("✅ API Online")
else:
    if "Timeout" in str(api_error):
        st.sidebar.warning("⏱️ API demorou para responder")
    elif "Conexão" in str(api_error):
        st.sidebar.error("❌ API Offline - Inicie o uvicorn")
    else:
        st.sidebar.warning(f"⚠️ {api_error}")


# ============================================
# FUNÇÕES DE API (AGORA USANDO make_request)
# ============================================

def get_financial_dashboard(project_id: str):
    """Busca dados do dashboard financeiro"""
    return make_request('GET', f'/projects/{project_id}/financial-dashboard')


def get_projects_list(limit: int = 100):
    """Busca lista de projetos"""
    return make_request('GET', '/projects/', params={'limit': limit})


def send_chat_message(query: str, image: str = None):
    """Envia mensagem para o chat com IA"""
    payload = {"query": query}
    if image:
        payload["image"] = image
    
    data, error = make_request('POST', '/ai/chat', json=payload)
    if data and not error:
        return data.get("answer"), None
    return None, error


def create_interaction(client_id: str, content: str, interaction_type: str):
    """Cria uma nova interação"""
    data, error = make_request('POST', '/interactions/', json={
        "client_id": client_id,
        "content": content,
        "interaction_type": interaction_type
    })
    if data and not error:
        return True, None
    return False, error


# ============================================
# PÁGINA 1: DASHBOARD FINANCEIRO
# ============================================

if page == "📊 Dashboard Financeiro":
    st.markdown('<p class="main-header">📊 Dashboard Financeiro</p>', unsafe_allow_html=True)
    
    # ============================================
    # CARREGAMENTO INTELIGENTE DE PROJETOS
    # ============================================
    
    projects, error = get_projects_list(limit=100)
    
    if error:
        # Erro ao carregar projetos
        st.error(error)
        if "Timeout" in error:
            st.warning("⏱️ Backend Inicializando... Aguarde e recarregue a página.")
        elif "Conexão" in error:
            st.info("💡 Inicie o backend com: `uvicorn main:app --reload`")
        project_id = None
        data = None
        
    elif not projects or len(projects) == 0:
        # Nenhum projeto no banco
        st.warning("⚠️ Backend Inicializando ou Nenhum Projeto Encontrado")
        st.info("💡 **Como resolver:**")
        st.markdown("""
        1. Se a API acabou de iniciar, aguarde alguns segundos e recarregue
        2. Se não há projetos, vá em **✍️ Lançamentos Manuais** → **Novo Projeto**
        3. Ou use a aba **🤖 Agency Brain** e peça: "Crie um projeto de teste"
        """)
        project_id = None
        data = None
        
    else:
        # Projetos carregados com sucesso!
        st.success(f"✅ {len(projects)} projeto(s) encontrado(s)")
        
        # Criar dicionário: Nome exibido -> UUID
        project_options = {
            f"{p['name']} ({p['client_name']})": p['id'] 
            for p in projects
        }
        
        # Selectbox para escolher projeto
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_project_display = st.selectbox(
                "📁 Selecione o Projeto",
                options=list(project_options.keys()),
                help="Escolha o projeto para visualizar o dashboard financeiro"
            )
            
            # Pegar o UUID do projeto selecionado
            project_id = project_options[selected_project_display]
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            load_button = st.button("📈 Carregar Dados", type="primary")
        
        # Carregar dados automaticamente
        if load_button or selected_project_display:
            with st.spinner("🔄 Carregando dashboard financeiro..."):
                data, error = get_financial_dashboard(project_id)
    
    # Exibir dashboard se houver dados
    if 'data' in locals() and data and not error:
        st.success("✅ Dados carregados com sucesso!")
        
        # ============================================
        # CARD: RESUMO FINANCEIRO
        # ============================================
        with st.container(border=True):
            st.markdown("### 💰 Resumo Financeiro")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="💵 Receita Total",
                    value=f"R$ {data['total_revenue']:,.2f}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="💸 Despesas",
                    value=f"R$ {data['total_expense']:,.2f}",
                    delta=None
                )
            
            with col3:
                st.metric(
                    label="💎 Lucro Líquido",
                    value=f"R$ {data['net_profit']:,.2f}",
                    delta=f"{data['margin_percentage']}"
                )
            
            with col4:
                # Extrai percentual para exibir como indicador
                margin_value = float(data['margin_percentage'].replace('%', ''))
                margin_color = "🟢" if margin_value > 50 else "🟡" if margin_value > 20 else "🔴"
                st.metric(
                    label=f"{margin_color} Margem",
                    value=data['margin_percentage'],
                    delta=None
                )
            
            # Botão de exportação para PDF dentro do card
            st.markdown("")
            col_download1, col_download2, col_download3 = st.columns([1, 2, 1])
            with col_download2:
                # Usar make_request para download de PDF
                # A função retorna (response.content, None) para PDFs - já em bytes
                pdf_data, pdf_error = make_request('GET', f'/projects/{project_id}/export/pdf')
                
                if pdf_data and not pdf_error:
                    # CORREÇÃO: pdf_data já são bytes puros do backend, usar diretamente
                    st.download_button(
                        label="📄 Baixar Relatório em PDF",
                        data=pdf_data,  # Bytes puros, SEM .encode()
                        file_name=f"relatorio_projeto_{project_id[:8]}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.error(f"❌ {pdf_error}")
            
            # ============================================
            # CARD: GRÁFICO DE DISTRIBUIÇÃO
            # ============================================
            with st.container(border=True):
                st.markdown("### 📊 Distribuição Financeira")
                fig = go.Figure(data=[go.Pie(
                    labels=['Receitas', 'Despesas', 'Lucro'],
                    values=[data['total_revenue'], data['total_expense'], data['net_profit']],
                    hole=.3,
                    marker_colors=['#2ecc71', '#e74c3c', '#3498db']
                )])
                fig.update_layout(
                    title="Composição Financeira",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # ============================================
            # CARD: ANÁLISE
            # ============================================
            with st.container(border=True):
                st.markdown("### 📈 Análise")
                if margin_value > 70:
                    st.success("🎉 Excelente! Margem de lucro muito saudável.")
                elif margin_value > 40:
                    st.info("👍 Boa margem de lucro. Projeto rentável.")
                elif margin_value > 0:
                    st.warning("⚠️ Margem baixa. Considere otimizar custos.")
                else:
                    st.error("❌ Projeto no prejuízo. Ação urgente necessária!")
            
            # ============================================
            # CARD: KPIs DE MARKETING
            # ============================================
            with st.container(border=True):
                st.markdown("### 📈 KPIs de Marketing")
                
                kpis, kpis_error = make_request('GET', f'/projects/{project_id}/marketing-kpis')
                
                if kpis and not kpis_error:
                    if kpis['total_impressions'] > 0:
                        # Métricas de Marketing
                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                        
                        with col_m1:
                            st.metric(
                                label="👁️ Impressões",
                                value=f"{kpis['total_impressions']:,}",
                                delta=None
                            )
                        
                        with col_m2:
                            st.metric(
                                label="🖱️ Cliques",
                                value=f"{kpis['total_clicks']:,}",
                                delta=kpis['ctr']
                            )
                        
                        with col_m3:
                            st.metric(
                                label="🎯 Leads",
                                value=kpis['total_leads'],
                                delta=kpis['conversion_rate']
                            )
                        
                        with col_m4:
                            st.metric(
                                label="💰 Custo Total",
                                value=f"R$ {kpis['total_cost']:,.2f}",
                                delta=None
                            )
                        
                        # KPIs Calculados
                        st.markdown("#### 📊 Métricas de Performance")
                        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                        
                        with col_k1:
                            cpc_value = float(kpis['cpc'].replace('R$ ', '').replace(',', '.'))
                            st.metric(
                                label="CPC Médio",
                                value=f"R$ {cpc_value:.2f}",
                                help="Custo por Clique = Custo Total / Cliques"
                            )
                        
                        with col_k2:
                            cpl_value = float(kpis['cpl'])
                            st.metric(
                                label="CPA/CPL Médio",
                                value=f"R$ {cpl_value:.2f}",
                                help="Custo por Lead = Custo Total / Leads"
                            )
                        
                        with col_k3:
                            conv_rate = float(kpis['conversion_rate'].replace('%', ''))
                            color = "🟢" if conv_rate > 5 else "🟡" if conv_rate > 2 else "🔴"
                            st.metric(
                                label=f"{color} Taxa de Conversão",
                                value=kpis['conversion_rate'],
                                help="Leads / Cliques × 100"
                            )
                        
                        with col_k4:
                            st.metric(
                                label="✅ Conversões",
                                value=kpis['total_conversions'],
                                help="Total de conversões registradas"
                            )
                        
                        # ROI Metrics
                        st.markdown("#### 💎 Business Intelligence - ROI")
                        col_roi1, col_roi2 = st.columns(2)
                        
                        with col_roi1:
                            st.metric(
                                label="💵 Faturamento Est. (Marketing)",
                                value=f"R$ {kpis['estimated_revenue']:,.2f}",
                                delta="Baseado em conversões",
                                delta_color="normal",
                                help="Conversões × Preço do Produto"
                            )
                        
                        with col_roi2:
                            roi_value = float(kpis['roi'].replace('%', ''))
                            if roi_value > 100:
                                roi_color = "🟢"
                                roi_status = "Excelente!"
                            elif roi_value > 0:
                                roi_color = "🟡"
                                roi_status = "Positivo"
                            else:
                                roi_color = "🔴"
                                roi_status = "Negativo"
                            
                            st.metric(
                                label=f"{roi_color} ROI de Marketing",
                                value=kpis['roi'],
                                delta=roi_status,
                                delta_color="normal" if roi_value > 0 else "inverse",
                                help="(Faturamento - Custo) / Custo × 100"
                            )
                        
                        # Análise de Performance
                        if conv_rate > 5:
                            st.success("🎉 Excelente taxa de conversão!")
                        elif conv_rate > 2:
                            st.info("👍 Taxa de conversão saudável.")
                        else:
                            st.warning("⚠️ Taxa de conversão baixa. Considere otimizar as campanhas.")
                    else:
                        st.info("ℹ️ Nenhuma métrica de marketing registrada para este projeto ainda.")
                        st.markdown("💡 Use a aba **'✍️ Lançamentos Manuais'** para adicionar dados de marketing.")
                else:
                    st.warning(f"⚠️ {kpis_error}")
            
            # ============================================
            # CARD: TIMELINE DO PROJETO & CLIENTE
            # ============================================
            # CARD: TIMELINE DO PROJETO & CLIENTE
            # ============================================
            with st.container(border=True):
                st.markdown("### 📜 Timeline do Projeto & Cliente")
                
                # Buscar client_id do projeto
                project_data, _ = get_financial_dashboard(project_id)
                
                if project_data and 'client_id' in project_data:
                    client_id = project_data['client_id']
                    
                    timeline_data, timeline_error = make_request(
                        'GET',
                        f'/clients/{client_id}/interactions',
                        params={"limit": 10}
                    )
                    
                    if timeline_data and not timeline_error:
                        interactions = timeline_data.get('interactions', [])
                        
                        if interactions:
                            st.success(f"📊 Cliente: **{timeline_data.get('client_name', 'N/A')}** | {timeline_data.get('total', 0)} interações registradas")
                            
                            for interaction in interactions:
                                # Ícones por tipo
                                icons = {
                                    'meeting': '👥',
                                    'call': '📞',
                                    'email': '📧',
                                    'whatsapp': '💬',
                                    'system_log': '🤖'
                                }
                                icon = icons.get(interaction['type'], '📝')
                                
                                # Cor por sentimento
                                if interaction.get('is_positive'):
                                    sentiment_badge = "🟢 Positivo"
                                elif interaction.get('is_positive') == False:
                                    sentiment_badge = "🔴 Negativo"
                                else:
                                    sentiment_badge = "⚪ Neutro"
                                
                                # Urgência
                                urgency = interaction.get('urgency', 'low')
                                urgency_badge = "🔥 Alta" if urgency == 'high' else "⚡ Média" if urgency == 'medium' else "🌊 Baixa"
                                
                                # Data formatada
                                date_str = interaction['date'][:10] if interaction.get('date') else 'N/A'
                                
                                # Exibir interação
                                with st.expander(f"{icon} **{interaction['type'].upper()}** - {date_str}"):
                                    col_t1, col_t2 = st.columns([3, 1])
                                    
                                    with col_t1:
                                        st.markdown(f"**📝 Descrição:**")
                                        st.write(interaction.get('description', 'Sem descrição'))
                                    
                                    with col_t2:
                                        st.markdown(f"**Status:**")
                                        st.write(f"{sentiment_badge}")
                                        st.write(f"{urgency_badge}")
                        else:
                            st.info("ℹ️ Nenhuma interação registrada para este cliente ainda.")
                            st.markdown("💡 As interações são criadas automaticamente quando você adiciona projetos, despesas ou métricas.")
                    else:
                        st.warning(f"⚠️ {timeline_error}")
                else:
                    st.info("ℹ️ Não foi possível identificar o cliente deste projeto.")


# ============================================
# PÁGINA 2: AGENCY BRAIN (CHAT COM IA)
# ============================================

elif page == "🤖 Agency Brain":
    st.markdown('<p class="main-header">🤖 Vyron Brain</p>', unsafe_allow_html=True)
    st.markdown("**Assistente IA com memória das interações da empresa e visão multimodal**")
    
    # 1. Componente de Upload de Imagem (apenas nesta página)
    # ⚠️ OTIMIZAÇÃO: key única para permitir limpeza após envio (evita reenvio silencioso)
    uploaded_file = st.file_uploader(
        "📎 Anexar Recibo/Imagem (Opcional)", 
        type=["jpg", "png", "jpeg"],
        key="image_uploader"
    )
    image_b64 = None
    
    if uploaded_file:
        import base64
        # Mostra a imagem na tela
        st.image(uploaded_file, caption="Imagem anexada", width='stretch')
        # Converte para Base64 para enviar pra API
        image_b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        st.info("💡 Imagem será enviada apenas na próxima mensagem. Após envio, remova o arquivo para economizar tokens.")
    
    # 2. Container para o histórico do chat
    chat_container = st.container()
    
    with chat_container:
        # Exibe histórico
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # 3. Input do chat
    user_input = st.chat_input("Digite sua pergunta ou comando...")
    
    if user_input:
        # Adiciona mensagem do usuário ao histórico
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Exibe mensagem do usuário
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
        
        # Prepara payload com imagem se existir
        payload = {"query": user_input}
        if image_b64:
            payload["image"] = image_b64
        
        # Busca resposta da IA com visão multimodal
        with st.spinner("🤔 Analisando..." if not image_b64 else "👁️ Analisando imagem..."):
            answer, error = send_chat_message(user_input, image_b64)
        
        if error:
            # Exibe erro
            with chat_container:
                with st.chat_message("assistant"):
                    st.error(error)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error
            })
        else:
            # Exibe resposta da IA
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(answer)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })
            
            # ⚠️ OTIMIZAÇÃO: Limpa imagem após envio bem-sucedido para evitar reenvio acidental
            if image_b64:
                st.success("✅ Imagem processada! Remova o arquivo acima para não reenviar nas próximas mensagens.")
        
        # Rerun para atualizar a interface
        st.rerun()
    
    # Botão para limpar histórico
    if st.session_state.chat_history:
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Exemplos de perguntas
    if not st.session_state.chat_history:
        st.markdown("---")
        st.markdown("**💡 Experimente perguntar:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - "Quais foram os principais problemas reportados?"
            - "Resuma as últimas reuniões"
            - "O que o cliente disse sobre prazos?"
            """)
        
        with col2:
            st.markdown("""
            - "Houve alguma reclamação recente?"
            - "Quais são os projetos ativos?"
            - "Me fale sobre o cliente X"
            """)


# ============================================
# PÁGINA 2: GESTÃO VISUAL (KANBAN)
# ============================================

elif page == "📋 Gestão Visual":
    st.markdown('<p class="main-header">📋 Gestão Visual - Kanban de Projetos</p>', unsafe_allow_html=True)
    st.markdown("**Arraste projetos entre as fases do fluxo de trabalho**")
    
    # Função auxiliar para atualizar o status de um projeto
    def update_project_status(project_id, new_status):
        """Atualiza o status de um projeto via API"""
        with st.spinner(f"🔄 Movendo projeto para {new_status}..."):
            data, error = make_request(
                'PATCH',
                f'/projects/{project_id}/status',
                json={'status': new_status}
            )
        
        if data and not error:
            st.success(f"✅ Projeto movido para {new_status}!")
            import time
            time.sleep(1)  # Pausa para o usuário ver a mensagem
            st.rerun()
        else:
            st.error(f"❌ Erro ao atualizar: {error}")
            st.stop()  # Para a execução para mostrar o erro
    
    # Buscar todos os projetos
    with st.spinner("🔄 Carregando projetos..."):
        projects, error = get_projects_list(limit=100)
    
    if error:
        st.error(error)
        if "Conexão" in error:
            st.info("💡 Inicie o backend com: `uvicorn main:app --reload`")
    elif not projects or len(projects) == 0:
        st.warning("⚠️ Nenhum projeto encontrado no sistema")
        st.info("💡 Crie seu primeiro projeto em **✍️ Lançamentos Manuais** → **Novo Projeto**")
    else:
        st.success(f"✅ {len(projects)} projeto(s) encontrado(s)")
        
        # Agrupar projetos por status
        projetos_por_fase = {
            'Negociação': [],
            'Em Produção': [],
            'Concluído': []
        }
        
        for project in projects:
            # Garante que o projeto tem um status válido
            status = project.get('status', 'Negociação')
            if status not in projetos_por_fase:
                # Se o status não for um dos 3, coloca em Negociação por padrão
                status = 'Negociação'
            
            projetos_por_fase[status].append(project)
        
        # Criar 3 colunas para o Kanban
        col_negociacao, col_producao, col_concluido = st.columns(3)
        
        # ============================================
        # COLUNA 1: NEGOCIAÇÃO 🟧
        # ============================================
        with col_negociacao:
            st.markdown("### 🟧 Negociação")
            st.markdown(f"**{len(projetos_por_fase['Negociação'])} projeto(s)**")
            st.markdown("---")
            
            if projetos_por_fase['Negociação']:
                for project in projetos_por_fase['Negociação']:
                    with st.container(border=True):
                        st.markdown(f"**📋 {project['name']}**")
                        st.caption(f"👤 Cliente: {project.get('client_name', 'N/A')}")
                        
                        # Formatar valor como moeda brasileira
                        valor = project.get('value', 0)
                        if valor:
                            valor_float = float(valor) if isinstance(valor, str) else valor
                            st.markdown(f"💰 **R$ {valor_float:,.2f}**")
                        
                        # Botão para mover para Produção
                        if st.button(
                            "▶️ Iniciar Produção",
                            key=f"start_{project['id']}",
                            use_container_width=True,
                            type="primary"
                        ):
                            update_project_status(project['id'], 'Em Produção')
            else:
                st.info("Nenhum projeto nesta fase")
        
        # ============================================
        # COLUNA 2: EM PRODUÇÃO 🟦
        # ============================================
        with col_producao:
            st.markdown("### 🟦 Em Produção")
            st.markdown(f"**{len(projetos_por_fase['Em Produção'])} projeto(s)**")
            st.markdown("---")
            
            if projetos_por_fase['Em Produção']:
                for project in projetos_por_fase['Em Produção']:
                    with st.container(border=True):
                        st.markdown(f"**📋 {project['name']}**")
                        st.caption(f"👤 Cliente: {project.get('client_name', 'N/A')}")
                        
                        # Formatar valor como moeda brasileira
                        valor = project.get('value', 0)
                        if valor:
                            valor_float = float(valor) if isinstance(valor, str) else valor
                            st.markdown(f"💰 **R$ {valor_float:,.2f}**")
                        
                        # Botões de ação
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button(
                                "⬅️ Voltar",
                                key=f"back_{project['id']}",
                                use_container_width=True
                            ):
                                update_project_status(project['id'], 'Negociação')
                        
                        with col_btn2:
                            if st.button(
                                "✅ Concluir",
                                key=f"complete_{project['id']}",
                                use_container_width=True,
                                type="primary"
                            ):
                                update_project_status(project['id'], 'Concluído')
            else:
                st.info("Nenhum projeto nesta fase")
        
        # ============================================
        # COLUNA 3: CONCLUÍDO 🟩
        # ============================================
        with col_concluido:
            st.markdown("### 🟩 Concluído")
            st.markdown(f"**{len(projetos_por_fase['Concluído'])} projeto(s)**")
            st.markdown("---")
            
            if projetos_por_fase['Concluído']:
                for project in projetos_por_fase['Concluído']:
                    with st.container(border=True):
                        st.markdown(f"**📋 {project['name']}**")
                        st.caption(f"👤 Cliente: {project.get('client_name', 'N/A')}")
                        
                        # Formatar valor como moeda brasileira
                        valor = project.get('value', 0)
                        if valor:
                            valor_float = float(valor) if isinstance(valor, str) else valor
                            st.markdown(f"💰 **R$ {valor_float:,.2f}**")
                        
                        # Mostrar badge de concluído
                        st.success("✅ Finalizado")
                        
                        # Botão para reabrir (caso necessário)
                        if st.button(
                            "🔄 Reabrir",
                            key=f"reopen_{project['id']}",
                            use_container_width=True
                        ):
                            update_project_status(project['id'], 'Em Produção')
            else:
                st.info("Nenhum projeto nesta fase")
        
        # Estatísticas resumidas
        st.markdown("---")
        st.markdown("### 📊 Estatísticas")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric(
                label="Total de Projetos",
                value=len(projects)
            )
        
        with col_stat2:
            st.metric(
                label="Em Negociação",
                value=len(projetos_por_fase['Negociação']),
                delta=None
            )
        
        with col_stat3:
            st.metric(
                label="Em Produção",
                value=len(projetos_por_fase['Em Produção']),
                delta=None
            )
        
        with col_stat4:
            st.metric(
                label="Concluídos",
                value=len(projetos_por_fase['Concluído']),
                delta=None
            )


# ============================================
# PÁGINA 3: LANÇAMENTOS MANUAIS
# ============================================

elif page == "✍️ Lançamentos Manuais":
    st.markdown('<p class="main-header">✍️ Lançamentos Manuais</p>', unsafe_allow_html=True)
    st.markdown("**Registre dados diretamente no sistema - memória RAG garantida**")
    
    # Tabs para organizar os formulários
    tab1, tab2, tab3 = st.tabs(["💼 Novo Projeto", "💸 Nova Despesa", "📊 Métricas de Marketing"])
    
    # ============================================
    # TAB 1: NOVO PROJETO
    # ============================================
    with tab1:
        st.markdown("### Criar Novo Projeto")
        st.info("💡 O cliente será criado automaticamente se não existir no sistema.")
        
        with st.form("form_novo_projeto"):
            col1, col2 = st.columns(2)
            
            with col1:
                projeto_nome = st.text_input("Nome do Projeto *", placeholder="Ex: Campanha Black Friday 2026")
                cliente_nome = st.text_input("Cliente *", placeholder="Ex: Loja ABC")
                projeto_orcamento = st.number_input("Orçamento (R$) *", min_value=0.0, step=100.0, value=5000.0)
            
            with col2:
                produto_preco = st.number_input(
                    "💰 Preço do Produto (Ticket Médio) *",
                    min_value=0.0,
                    step=10.0,
                    value=0.0,
                    help="Valor médio de venda do produto/serviço. Usado para calcular ROI de Marketing."
                )
                projeto_descricao = st.text_area("Descrição (Opcional)", placeholder="Detalhes sobre o projeto...")
            
            submitted_projeto = st.form_submit_button("💼 Criar Projeto", type="primary")
            
            if submitted_projeto:
                if not projeto_nome or not cliente_nome or projeto_orcamento <= 0:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                else:
                    with st.spinner("Criando projeto..."):
                        result, error = make_request(
                            'POST',
                            '/manual/projects',
                            params={
                                "project_name": projeto_nome,
                                "client_name": cliente_nome,
                                "budget": projeto_orcamento,
                                "product_price": produto_preco,
                                "description": projeto_descricao
                            }
                        )
                        
                        if result and not error:
                            st.success(f"✅ {result['message']}")
                            st.balloons()
                            st.info(f"**ID do Projeto:** `{result['project_id']}`")
                        else:
                            st.error(error)
    
    # ============================================
    # TAB 2: NOVA DESPESA
    # ============================================
    with tab2:
        st.markdown("### Registrar Nova Despesa")
        
        # Busca projetos para o selectbox
        projetos, projetos_error = get_projects_list(limit=100)
        
        if projetos and not projetos_error:
            projetos_dict = {f"{p['name']} ({p['client_name']})": p['id'] for p in projetos}
        else:
            projetos_dict = {}
            if projetos_error:
                st.warning(f"⚠️ {projetos_error}")
        
        with st.form("form_nova_despesa"):
            col1, col2 = st.columns(2)
            
            with col1:
                if projetos_dict:
                    projeto_selecionado = st.selectbox("Projeto", options=list(projetos_dict.keys()))
                    projeto_id_despesa = projetos_dict[projeto_selecionado]
                else:
                    st.warning("Nenhum projeto disponível. Crie um projeto primeiro.")
                    projeto_id_despesa = None
                
                despesa_descricao = st.text_input("Descrição *", placeholder="Ex: Anúncios Google Ads")
                despesa_valor = st.number_input("Valor (R$) *", min_value=0.01, step=10.0, value=500.0)
            
            with col2:
                despesa_categoria = st.selectbox(
                    "Categoria *",
                    ["Publicidade", "Freelancer", "Software", "Infraestrutura", "Operacional", "Outros"]
                )
                despesa_data = st.date_input("Data de Vencimento *")
                despesa_status = st.selectbox("Status", ["pending", "paid"], index=0)
            
            submitted_despesa = st.form_submit_button("💸 Lançar Despesa", type="primary")
            
            if submitted_despesa:
                if not projeto_id_despesa or not despesa_descricao:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                else:
                    with st.spinner("Registrando despesa..."):
                        result, error = make_request(
                            'POST',
                            '/manual/expenses',
                            json={
                                "project_id": projeto_id_despesa,
                                "category": despesa_categoria,
                                "description": despesa_descricao,
                                "amount": despesa_valor,
                                "due_date": despesa_data.isoformat(),
                                "status": despesa_status
                            }
                        )
                        
                        if result and not error:
                            st.success(f"✅ {result['message']}")
                            st.balloons()
                        else:
                            st.error(error)
    
    # ============================================
    # TAB 3: MÉTRICAS DE MARKETING
    # ============================================
    with tab3:
        st.markdown("### Registrar Métricas de Marketing")
        
        # Busca projetos
        projetos_mkt, projetos_mkt_error = get_projects_list(limit=100)
        
        if projetos_mkt and not projetos_mkt_error:
            projetos_dict_mkt = {f"{p['name']} ({p['client_name']})": p['id'] for p in projetos_mkt}
        else:
            projetos_dict_mkt = {}
            if projetos_mkt_error:
                st.warning(f"⚠️ {projetos_mkt_error}")
        
        with st.form("form_metricas_marketing"):
            col1, col2 = st.columns(2)
            
            with col1:
                if projetos_dict_mkt:
                    projeto_selecionado_mkt = st.selectbox("Projeto *", options=list(projetos_dict_mkt.keys()), key="mkt_proj")
                    projeto_id_mkt = projetos_dict_mkt[projeto_selecionado_mkt]
                else:
                    st.warning("Nenhum projeto disponível.")
                    projeto_id_mkt = None
                
                metrica_data = st.date_input("Data das Métricas *", key="mkt_date")
                metrica_impressoes = st.number_input("Impressões", min_value=0, step=100, value=1000)
                metrica_cliques = st.number_input("Cliques", min_value=0, step=10, value=50)
            
            with col2:
                metrica_leads = st.number_input("Leads Gerados", min_value=0, step=1, value=5)
                metrica_conversoes = st.number_input("Conversões", min_value=0, step=1, value=0)
                metrica_custo = st.number_input("Custo da Campanha (R$)", min_value=0.0, step=50.0, value=0.0)
                metrica_plataforma = st.selectbox("Plataforma", ["Google Ads", "Meta Ads", "TikTok Ads", "LinkedIn Ads", "Outro"])
            
            submitted_metrica = st.form_submit_button("📊 Salvar Métricas", type="primary")
            
            if submitted_metrica:
                if not projeto_id_mkt:
                    st.error("❌ Selecione um projeto!")
                else:
                    with st.spinner("Salvando métricas..."):
                        from datetime import datetime
                        result, error = make_request(
                            'POST',
                            '/manual/marketing-metrics',
                            json={
                                "project_id": projeto_id_mkt,
                                "date": datetime.combine(metrica_data, datetime.min.time()).isoformat(),
                                "impressions": metrica_impressoes,
                                "clicks": metrica_cliques,
                                "leads": metrica_leads,
                                "conversions": metrica_conversoes,
                                "cost": metrica_custo if metrica_custo > 0 else None,
                                "platform": metrica_plataforma
                            }
                        )
                        
                        if result and not error:
                            st.success(f"✅ {result['message']}")
                            if 'ctr' in result:
                                st.info(f"📈 **KPIs Calculados:** CTR: {result['ctr']} | Taxa de Conversão: {result['conversion_rate']}")
                            st.balloons()
                        else:
                            st.error(error)
    
    # Informativo
    st.markdown("---")
    st.info("""
    **ℹ️ Como funciona:**
    
    - **Memória RAG**: Todos os lançamentos manuais criam registros no sistema de memória da IA
    - **Integração Total**: A IA consegue consultar e responder sobre dados inseridos manualmente
    - **Auditoria**: Todos os registros ficam com timestamp e podem ser rastreados
    """)


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🚀 <strong>Vyron System</strong> | Powered by FastAPI + Streamlit + OpenAI</p>
    <p><small>v1.1.0 | 2026</small></p>
</div>
""", unsafe_allow_html=True)
