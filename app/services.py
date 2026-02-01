"""
Services - Lógica de Negócio e Integrações
Integração com APIs externas (OpenAI, etc.)
"""
import os
import json
import io
from typing import List
from datetime import date, datetime
from decimal import Decimal
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import de FPDF2 para geração de PDFs
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
    print(f"✅ FPDF2 carregado com sucesso!")
except ImportError as e:
    FPDF_AVAILABLE = False
    import sys
    print(f"⚠️ FPDF2 não instalado. Python: {sys.executable}")
    print(f"⚠️ Erro: {e}")

# Import dos models será feito dinamicamente para evitar circular import
# Mas declaramos aqui para type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import models

# Inicializa cliente OpenAI (apenas se a chave estiver configurada)
_api_key = os.getenv("OPENAI_API_KEY")
if _api_key:
    client = AsyncOpenAI(api_key=_api_key)
else:
    client = None


async def generate_embedding(text: str) -> List[float]:
    """
    Gera um embedding vetorial usando OpenAI text-embedding-3-small.
    
    Modelo: text-embedding-3-small
    - Custo-benefício ideal
    - Dimensão: 1536
    - Mais barato que ada-002
    
    Args:
        text: Texto para gerar o embedding
        
    Returns:
        Lista com 1536 floats representando o embedding vetorial
        
    Fallback:
        Se a API falhar ou não houver chave configurada, retorna vetor de zeros
    """
    try:
        # Verifica se o cliente OpenAI está disponível
        if not client:
            print("⚠️ OpenAI API key não configurada. Usando vetor de zeros.")
            return [0.0] * 1536
        
        # Chama a API da OpenAI
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        # Retorna o vetor de embedding
        return response.data[0].embedding
        
    except Exception as e:
        # Log do erro no console
        print(f"⚠️ Erro ao gerar embedding com OpenAI: {e}")
        print("📝 Usando vetor de zeros como fallback")
        
        # Retorna vetor de zeros (1536 dimensões) para não quebrar a aplicação
        return [0.0] * 1536


# ============================================
# FUNCTION CALLING - DEFINIÇÃO DAS TOOLS
# ============================================

# Definição das ferramentas disponíveis para a IA
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Cria um novo projeto no sistema. SEMPRE use esta função quando o usuário mencionar criar, adicionar, registrar ou aprovar um novo projeto, mesmo que o cliente não exista ainda no banco. A função criará o cliente automaticamente se necessário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Nome do projeto a ser criado (ex: 'Mars Landing', 'Website Redesign')"
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Nome do cliente para quem o projeto será criado (ex: 'SpaceX', 'Tesla'). Não precisa existir no banco."
                    },
                    "budget": {
                        "type": "number",
                        "description": "Orçamento ou valor do projeto em reais/dólares (número sem formatação)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Descrição opcional do projeto"
                    }
                },
                "required": ["project_name", "client_name", "budget"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "Lista projetos existentes no sistema. Use esta função para consultar projetos, verificar IDs, status, valores, clientes ou confirmar se um projeto já foi criado. Essencial para responder perguntas sobre projetos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Termo de busca opcional para filtrar projetos por nome do projeto ou nome do cliente"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de projetos a retornar (padrão: 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Registra uma nova despesa vinculada a um projeto específico. SEMPRE use esta função quando o usuário mencionar gastos, despesas, custos ou pagamentos relacionados a um projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Nome do projeto ao qual a despesa está vinculada (ex: 'Mars Landing', 'Website Redesign')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Descrição da despesa - o que foi comprado ou pago (ex: 'Licença Adobe Creative Cloud', 'Freelancer design')"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Valor da despesa em reais/dólares (número sem formatação)"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Operational", "Marketing", "Software", "Team"],
                        "description": "Categoria da despesa. Operational=operacional geral, Marketing=anúncios/mídia, Software=ferramentas/licenças, Team=equipe/freelancers"
                    }
                },
                "required": ["project_name", "description", "amount"]
            }
        }
    }
]


async def _execute_create_project(
    db: Session,
    project_name: str,
    client_name: str,
    budget: float,
    description: str = None,
    product_price: float = 0.0
) -> str:
    """
    Executa a criação de um projeto no banco de dados COM INTEGRIDADE TOTAL.
    
    Realiza 3 operações atômicas:
    1. Cria o projeto (ou busca cliente existente e cria)
    2. Lança registro financeiro automático (revenues)
    3. Gera memória RAG (interactions) para busca futura pela IA
    
    Busca o cliente pelo nome (case-insensitive) ou cria um novo se não existir.
    Cria o projeto vinculado ao cliente.
    
    Args:
        db: Sessão do banco de dados
        project_name: Nome do projeto
        client_name: Nome do cliente
        budget: Orçamento do projeto
        description: Descrição do projeto (opcional)
        product_price: Preço do produto/serviço (ticket médio) para cálculo de ROI
        
    Returns:
        String JSON com o resultado da operação
    """
    try:
        # Import tardio para evitar circular dependency
        from app import models
        
        # ============================================
        # OPERAÇÃO 1: CRIAR/BUSCAR CLIENTE E PROJETO
        # ============================================
        
        # 1.1 Busca cliente pelo nome (case-insensitive)
        client = db.query(models.Client)\
            .filter(func.lower(models.Client.name) == client_name.lower())\
            .first()
        
        # 1.2 Se cliente não existe, cria um novo
        if not client:
            # Gera um email temporário se não tiver
            temp_email = f"{client_name.lower().replace(' ', '.')}@temp.agency"
            
            client = models.Client(
                name=client_name,
                email=temp_email,
                status='client'  # Status direto de cliente
            )
            db.add(client)
            db.flush()  # Garante que o ID seja gerado
            
            client_status = "novo cliente criado"
        else:
            client_status = "cliente existente"
        
        # 1.3 Cria o projeto
        project = models.Project(
            client_id=client.id,
            name=project_name,
            type='one_off',  # Default: projeto pontual
            category='general',  # Categoria geral
            contract_value=Decimal(str(budget)),
            product_price=Decimal(str(product_price)),  # Preço do produto para cálculo de ROI
            start_date=date.today(),
            status='planning'  # Status inicial
        )
        
        db.add(project)
        db.flush()  # Garante que o ID do projeto seja gerado ANTES de usar
        
        # ============================================
        # OPERAÇÃO 2: LANÇAR FINANCEIRO AUTOMÁTICO
        # ============================================
        
        revenue = models.Revenue(
            project_id=project.id,
            client_id=client.id,
            description=f"Orçamento Inicial do Projeto {project_name}",
            amount=Decimal(str(budget)),
            due_date=date.today(),
            status='pending'  # Receita pendente de pagamento
        )
        
        db.add(revenue)
        db.flush()
        
        # ============================================
        # OPERAÇÃO 3: GERAR MEMÓRIA RAG (EMBEDDINGS)
        # ============================================
        
        # 3.1 Monta o conteúdo para embedding
        rag_content = (
            f"SISTEMA: Novo projeto criado. "
            f"Cliente: {client_name}. "
            f"Projeto: {project_name}. "
            f"Orçamento: R$ {budget:,.2f}. "
            f"Status: Em andamento."
        )
        
        # 3.2 Gera o embedding vetorial (RAG)
        content_embedding = await generate_embedding(rag_content)
        
        # 3.3 Cria o registro de interação com embedding
        interaction = models.Interaction(
            client_id=client.id,
            type='system_log',
            subject=f"Projeto Criado: {project_name}",
            content=rag_content,
            content_embedding=content_embedding,  # Vetor para RAG
            interaction_date=datetime.utcnow(),
            is_positive=True,
            requires_followup=False,
            urgency_level='low'
        )
        
        db.add(interaction)
        
        # ============================================
        # COMMIT ATÔMICO DE TODAS AS OPERAÇÕES
        # ============================================
        
        db.commit()
        
        # Refresh para obter dados atualizados
        db.refresh(project)
        db.refresh(revenue)
        db.refresh(interaction)
        
        # ============================================
        # RETORNA RESULTADO COMPLETO
        # ============================================
        
        result = {
            "status": "success",
            "project_id": str(project.id),
            "project_name": project.name,
            "client_id": str(client.id),
            "client_name": client.name,
            "client_status": client_status,
            "budget": float(budget),
            "revenue_id": str(revenue.id),
            "interaction_id": str(interaction.id),
            "message": f"✅ Projeto '{project_name}' criado com sucesso para {client_name}! Financeiro e memória RAG registrados."
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        # Rollback em caso de erro (garante atomicidade)
        db.rollback()
        
        error_result = {
            "status": "error",
            "message": f"❌ Erro ao criar projeto: {str(e)}"
        }
        
        return json.dumps(error_result, ensure_ascii=False)


async def _execute_add_expense(
    db: Session,
    project_name: str,
    description: str,
    amount: float,
    category: str = "Operational"
) -> str:
    """
    Registra uma despesa vinculada a um projeto COM INTEGRIDADE TOTAL.
    
    Realiza 2 operações atômicas:
    1. Cria o registro financeiro (expenses) vinculado ao projeto
    2. Gera memória RAG (interactions) para busca futura pela IA
    
    Args:
        db: Sessão do banco de dados
        project_name: Nome do projeto
        description: Descrição da despesa
        amount: Valor da despesa
        category: Categoria da despesa (Operational, Marketing, Software, Team)
        
    Returns:
        String JSON com o resultado da operação
    """
    try:
        # Import tardio para evitar circular dependency
        from app import models
        
        # ============================================
        # OPERAÇÃO 1: BUSCAR PROJETO
        # ============================================
        
        # Busca projeto pelo nome (case-insensitive)
        project = db.query(models.Project)\
            .filter(func.lower(models.Project.name) == project_name.lower())\
            .first()
        
        if not project:
            error_result = {
                "status": "error",
                "message": f"❌ Projeto '{project_name}' não encontrado. Verifique o nome e tente novamente."
            }
            return json.dumps(error_result, ensure_ascii=False)
        
        # ============================================
        # OPERAÇÃO 2: REGISTRAR DESPESA FINANCEIRA
        # ============================================
        
        expense = models.Expense(
            project_id=project.id,
            category=category,
            description=description,
            amount=Decimal(str(amount)),
            due_date=date.today(),
            status='paid',  # Despesa já paga
            is_project_related=True
        )
        
        db.add(expense)
        db.flush()  # Garante que o ID seja gerado
        
        # ============================================
        # OPERAÇÃO 3: GERAR MEMÓRIA RAG (EMBEDDINGS)
        # ============================================
        
        # 3.1 Monta o conteúdo para embedding
        rag_content = (
            f"SISTEMA: Nova despesa registrada. "
            f"Projeto: {project_name}. "
            f"Valor: R$ {amount:,.2f}. "
            f"Descrição: {description}. "
            f"Categoria: {category}."
        )
        
        # 3.2 Gera o embedding vetorial (RAG)
        content_embedding = await generate_embedding(rag_content)
        
        # 3.3 Cria o registro de interação com embedding
        interaction = models.Interaction(
            client_id=project.client_id,
            type='system_log',
            subject=f"Despesa Registrada: {project_name}",
            content=rag_content,
            content_embedding=content_embedding,  # Vetor para RAG
            interaction_date=datetime.utcnow(),
            is_positive=False,  # Despesa é saída de caixa
            requires_followup=False,
            urgency_level='low'
        )
        
        db.add(interaction)
        
        # ============================================
        # COMMIT ATÔMICO DE TODAS AS OPERAÇÕES
        # ============================================
        
        db.commit()
        
        # Refresh para obter dados atualizados
        db.refresh(expense)
        db.refresh(interaction)
        
        # ============================================
        # RETORNA RESULTADO COMPLETO
        # ============================================
        
        result = {
            "status": "success",
            "expense_id": str(expense.id),
            "project_id": str(project.id),
            "project_name": project.name,
            "description": description,
            "amount": float(amount),
            "category": category,
            "interaction_id": str(interaction.id),
            "message": f"✅ Despesa de R$ {amount:,.2f} registrada no projeto '{project_name}'! Financeiro e memória RAG atualizados."
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        # Rollback em caso de erro (garante atomicidade)
        db.rollback()
        
        error_result = {
            "status": "error",
            "message": f"❌ Erro ao registrar despesa: {str(e)}"
        }
        
        return json.dumps(error_result, ensure_ascii=False)


async def _execute_add_marketing_stats(
    db: Session,
    project_name: str,
    date: datetime,
    impressions: int,
    clicks: int,
    leads: int,
    conversions: int = 0,
    cost: float = None,
    platform: str = None,
    source: str = "manual"
) -> str:
    """
    Registra métricas de marketing para um projeto COM MEMÓRIA RAG.
    
    Realiza 2 operações atômicas:
    1. Cria o registro de métrica de marketing
    2. Gera memória RAG (interactions) para busca futura pela IA
    
    Args:
        db: Sessão do banco de dados
        project_name: Nome do projeto
        date: Data das métricas
        impressions: Número de impressões
        clicks: Número de cliques
        leads: Número de leads gerados
        conversions: Número de conversões (opcional)
        cost: Custo da campanha (opcional)
        platform: Plataforma (Google Ads, Meta Ads, etc.)
        source: Origem do registro ('manual' ou 'ai')
        
    Returns:
        String JSON com o resultado da operação
    """
    try:
        from app import models
        from decimal import Decimal
        
        # ============================================
        # OPERAÇÃO 1: BUSCAR PROJETO
        # ============================================
        
        project = db.query(models.Project)\
            .filter(func.lower(models.Project.name) == project_name.lower())\
            .first()
        
        if not project:
            return json.dumps({
                "status": "error",
                "message": f"❌ Projeto '{project_name}' não encontrado. Use list_projects para ver projetos disponíveis."
            }, ensure_ascii=False)
        
        # ============================================
        # OPERAÇÃO 2: CRIAR MÉTRICA DE MARKETING
        # ============================================
        
        metric = models.MarketingMetric(
            project_id=project.id,
            date=date,
            impressions=impressions,
            clicks=clicks,
            leads=leads,
            conversions=conversions,
            cost=Decimal(str(cost)) if cost else None,
            platform=platform
        )
        
        db.add(metric)
        db.flush()  # Garante que o ID seja gerado
        
        # ============================================
        # OPERAÇÃO 3: GERAR MEMÓRIA RAG (SYSTEM LOG)
        # ============================================
        
        # Calcula KPIs para o log
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        conversion_rate = (leads / clicks * 100) if clicks > 0 else 0
        cpc = (cost / clicks) if cost and clicks > 0 else 0
        cpl = (cost / leads) if cost and leads > 0 else 0
        
        # Monta a mensagem de log
        log_parts = [
            f"SISTEMA: Métricas de marketing registradas {'' if source == 'manual' else 'automaticamente '}para o projeto '{project.name}'.",
            f"Data: {date.strftime('%d/%m/%Y')}",
            f"Performance: {impressions:,} impressões, {clicks:,} cliques, {leads} leads"
        ]
        
        if conversions > 0:
            log_parts.append(f", {conversions} conversões")
        
        if platform:
            log_parts.append(f"Plataforma: {platform}")
        
        if cost:
            log_parts.append(f"Custo: R$ {cost:,.2f}")
            log_parts.append(f"KPIs: CTR {ctr:.2f}%, CPC R$ {cpc:.2f}, CPL R$ {cpl:.2f}")
        
        log_content = "\n".join(log_parts)
        
        # Gera embedding para RAG
        embedding = await generate_embedding(log_content)
        
        # Cria interação como log do sistema
        interaction = models.Interaction(
            client_id=project.client_id,
            type="system_log",
            content=log_content,
            content_embedding=embedding,
            interaction_date=datetime.now()
        )
        
        db.add(interaction)
        db.commit()
        
        # ============================================
        # RETORNA RESULTADO
        # ============================================
        
        result = {
            "status": "success",
            "metric_id": str(metric.id),
            "project_id": str(project.id),
            "project_name": project.name,
            "impressions": impressions,
            "clicks": clicks,
            "leads": leads,
            "conversions": conversions,
            "ctr": f"{ctr:.2f}%",
            "conversion_rate": f"{conversion_rate:.2f}%",
            "interaction_id": str(interaction.id),
            "message": f"✅ Métricas de marketing registradas para '{project_name}'! {impressions:,} impressões, {clicks:,} cliques, {leads} leads."
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        db.rollback()
        
        error_result = {
            "status": "error",
            "message": f"❌ Erro ao registrar métricas: {str(e)}"
        }
        
        return json.dumps(error_result, ensure_ascii=False)


def _execute_list_projects(
    db: Session,
    search_term: str = None,
    limit: int = 10
) -> str:
    """
    Lista projetos do sistema com opção de busca.
    
    Args:
        db: Sessão do banco de dados
        search_term: Termo opcional para filtrar por nome do projeto ou cliente
        limit: Número máximo de resultados (padrão: 10)
        
    Returns:
        String JSON com a lista de projetos
    """
    try:
        # Import tardio para evitar circular dependency
        from app import models
        
        # Inicia query base com join para pegar dados do cliente
        query = db.query(models.Project, models.Client)\
            .join(models.Client, models.Project.client_id == models.Client.id)
        
        # Aplica filtro de busca se fornecido
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (models.Project.name.ilike(search_pattern)) |
                (models.Client.name.ilike(search_pattern))
            )
        
        # Ordena por data de criação (mais recentes primeiro) e limita
        query = query.order_by(models.Project.created_at.desc()).limit(limit)
        
        results = query.all()
        
        # Formata os resultados
        projects_list = []
        for project, client in results:
            projects_list.append({
                "id": str(project.id),
                "name": project.name,
                "client_name": client.name,
                "client_id": str(client.id),
                "status": project.status,
                "budget": float(project.contract_value),
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "type": project.type
            })
        
        result = {
            "status": "success",
            "count": len(projects_list),
            "projects": projects_list,
            "message": f"✅ Encontrados {len(projects_list)} projeto(s)"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"❌ Erro ao listar projetos: {str(e)}"
        }
        
        return json.dumps(error_result, ensure_ascii=False)


async def generate_answer(query: str, context: str, db: Session = None, image_data: str = None) -> str:
    """
    Gera uma resposta usando GPT com contexto RAG e Function Calling.
    Suporta entrada multimodal (texto + imagem).
    
    Utiliza gpt-4o-mini para responder perguntas e executar ações no sistema.
    Suporta Function Calling para operações como criar projetos e registrar despesas.
    
    Args:
        query: Pergunta do usuário
        context: Contexto relevante recuperado do banco
        db: Sessão do banco de dados (necessária para Function Calling)
        image_data: Imagem em Base64 (opcional para visão multimodal)
        
    Returns:
        Resposta gerada pela IA
        
    Fallback:
        Se a API falhar, retorna mensagem de erro amigável
    """
    try:
        # Verifica se o cliente OpenAI está disponível
        if not client:
            return "⚠️ OpenAI API não configurada. Por favor, configure a chave OPENAI_API_KEY no arquivo .env"
        
        # Monta as mensagens iniciais
        messages = [
            {
                "role": "system",
                "content": """Você é o assistente IA do Agency OS com capacidade de executar ações no sistema.

CAPACIDADES DISPONÍVEIS:
1. Criar projetos: Use create_project quando solicitado
2. Listar/Consultar projetos: Use list_projects para buscar, verificar ou listar projetos
3. Registrar despesas: Use add_expense para registrar gastos/custos em projetos

IMPORTANTE: 
- Para criar projetos: SEMPRE use create_project
- Para consultar/listar projetos: SEMPRE use list_projects
- Para registrar despesas: SEMPRE use add_expense
- Não diga que não tem acesso aos dados - você TEM através das ferramentas!

Exemplos de uso:
- list_projects: "Quais projetos temos?", "Liste projetos do cliente X"
- add_expense: "Registre uma despesa de R$ 500 em Software no projeto Mars Landing", "Comprei licença Adobe por R$ 200 para o projeto X"

Categorias de despesas:
- Operational: Despesas operacionais gerais
- Marketing: Anúncios, mídia paga
- Software: Ferramentas, licenças, SaaS
- Team: Freelancers, colaboradores externos

VISÃO MULTIMODAL:
- Se o usuário enviar uma imagem (ex: recibo, nota fiscal), analise-a e extraia informações relevantes
- Use os dados extraídos da imagem para preencher os parâmetros das ferramentas automaticamente
- Exemplo: Recibo mostrando "Adobe Creative Cloud - R$ 500" → use add_expense com esses dados

Use o contexto fornecido apenas para responder perguntas sobre interações. Para dados de projetos e despesas, use as ferramentas!"""
            }
        ]
        
        # Constrói a mensagem do usuário (multimodal se houver imagem)
        if image_data:
            # Modo multimodal: texto + imagem (otimizado para low detail = 85 tokens)
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Contexto:\n{context}\n\nSolicitação: {query}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                            "detail": "low"  # 85 tokens por imagem (vs 765+ no auto)
                        }
                    }
                ]
            }
        else:
            # Modo texto simples (economiza tokens)
            user_message = {
                "role": "user",
                "content": f"Contexto:\n{context}\n\nSolicitação: {query}"
            }
        
        messages.append(user_message)
        
        # Primeira chamada: verifica se precisa executar alguma tool
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # ⚠️ TRAVA: Sempre usar gpt-4o-mini (custo otimizado)
            messages=messages,
            tools=tools,  # Disponibiliza as ferramentas para a IA
            tool_choice="auto",  # IA decide quando usar
            temperature=0.7,
            max_tokens=500  # Limite de tokens de saída para controlar custos
        )
        
        response_message = response.choices[0].message
        
        # Verifica se a IA quer executar alguma função
        if response_message.tool_calls:
            # Adiciona a resposta da IA ao histórico
            messages.append(response_message)
            
            # Executa cada tool call solicitada
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🤖 IA solicitou execução: {function_name}")
                print(f"📋 Argumentos: {function_args}")
                
                # Executa a função correspondente
                if function_name == "create_project":
                    if db is None:
                        function_response = json.dumps({
                            "status": "error",
                            "message": "Sessão do banco de dados não disponível"
                        })
                    else:
                        function_response = await _execute_create_project(
                            db=db,
                            project_name=function_args.get("project_name"),
                            client_name=function_args.get("client_name"),
                            budget=function_args.get("budget"),
                            description=function_args.get("description")
                        )
                
                elif function_name == "list_projects":
                    if db is None:
                        function_response = json.dumps({
                            "status": "error",
                            "message": "Sessão do banco de dados não disponível"
                        })
                    else:
                        function_response = _execute_list_projects(
                            db=db,
                            search_term=function_args.get("search_term"),
                            limit=function_args.get("limit", 10)
                        )
                
                elif function_name == "add_expense":
                    if db is None:
                        function_response = json.dumps({
                            "status": "error",
                            "message": "Sessão do banco de dados não disponível"
                        })
                    else:
                        function_response = await _execute_add_expense(
                            db=db,
                            project_name=function_args.get("project_name"),
                            description=function_args.get("description"),
                            amount=function_args.get("amount"),
                            category=function_args.get("category", "Operational")
                        )
                
                else:
                    function_response = json.dumps({
                        "status": "error",
                        "message": f"Função {function_name} não implementada"
                    })
                
                print(f"✅ Resultado: {function_response}")
                
                # Adiciona o resultado da função ao histórico
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response
                })
            
            # Segunda chamada: IA gera resposta final para o usuário
            final_response = await client.chat.completions.create(
                model="gpt-4o-mini",  # ⚠️ TRAVA: Sempre usar gpt-4o-mini (custo otimizado)
                messages=messages,
                temperature=0.7,
                max_tokens=500  # Limite de tokens de saída para controlar custos
            )
            
            return final_response.choices[0].message.content
        
        else:
            # Não há tool calls, retorna resposta normal
            return response_message.content
        
    except Exception as e:
        # Log do erro no console
        print(f"⚠️ Erro ao gerar resposta com OpenAI: {e}")
        
        # Retorna mensagem de erro amigável
        return "Desculpe, não consegui processar sua pergunta no momento. Por favor, tente novamente."


# ============================================
# GERAÇÃO DE RELATÓRIOS PDF COM FPDF2
# ============================================

class PDF(FPDF):
    """
    Classe customizada para geração de PDFs profissionais.
    
    Design Moderno:
    - Cabeçalho com fundo azul escuro e título branco
    - Tabelas com headers cinza claro e negrito
    - Rodapé com linha separadora elegante
    """
    
    def header(self):
        """Cabeçalho do PDF - aparece em todas as páginas."""
        # Retângulo de fundo azul escuro no topo
        self.set_fill_color(20, 30, 70)  # Azul escuro corporativo
        self.rect(0, 0, 210, 20, 'F')  # Retângulo preenchido (largura A4 = 210mm)
        
        # Logo/Título em branco sobre o fundo azul
        self.set_font('Arial', 'B', 18)
        self.set_text_color(255, 255, 255)  # Branco
        self.set_y(7)  # Posiciona verticalmente no centro do retângulo
        self.cell(0, 10, 'VYRON SYSTEM REPORT', 0, 1, 'C')
        
        # Espaço após o header
        self.ln(5)
    
    def footer(self):
        """Rodapé do PDF - aparece em todas as páginas."""
        # Linha fina cinza separadora acima do rodapé
        self.set_y(-20)
        self.set_draw_color(180, 180, 180)  # Cinza médio
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        
        # Posiciona o texto do rodapé
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        
        # Número da página
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')


def generate_project_pdf(db: Session, project_id: str) -> bytes:
    """
    ============================================================
    GERAÇÃO DE PDF - FPDF2 PURO (SEM REPORTLAB)
    ============================================================
    Gera relatório executivo financeiro de um projeto.
    
    CORREÇÃO DEFINITIVA:
    - Usa FPDF2 exclusivamente
    - Classe PDF customizada com header/footer
    - Encoding Latin-1 para evitar erros de caracteres
    - Tratamento robusto de erros
    
    Args:
        db: Sessão do banco de dados
        project_id: UUID do projeto
        
    Returns:
        bytes: Conteúdo do PDF gerado
        
    Raises:
        ValueError: Se o projeto não for encontrado
        RuntimeError: Se FPDF2 não estiver instalado
    """
    if not FPDF_AVAILABLE:
        raise RuntimeError("❌ FPDF2 não está instalado. Execute: pip install fpdf2")
    
    from app import models
    
    # ============================================
    # 1. BUSCAR DADOS DO PROJETO
    # ============================================
    try:
        # Busca o projeto
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            raise ValueError(f"❌ Projeto com ID {project_id} não encontrado")
        
        # Busca receitas e despesas
        revenues = db.query(models.Revenue).filter(models.Revenue.project_id == project_id).all()
        expenses = db.query(models.Expense).filter(models.Expense.project_id == project_id).all()
        
        # Cálculos financeiros
        total_revenue = sum([r.amount for r in revenues]) if revenues else Decimal('0')
        total_expense = sum([e.amount for e in expenses]) if expenses else Decimal('0')
        net_profit = total_revenue - total_expense
        margin_percentage = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        # ROI calculation se houver product_price
        roi_percentage = Decimal('0')
        if project.product_price and project.product_price > 0:
            estimated_revenue = project.product_price * Decimal('10')  # Estimativa conservadora
            roi_percentage = ((estimated_revenue - total_expense) / total_expense * 100) if total_expense > 0 else Decimal('0')
        
    except Exception as e:
        raise ValueError(f"❌ Erro ao buscar dados do projeto: {str(e)}")
    
    # ============================================
    # 2. CRIAR PDF COM CLASSE CUSTOMIZADA
    # ============================================
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ============================================
    # 3. DASHBOARD ESTÁTICO - DESTAQUES FINANCEIROS
    # ============================================
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(20, 30, 70)
    pdf.cell(0, 10, 'DESTAQUES FINANCEIROS', 0, 1, 'C')
    pdf.ln(3)
    
    # Desenha 3 retângulos lado a lado com os valores principais
    # Largura disponível: 190mm (210mm - 20mm margens)
    # Cada card: ~60mm de largura com 3mm de espaço entre eles
    card_width = 60
    card_height = 25
    spacing = 5
    start_x = 15  # Centralizar melhor
    start_y = pdf.get_y()
    
    # CARD 1: RECEITA
    pdf.set_fill_color(230, 245, 230)  # Verde muito suave
    pdf.rect(start_x, start_y, card_width, card_height, 'F')
    pdf.set_xy(start_x, start_y + 5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(card_width, 5, 'RECEITA TOTAL', 0, 1, 'C')
    pdf.set_xy(start_x, start_y + 12)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(card_width, 8, f"R$ {float(total_revenue):,.0f}", 0, 1, 'C')
    
    # CARD 2: DESPESAS
    pdf.set_fill_color(255, 240, 240)  # Vermelho muito suave
    pdf.rect(start_x + card_width + spacing, start_y, card_width, card_height, 'F')
    pdf.set_xy(start_x + card_width + spacing, start_y + 5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(card_width, 5, 'DESPESAS TOTAIS', 0, 1, 'C')
    pdf.set_xy(start_x + card_width + spacing, start_y + 12)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(card_width, 8, f"R$ {float(total_expense):,.0f}", 0, 1, 'C')
    
    # CARD 3: LUCRO
    pdf.set_fill_color(240, 245, 255)  # Azul muito suave
    pdf.rect(start_x + (card_width + spacing) * 2, start_y, card_width, card_height, 'F')
    pdf.set_xy(start_x + (card_width + spacing) * 2, start_y + 5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(31, 119, 180)
    pdf.cell(card_width, 5, 'LUCRO LIQUIDO', 0, 1, 'C')
    pdf.set_xy(start_x + (card_width + spacing) * 2, start_y + 12)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(card_width, 8, f"R$ {float(net_profit):,.0f}", 0, 1, 'C')
    
    # Move para depois dos cards
    pdf.set_xy(10, start_y + card_height + 10)
    pdf.ln(5)
    
    # ============================================
    # 4. SEÇÃO: INFORMAÇÕES DO PROJETO
    # ============================================
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(31, 119, 180)
    pdf.cell(0, 10, 'INFORMACOES DO PROJETO', 0, 1, 'L')
    pdf.ln(2)
    
    # Informações básicas - Design moderno
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 220, 220)  # Cinza claro consistente
    pdf.set_text_color(0, 0, 0)
    
    info_data = [
        ('Nome do Projeto:', project.name),
        ('Cliente:', project.client.name if project.client else "N/A"),
        ('Data de Inicio:', project.start_date.strftime('%d/%m/%Y') if project.start_date else "N/A"),
        ('Status:', project.status.upper()),
        ('Tipo:', project.type if project.type else "N/A"),
    ]
    
    for label, value in info_data:
        pdf.cell(60, 8, label, 1, 0, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(130, 8, str(value)[:45], 1, 1, 'L')  # Limita a 45 caracteres
        pdf.set_font('Arial', 'B', 10)
    
    pdf.ln(8)
    
    # ============================================
    # 5. SEÇÃO: RESUMO FINANCEIRO
    # ============================================
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, 'RESUMO FINANCEIRO', 0, 1, 'L')
    pdf.ln(2)
    
    # Cabeçalho da tabela financeira - Design moderno
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(220, 220, 220)  # Cinza claro corporativo
    pdf.set_text_color(0, 0, 0)  # Texto preto em negrito
    pdf.cell(100, 9, 'Metrica', 1, 0, 'L', True)
    pdf.cell(90, 9, 'Valor', 1, 1, 'R', True)
    
    # Dados financeiros
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    financial_data = [
        ('Receita Total', f"R$ {float(total_revenue):,.2f}"),
        ('Despesas Totais', f"R$ {float(total_expense):,.2f}"),
        ('Lucro Liquido', f"R$ {float(net_profit):,.2f}"),
        ('Margem de Lucro', f"{float(margin_percentage):.1f}%"),
    ]
    
    # Adiciona ROI se disponível
    if roi_percentage != 0:
        financial_data.append(('ROI Estimado', f"{float(roi_percentage):.1f}%"))
    
    for i, (metric, value) in enumerate(financial_data):
        # Destaca lucro líquido
        if 'Lucro' in metric:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(200, 230, 200)
        else:
            pdf.set_font('Arial', '', 10)
            pdf.set_fill_color(250, 250, 250) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(100, 8, metric, 1, 0, 'L', True)
        pdf.cell(90, 8, value, 1, 1, 'R', True)
    
    pdf.ln(8)
    
    # ============================================
    # 6. SEÇÃO: TABELA DE DESPESAS
    # ============================================
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 10, 'DETALHAMENTO DE DESPESAS', 0, 1, 'L')
    pdf.ln(2)
    
    if expenses and len(expenses) > 0:
        # Cabeçalho da tabela - Design moderno
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(220, 220, 220)  # Cinza claro corporativo
        pdf.set_text_color(0, 0, 0)  # Texto preto em negrito
        
        pdf.cell(22, 7, 'Data', 1, 0, 'C', True)
        pdf.cell(90, 7, 'Descricao', 1, 0, 'C', True)
        pdf.cell(40, 7, 'Categoria', 1, 0, 'C', True)
        pdf.cell(38, 7, 'Valor (R$)', 1, 1, 'C', True)
        
        # Linhas de despesas
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        for i, expense in enumerate(expenses):
            # Alterna cores
            if i % 2 == 0:
                pdf.set_fill_color(248, 248, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            
            # Formata dados
            date_str = expense.due_date.strftime('%d/%m/%y') if expense.due_date else "N/A"
            # Trata caracteres especiais - Remove acentos problemáticos
            desc = expense.description.encode('latin-1', 'ignore').decode('latin-1')
            desc = desc[:35] + "..." if len(desc) > 35 else desc
            category = (expense.category or "Outros")[:15]
            amount = f"{float(expense.amount):,.2f}"
            
            pdf.cell(22, 6, date_str, 1, 0, 'C', True)
            pdf.cell(90, 6, desc, 1, 0, 'L', True)
            pdf.cell(40, 6, category, 1, 0, 'C', True)
            pdf.cell(38, 6, amount, 1, 1, 'R', True)
        
        # Total de despesas
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(255, 200, 200)
        pdf.cell(152, 7, 'TOTAL DE DESPESAS:', 1, 0, 'R', True)
        pdf.cell(38, 7, f"{float(total_expense):,.2f}", 1, 1, 'R', True)
        
    else:
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 8, 'Nenhuma despesa registrada para este projeto.', 0, 1, 'C')
    
    pdf.ln(10)
    
    # ============================================
    # 7. RODAPÉ FINAL
    # ============================================
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y as %H:%M')} | Vyron System v1.1", 0, 1, 'C')
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(0, 5, 'Documento gerado automaticamente - Dados sujeitos a auditoria', 0, 1, 'C')
    
    # ============================================
    # 8. RETORNAR BYTES DO PDF
    # ============================================
    try:
        # Output em modo String para retornar bytes
        pdf_output = pdf.output(dest='S')
        
        # Garante que sempre retorna bytes puros (não bytearray ou string)
        if isinstance(pdf_output, str):
            return pdf_output.encode('latin-1')
        elif isinstance(pdf_output, bytearray):
            return bytes(pdf_output)
        else:
            return pdf_output
            
    except Exception as e:
        raise RuntimeError(f"❌ Erro ao gerar PDF: {str(e)}")


def get_client_interactions(db: Session, client_id: str, limit: int = 10) -> List[dict]:
    """
    Busca as últimas interações de um cliente para exibição na timeline.
    
    Args:
        db: Sessão do banco de dados
        client_id: UUID do cliente
        limit: Número máximo de interações a retornar (padrão: 10)
        
    Returns:
        Lista de dicionários com: date, type, description, sentiment
    """
    from app import models
    
    # Busca interações ordenadas pela mais recente
    interactions = db.query(models.Interaction)\
        .filter(models.Interaction.client_id == client_id)\
        .order_by(models.Interaction.interaction_date.desc())\
        .limit(limit)\
        .all()
    
    # Formata para o frontend
    result = []
    for interaction in interactions:
        result.append({
            "date": interaction.interaction_date.isoformat(),
            "type": interaction.type,
            "description": interaction.subject or interaction.content[:100],  # Usa subject ou primeiros 100 chars
            "sentiment": float(interaction.sentiment_score) if interaction.sentiment_score else None,
            "is_positive": interaction.is_positive,
            "urgency": interaction.urgency_level
        })
    
    return result


# Função futura para análise de sentimento (exemplo):
"""
async def analyze_sentiment(text: str) -> float:
    '''
    Analisa o sentimento de um texto usando OpenAI.
    Retorna score entre -1.0 (negativo) e 1.0 (positivo).
    '''
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze sentiment. Return only a number between -1.0 and 1.0"},
                {"role": "user", "content": text}
            ]
        )
        return float(response.choices[0].message.content)
    except:
        return 0.0  # Neutro como fallback
"""

