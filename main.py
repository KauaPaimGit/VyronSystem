from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.database import get_db, engine
from app import models, schemas
from app.services import (
    generate_embedding, 
    generate_answer, 
    generate_project_pdf,
    _execute_create_project,
    _execute_add_expense,
    _execute_add_marketing_stats
)
from app.auth import authenticate_user

# ============================================
# CRIA AS TABELAS NO BANCO DE DADOS (Se não existirem)
# ============================================
print("🔄 Criando tabelas no banco de dados...")
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas/verificadas com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao criar tabelas: {e}")
    raise  # Re-lança o erro para falhar visualmente no deploy

app = FastAPI(
    title="Vyron System - Core API",
    description="Enterprise AI ERP - Sistema Inteligente de Gestão Empresarial",
    version="1.1.0"
)

# Configuração CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "running", "service": "Vyron System API"}


# ============================================
# ROTAS: AUTENTICAÇÃO
# ============================================

class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Schema para resposta de login"""
    message: str
    user_role: str
    username: str
    token: str


@app.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de autenticação - Login
    
    Recebe username e password, verifica as credenciais e retorna informações do usuário.
    
    Args:
        credentials: Objeto com username e password
        db: Sessão do banco de dados
        
    Returns:
        LoginResponse: Informações do usuário autenticado
        
    Raises:
        HTTPException 401: Se credenciais inválidas
    """
    # Autentica o usuário
    user = authenticate_user(db, credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas. Verifique seu usuário e senha."
        )
    
    # Retorna sucesso com informações do usuário
    # NOTA: Em produção, use JWT real (PyJWT) ao invés de "fake-jwt-token"
    return LoginResponse(
        message="Login realizado com sucesso",
        user_role=user.role,
        username=user.username,
        token=f"fake-jwt-token-{user.id}"  # Em produção, use JWT real
    )


@app.get("/db-test")
def test_database_connection(db: Session = Depends(get_db)):
    """
    Testa a conexão com o banco e verifica se o pgvector está ativo.
    """
    try:
        # 1. Teste simples de conexão
        result = db.execute(text("SELECT 1")).scalar()
        
        # 2. Verifica a extensão vector
        vector_check = db.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")).scalar()
        
        return {
            "database_connection": "OK" if result == 1 else "FAIL",
            "pgvector_extension": "INSTALLED" if vector_check > 0 else "MISSING",
            "sqlalchemy_mode": "Working"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")


# ============================================
# ROTAS: CLIENTES (CRM)
# ============================================

@app.post("/clients", response_model=schemas.ClientResponse, status_code=201)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    """
    Cria um novo cliente no sistema.
    
    - **name**: Nome do cliente (obrigatório)
    - **email**: Email único do cliente (obrigatório)
    - **company_name**: Nome da empresa (opcional)
    - **phone**: Telefone (opcional)
    - **status**: Status inicial (default: 'lead')
    """
    # Verifica se o email já existe
    existing_client = db.query(models.Client).filter(models.Client.email == client.email).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Email já cadastrado no sistema")
    
    # Cria o novo cliente
    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    return db_client


@app.get("/clients", response_model=List[schemas.ClientResponse])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos os clientes cadastrados.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **status**: Filtrar por status (opcional: lead, prospect, client, churned)
    """
    query = db.query(models.Client)
    
    # Filtro opcional por status
    if status:
        query = query.filter(models.Client.status == status)
    
    clients = query.offset(skip).limit(limit).all()
    return clients


@app.get("/clients/{client_id}", response_model=schemas.ClientResponse)
def get_client(client_id: str, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um cliente específico pelo ID.
    """
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return client


@app.patch("/clients/{client_id}", response_model=schemas.ClientResponse)
def update_client(
    client_id: str,
    client_update: schemas.ClientUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza parcialmente os dados de um cliente.
    """
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Atualiza apenas os campos fornecidos
    update_data = client_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    return client


@app.delete("/clients/{client_id}", status_code=204)
def delete_client(client_id: str, db: Session = Depends(get_db)):
    """
    Remove um cliente do sistema.
    Atenção: Isso pode falhar se houver projetos vinculados (RESTRICT).
    """
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    try:
        db.delete(client)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível deletar cliente com projetos vinculados: {str(e)}"
        )
    
    return None


# ============================================
# ROTAS: PROJETOS
# ============================================

@app.post("/projects/", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Cria um novo projeto vinculado a um cliente.
    
    - **name**: Nome do projeto (obrigatório)
    - **description**: Descrição do projeto (opcional)
    - **project_type**: Tipo do projeto - 'recurring' ou 'one_off' (obrigatório)
    - **value**: Valor do contrato (obrigatório)
    - **start_date**: Data de início (obrigatório)
    - **end_date**: Data de término (opcional)
    - **client_id**: ID do cliente (obrigatório)
    """
    # Valida se o cliente existe
    client = db.query(models.Client).filter(models.Client.id == project.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Prepara dados para o modelo ORM (ajustando nomes de campos)
    project_data = project.model_dump()
    
    # Mapeia campos do schema para o modelo ORM
    # O schema usa 'project_type' e 'value', mas o modelo ORM usa 'type' e 'contract_value'
    orm_data = {
        "client_id": project_data["client_id"],
        "name": project_data["name"],
        "type": project_data["project_type"],  # Mapeia project_type -> type
        "category": "general",  # Valor padrão temporário
        "contract_value": project_data["value"],  # Mapeia value -> contract_value
        "start_date": project_data["start_date"],
        "end_date": project_data.get("end_date"),
    }
    
    # Adiciona description se existir (campo opcional no ORM)
    # Note: O modelo ORM não tem campo 'description', então vamos ignorar por enquanto
    
    # Cria o projeto
    db_project = models.Project(**orm_data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Retorna resposta com mapeamento correto
    return schemas.ProjectResponse(
        id=db_project.id,
        client_id=db_project.client_id,
        name=db_project.name,
        description=None,  # Não temos no ORM
        project_type=db_project.type,  # Mapeia type -> project_type
        value=db_project.contract_value,  # Mapeia contract_value -> value
        start_date=db_project.start_date,
        end_date=db_project.end_date,
        created_at=db_project.created_at
    )


@app.get("/projects/", response_model=List[schemas.ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    client_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos os projetos cadastrados.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **client_id**: Filtrar por cliente específico (opcional)
    """
    query = db.query(models.Project)
    
    # Filtro opcional por cliente
    if client_id:
        query = query.filter(models.Project.client_id == client_id)
    
    projects = query.offset(skip).limit(limit).all()
    
    # Mapeia para o schema de resposta
    return [
        schemas.ProjectResponse(
            id=p.id,
            client_id=p.client_id,
            client_name=p.client.name if p.client else "Cliente não encontrado",  # Adiciona nome do cliente
            name=p.name,
            description=None,  # Não temos no ORM
            project_type=p.type,  # Mapeia type -> project_type
            value=p.contract_value,  # Mapeia contract_value -> value
            start_date=p.start_date,
            end_date=p.end_date,
            created_at=p.created_at
        )
        for p in projects
    ]


@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um projeto específico pelo ID.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    return schemas.ProjectResponse(
        id=project.id,
        client_id=project.client_id,
        client_name=project.client.name if project.client else "Cliente não encontrado",  # Adiciona nome do cliente
        name=project.name,
        description=None,  # Não temos no ORM
        project_type=project.type,  # Mapeia type -> project_type
        value=project.contract_value,  # Mapeia contract_value -> value
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at
    )


# ============================================
# ROTAS: ENTRADA MANUAL DE DADOS
# ============================================

@app.post("/manual/projects", status_code=201)
async def create_project_manual(
    project_name: str,
    client_name: str,
    budget: float,
    product_price: float = 0.0,
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    Cria um novo projeto via entrada manual.
    
    Esta rota executa a mesma lógica que a IA usa, garantindo:
    - Criação/busca do cliente
    - Criação do projeto
    - Registro de receita
    - Geração de memória RAG (log do sistema)
    
    Args:
        project_name: Nome do projeto
        client_name: Nome do cliente (será criado se não existir)
        budget: Orçamento/valor do projeto
        product_price: Preço do produto/serviço (ticket médio) para cálculo de ROI
        description: Descrição opcional
    """
    result_json = await _execute_create_project(
        db=db,
        project_name=project_name,
        client_name=client_name,
        budget=budget,
        product_price=product_price,
        description=description
    )
    
    import json
    result = json.loads(result_json)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@app.post("/manual/expenses", status_code=201)
async def create_expense_manual(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db)
):
    """
    Registra uma nova despesa via entrada manual.
    
    Executa a mesma lógica que a IA usa, garantindo:
    - Criação da despesa
    - Vinculação ao projeto (se fornecido)
    - Geração de memória RAG (log do sistema)
    
    Args:
        expense: Dados da despesa
    """
    # Busca projeto se project_id foi fornecido
    project = None
    if expense.project_id:
        project = db.query(models.Project).filter(models.Project.id == expense.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        project_name = project.name
    else:
        project_name = "Despesa sem projeto vinculado"
    
    # Cria a despesa
    db_expense = models.Expense(
        project_id=expense.project_id,
        category=expense.category,
        description=expense.description,
        amount=expense.amount,
        due_date=expense.due_date,
        paid_date=expense.paid_date,
        status=expense.status,
        is_fixed_cost=expense.is_fixed_cost,
        is_project_related=expense.is_project_related,
        supplier=expense.supplier,
        payment_method=expense.payment_method,
        notes=expense.notes
    )
    
    db.add(db_expense)
    db.flush()
    
    # Gera memória RAG
    log_content = f"SISTEMA: Usuário registrou manualmente despesa de R$ {float(expense.amount):,.2f} - {expense.description}"
    if project:
        log_content += f" no projeto '{project.name}'"
    log_content += f". Categoria: {expense.category}. Data de vencimento: {expense.due_date.strftime('%d/%m/%Y')}."
    
    embedding = await generate_embedding(log_content)
    
    # Determina client_id (se houver projeto, usa o cliente dele)
    client_id = None
    if project and project.client_id:
        client_id = project.client_id
    else:
        # Tenta pegar primeiro cliente disponível como fallback
        first_client = db.query(models.Client).first()
        if first_client:
            client_id = first_client.id
    
    # Só cria interação se houver um client_id válido
    if client_id:
        interaction = models.Interaction(
            client_id=client_id,
            type="system_log",
            content=log_content,
            content_embedding=embedding,
            interaction_date=datetime.now()
        )
        db.add(interaction)
    
    db.commit()
    db.refresh(db_expense)
    
    return {
        "status": "success",
        "expense_id": str(db_expense.id),
        "message": f"✅ Despesa de R$ {float(expense.amount):,.2f} registrada com sucesso!"
    }


@app.post("/manual/marketing-metrics", status_code=201)
async def create_marketing_metrics_manual(
    metric: schemas.MarketingMetricCreate,
    db: Session = Depends(get_db)
):
    """
    Registra métricas de marketing via entrada manual.
    
    Executa a mesma lógica que a IA usaria, garantindo:
    - Criação da métrica
    - Geração de memória RAG (log do sistema com KPIs calculados)
    
    Args:
        metric: Dados da métrica de marketing
    """
    # Busca o projeto
    project = db.query(models.Project).filter(models.Project.id == metric.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    result_json = await _execute_add_marketing_stats(
        db=db,
        project_name=project.name,
        date=metric.date,
        impressions=metric.impressions,
        clicks=metric.clicks,
        leads=metric.leads,
        conversions=metric.conversions,
        cost=float(metric.cost) if metric.cost else None,
        platform=metric.platform,
        source="manual"
    )
    
    import json
    result = json.loads(result_json)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@app.get("/projects/{project_id}/marketing-kpis", response_model=schemas.MarketingKPIs)
def get_project_marketing_kpis(project_id: str, db: Session = Depends(get_db)):
    """
    Retorna KPIs de marketing calculados para um projeto.
    
    Calcula:
    - CTR (Click-Through Rate): Cliques / Impressões
    - CPC (Cost Per Click): Custo / Cliques
    - CPL/CPA (Cost Per Lead): Custo / Leads
    - Taxa de Conversão: Leads / Cliques
    
    Args:
        project_id: ID do projeto
    """
    # Valida se o projeto existe
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Busca todas as métricas do projeto
    metrics = db.query(models.MarketingMetric)\
        .filter(models.MarketingMetric.project_id == project_id)\
        .all()
    
    if not metrics:
        # Retorna zeros se não houver métricas
        return schemas.MarketingKPIs(
            total_impressions=0,
            total_clicks=0,
            total_leads=0,
            total_conversions=0,
            total_cost=0.0,
            ctr="0.00%",
            cpc="R$ 0.00",
            cpl="R$ 0.00",
            conversion_rate="0.00%",
            estimated_revenue=0.0,
            roi="0.00%"
        )
    
    # Calcula totais
    total_impressions = sum(m.impressions for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    total_leads = sum(m.leads for m in metrics)
    total_conversions = sum(m.conversions for m in metrics)
    total_cost = sum(float(m.cost) for m in metrics if m.cost)
    
    # Calcula KPIs
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    cpl = (total_cost / total_leads) if total_leads > 0 else 0
    conversion_rate = (total_leads / total_clicks * 100) if total_clicks > 0 else 0
    
    # Calcula ROI
    product_price = float(project.product_price) if project.product_price else 0.0
    estimated_revenue = total_conversions * product_price
    roi = ((estimated_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
    
    return schemas.MarketingKPIs(
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_leads=total_leads,
        total_conversions=total_conversions,
        total_cost=total_cost,
        ctr=f"{ctr:.2f}%",
        cpc=f"{cpc:.2f}",
        cpl=f"{cpl:.2f}",
        conversion_rate=f"{conversion_rate:.2f}%",
        estimated_revenue=estimated_revenue,
        roi=f"{roi:.2f}%"
    )


# ============================================
# ROTAS: INTERACTIONS (RAG)
# ============================================

@app.post("/interactions/", response_model=schemas.InteractionResponse, status_code=201)
async def create_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova interação com o cliente e gera embedding vetorial.
    
    - **content**: Conteúdo da interação/nota (obrigatório)
    - **interaction_type**: Tipo - meeting, call, email, whatsapp (obrigatório)
    - **client_id**: ID do cliente (obrigatório)
    - **project_id**: ID do projeto (opcional)
    
    O sistema gera automaticamente um embedding vetorial do conteúdo para RAG.
    """
    # Valida se o cliente existe
    client = db.query(models.Client).filter(models.Client.id == interaction.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Valida projeto se fornecido
    if interaction.project_id:
        project = db.query(models.Project).filter(models.Project.id == interaction.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Gera embedding vetorial do conteúdo usando OpenAI
    embedding = await generate_embedding(interaction.content)
    
    # Prepara dados para o modelo ORM
    db_interaction = models.Interaction(
        client_id=interaction.client_id,
        type=interaction.interaction_type.value,  # Converte enum para string
        content=interaction.content,
        content_embedding=embedding,  # Vetor de 1536 dimensões
        interaction_date=datetime.utcnow(),
    )
    
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    
    # Retorna resposta
    return schemas.InteractionResponse(
        id=db_interaction.id,
        client_id=db_interaction.client_id,
        project_id=interaction.project_id,  # Pode ser None
        content=db_interaction.content,
        interaction_type=db_interaction.type,  # Mapeia type -> interaction_type
        created_at=db_interaction.created_at
    )


@app.get("/interactions/", response_model=List[schemas.InteractionResponse])
def list_interactions(
    skip: int = 0,
    limit: int = 100,
    client_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista todas as interações cadastradas.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **client_id**: Filtrar por cliente específico (opcional)
    """
    query = db.query(models.Interaction)
    
    # Filtro opcional por cliente
    if client_id:
        query = query.filter(models.Interaction.client_id == client_id)
    
    # Ordena por data de interação decrescente (mais recentes primeiro)
    query = query.order_by(models.Interaction.interaction_date.desc())
    
    interactions = query.offset(skip).limit(limit).all()
    
    # Mapeia para o schema de resposta
    return [
        schemas.InteractionResponse(
            id=i.id,
            client_id=i.client_id,
            project_id=None,  # Não temos no modelo atual
            content=i.content,
            interaction_type=i.type,  # Mapeia type -> interaction_type
            created_at=i.created_at
        )
        for i in interactions
    ]


@app.get("/interactions/{interaction_id}", response_model=schemas.InteractionResponse)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de uma interação específica pelo ID.
    """
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    
    if not interaction:
        raise HTTPException(status_code=404, detail="Interação não encontrada")
    
    return schemas.InteractionResponse(
        id=interaction.id,
        client_id=interaction.client_id,
        project_id=None,  # Não temos no modelo atual
        content=interaction.content,
        interaction_type=interaction.type,  # Mapeia type -> interaction_type
        created_at=interaction.created_at
    )


# ============================================
# ROTAS: FINANCEIRO - REVENUES (RECEITAS)
# ============================================

@app.post("/revenues/", response_model=schemas.RevenueResponse, status_code=201)
def create_revenue(revenue: schemas.RevenueCreate, db: Session = Depends(get_db)):
    """
    Lança uma receita no sistema.
    
    - **description**: Descrição da receita (obrigatório)
    - **amount**: Valor da receita (obrigatório)
    - **category**: Categoria - setup_fee, monthly_fee, consulting, etc (obrigatório)
    - **received_at**: Data de recebimento (obrigatório)
    - **project_id**: ID do projeto vinculado (obrigatório)
    - **client_id**: ID do cliente (obrigatório)
    """
    # Valida se o cliente existe
    client = db.query(models.Client).filter(models.Client.id == revenue.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Valida se o projeto existe
    project = db.query(models.Project).filter(models.Project.id == revenue.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Cria a receita
    db_revenue = models.Revenue(
        client_id=revenue.client_id,
        project_id=revenue.project_id,
        description=revenue.description,
        amount=revenue.amount,
        due_date=revenue.received_at,  # Usando received_at como due_date
        paid_date=revenue.received_at,  # Marcando como já pago
        status='paid',  # Status pago por padrão
    )
    
    db.add(db_revenue)
    db.commit()
    db.refresh(db_revenue)
    
    return schemas.RevenueResponse(
        id=db_revenue.id,
        project_id=db_revenue.project_id,
        client_id=db_revenue.client_id,
        description=db_revenue.description,
        amount=db_revenue.amount,
        category=revenue.category,  # Retorna do input
        received_at=db_revenue.paid_date,
        status=db_revenue.status,
        created_at=db_revenue.created_at
    )


@app.get("/revenues/", response_model=List[schemas.RevenueResponse])
def list_revenues(
    skip: int = 0,
    limit: int = 100,
    project_id: str = None,
    client_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista todas as receitas cadastradas.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **project_id**: Filtrar por projeto específico (opcional)
    - **client_id**: Filtrar por cliente específico (opcional)
    """
    query = db.query(models.Revenue)
    
    # Filtros opcionais
    if project_id:
        query = query.filter(models.Revenue.project_id == project_id)
    
    if client_id:
        query = query.filter(models.Revenue.client_id == client_id)
    
    # Ordena por data de criação decrescente
    query = query.order_by(models.Revenue.created_at.desc())
    
    revenues = query.offset(skip).limit(limit).all()
    
    return [
        schemas.RevenueResponse(
            id=r.id,
            project_id=r.project_id,
            client_id=r.client_id,
            description=r.description,
            amount=r.amount,
            category=schemas.RevenueCategory.other,  # Default
            received_at=r.paid_date or r.due_date,
            status=r.status,
            created_at=r.created_at
        )
        for r in revenues
    ]


@app.get("/revenues/{revenue_id}", response_model=schemas.RevenueResponse)
def get_revenue(revenue_id: str, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de uma receita específica pelo ID.
    """
    revenue = db.query(models.Revenue).filter(models.Revenue.id == revenue_id).first()
    
    if not revenue:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    return schemas.RevenueResponse(
        id=revenue.id,
        project_id=revenue.project_id,
        client_id=revenue.client_id,
        description=revenue.description,
        amount=revenue.amount,
        category=schemas.RevenueCategory.other,  # Default
        received_at=revenue.paid_date or revenue.due_date,
        status=revenue.status,
        created_at=revenue.created_at
    )


# ============================================
# ROTAS: FINANCEIRO - EXPENSES (DESPESAS)
# ============================================

@app.post("/expenses/", response_model=schemas.ExpenseResponse, status_code=201)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """
    Lança uma despesa no sistema.
    
    - **description**: Descrição da despesa (obrigatório)
    - **amount**: Valor da despesa (obrigatório)
    - **category**: Categoria - software, freelancer, tax, ads, etc (obrigatório)
    - **paid_at**: Data de pagamento (obrigatório)
    - **project_id**: ID do projeto vinculado (opcional - pode ser custo fixo)
    """
    # Se tiver project_id, valida se existe
    if expense.project_id:
        project = db.query(models.Project).filter(models.Project.id == expense.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Determina se é custo fixo ou relacionado a projeto
    is_project_related = expense.project_id is not None
    is_fixed = not is_project_related
    
    # Cria a despesa
    db_expense = models.Expense(
        project_id=expense.project_id,
        category=expense.category.value,
        description=expense.description,
        amount=expense.amount,
        due_date=expense.paid_at,  # Usando paid_at como due_date
        paid_date=expense.paid_at,  # Marcando como já pago
        status='paid',  # Status pago por padrão
        is_fixed_cost=is_fixed,
        is_project_related=is_project_related,
    )
    
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    return schemas.ExpenseResponse(
        id=db_expense.id,
        project_id=db_expense.project_id,
        description=db_expense.description,
        amount=db_expense.amount,
        category=expense.category,
        paid_at=db_expense.paid_date,
        status=db_expense.status,
        is_fixed_cost=db_expense.is_fixed_cost,
        is_project_related=db_expense.is_project_related,
        created_at=db_expense.created_at
    )


@app.get("/expenses/", response_model=List[schemas.ExpenseResponse])
def list_expenses(
    skip: int = 0,
    limit: int = 100,
    project_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista todas as despesas cadastradas.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **project_id**: Filtrar por projeto específico (opcional)
    """
    query = db.query(models.Expense)
    
    # Filtro opcional por projeto
    if project_id:
        query = query.filter(models.Expense.project_id == project_id)
    
    # Ordena por data de criação decrescente
    query = query.order_by(models.Expense.created_at.desc())
    
    expenses = query.offset(skip).limit(limit).all()
    
    return [
        schemas.ExpenseResponse(
            id=e.id,
            project_id=e.project_id,
            description=e.description,
            amount=e.amount,
            category=schemas.ExpenseCategory.other,  # Default, idealmente ler do banco
            paid_at=e.paid_date or e.due_date,
            status=e.status,
            is_fixed_cost=e.is_fixed_cost,
            is_project_related=e.is_project_related,
            created_at=e.created_at
        )
        for e in expenses
    ]


@app.get("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def get_expense(expense_id: str, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de uma despesa específica pelo ID.
    """
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    
    return schemas.ExpenseResponse(
        id=expense.id,
        project_id=expense.project_id,
        description=expense.description,
        amount=expense.amount,
        category=schemas.ExpenseCategory.other,  # Default
        paid_at=expense.paid_date or expense.due_date,
        status=expense.status,
        is_fixed_cost=expense.is_fixed_cost,
        is_project_related=expense.is_project_related,
        created_at=expense.created_at
    )


# ============================================
# ROTAS: DASHBOARD FINANCEIRO
# ============================================

@app.get("/projects/{project_id}/financial-dashboard", response_model=schemas.FinancialSummary)
def get_project_financial_dashboard(project_id: str, db: Session = Depends(get_db)):
    """
    Retorna um resumo financeiro consolidado do projeto.
    
    Calcula:
    - Total de receitas
    - Total de despesas
    - Lucro líquido (receitas - despesas)
    - Margem de lucro percentual
    
    **project_id**: ID do projeto para análise
    """
    # Valida se o projeto existe
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Calcula total de receitas do projeto
    total_revenue = db.query(func.sum(models.Revenue.amount))\
        .filter(models.Revenue.project_id == project_id)\
        .scalar()
    
    # Calcula total de despesas do projeto
    total_expense = db.query(func.sum(models.Expense.amount))\
        .filter(models.Expense.project_id == project_id)\
        .scalar()
    
    # Trata None (sem lançamentos) como 0.0
    total_revenue = float(total_revenue) if total_revenue is not None else 0.0
    total_expense = float(total_expense) if total_expense is not None else 0.0
    
    # Calcula lucro líquido
    net_profit = total_revenue - total_expense
    
    # Calcula margem percentual (protegido contra divisão por zero)
    if total_revenue > 0:
        margin_percentage = (net_profit / total_revenue) * 100
        margin_str = f"{margin_percentage:.1f}%"
    else:
        margin_str = "0.0%"
    
    return schemas.FinancialSummary(
        total_revenue=total_revenue,
        total_expense=total_expense,
        net_profit=net_profit,
        margin_percentage=margin_str
    )


@app.get("/projects/{project_id}/export/pdf")
def export_project_pdf(project_id: str, db: Session = Depends(get_db)):
    """
    Exporta o relatório executivo financeiro do projeto em formato PDF.
    
    Gera um documento com:
    - Dados do projeto (nome, cliente, status, datas)
    - Resumo financeiro (receitas, despesas, lucro, margem)
    - Tabela detalhada de despesas
    
    **project_id**: ID do projeto para exportação
    
    Retorna um arquivo PDF para download.
    """
    try:
        # Gera o PDF
        pdf_bytes = generate_project_pdf(db, project_id)
        
        # Retorna como resposta com headers apropriados
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=relatorio_projeto_{project_id[:8]}.pdf"
            }
        )
    except ValueError as e:
        # Projeto não encontrado
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Erro interno na geração do PDF
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


# ============================================
# ROTAS: AI - BUSCA SEMÂNTICA (RAG)
# ============================================

@app.post("/ai/search", response_model=schemas.SearchResponse)
async def semantic_search(request: schemas.SearchRequest, db: Session = Depends(get_db)):
    """
    Busca semântica de interações usando embeddings vetoriais.
    
    Utiliza pgvector para encontrar as interações mais similares à query fornecida.
    
    - **query**: Texto de busca em linguagem natural
    - **limit**: Número máximo de resultados (default: 5)
    
    Exemplo:
    - Query: "problemas com prazo de entrega"
    - Retorna: Interações que mencionam atrasos, deadlines, etc.
    """
    # Gera embedding da query de busca
    query_embedding = await generate_embedding(request.query)
    
    # Busca as interações mais similares usando cosine distance do pgvector
    # Quanto menor a distância, mais similar é o conteúdo
    similar_interactions = db.query(models.Interaction)\
        .filter(models.Interaction.content_embedding.isnot(None))\
        .order_by(models.Interaction.content_embedding.cosine_distance(query_embedding))\
        .limit(request.limit)\
        .all()
    
    # Mapeia para o schema de resposta
    results = [
        schemas.InteractionResponse(
            id=i.id,
            client_id=i.client_id,
            project_id=None,  # Não temos no modelo atual
            content=i.content,
            interaction_type=i.type,
            created_at=i.created_at
        )
        for i in similar_interactions
    ]
    
    return schemas.SearchResponse(results=results)


@app.post("/ai/chat", response_model=schemas.ChatResponse)
async def chat_with_rag(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Chat com IA usando RAG (Retrieval-Augmented Generation) e Visão Multimodal.
    
    O sistema:
    1. Busca interações relevantes no banco usando embeddings
    2. Usa esse contexto para responder à pergunta via GPT
    3. Suporta imagens (Base64) para análise visual (ex: recibos, notas fiscais)
    
    - **query**: Pergunta em linguagem natural
    - **image**: (Opcional) Imagem em Base64 para análise visual
    
    Exemplos:
    - "Quais foram os principais problemas reportados pelo cliente X?"
    - "Resuma as últimas reuniões sobre o projeto Y"
    - "O cliente mencionou algo sobre prazos?"
    - "Registre esta despesa" + [imagem do recibo]
    """
    # 1. Gera embedding da pergunta
    query_embedding = await generate_embedding(request.query)
    
    # 2. Busca as 3 interações mais relevantes no banco (⚠️ OTIMIZAÇÃO: max 3 chunks para minimizar tokens)
    relevant_interactions = db.query(models.Interaction)\
        .filter(models.Interaction.content_embedding.isnot(None))\
        .order_by(models.Interaction.content_embedding.cosine_distance(query_embedding))\
        .limit(3)\
        .all()
    
    # 3. Concatena o conteúdo das interações como contexto
    if relevant_interactions:
        context_text = "\n\n---\n\n".join([
            f"Interação ({i.type}) em {i.interaction_date}:\n{i.content}"
            for i in relevant_interactions
        ])
    else:
        context_text = "Nenhuma informação disponível no banco de dados."
    
    # 4. Gera resposta usando GPT com o contexto, sessão do banco e imagem (se fornecida)
    answer = await generate_answer(
        query=request.query,
        context=context_text,
        db=db,
        image_data=request.image  # Passa a imagem Base64 (ou None)
    )
    
    return schemas.ChatResponse(answer=answer)


@app.delete("/interactions/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    """
    Remove uma interação do sistema.
    """
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    
    if not interaction:
        raise HTTPException(status_code=404, detail="Interação não encontrada")
    
    db.delete(interaction)
    db.commit()
    
    return None

@app.get("/clients/{client_id}/interactions")
def get_client_interactions_endpoint(client_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Busca as últimas interações de um cliente para exibir na timeline.
    """
    from app.services import get_client_interactions
    
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    interactions = get_client_interactions(db, client_id, limit)
    
    return {
        "client_id": client_id,
        "client_name": client.name,
        "total": len(interactions),
        "interactions": interactions
    }