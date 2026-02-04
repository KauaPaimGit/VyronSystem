"""
SQLAlchemy ORM Models
Mapeamento das tabelas do banco de dados Agency OS
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    String, Integer, Numeric, Boolean, Date, DateTime, Text,
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.database import engine

# ============================================
# MÓDULO: AUTENTICAÇÃO
# ============================================

class User(Base):
    """Tabela de Usuários para Autenticação"""
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default='user')  # 'admin', 'user', 'manager', etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)


# ============================================
# MÓDULO: CRM INTELIGENTE
# ============================================

class Client(Base):
    """Tabela de Leads/Clientes"""
    __tablename__ = "clients"
    
    # Campos principais
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='lead')
    segment: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Campos para análise de IA
    profile_summary: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    health_score: Mapped[Optional[int]] = mapped_column(Integer, CheckConstraint('health_score >= 0 AND health_score <= 100'))
    churn_risk: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Dados financeiros agregados
    lifetime_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0'))
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0'))
    average_project_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0'))
    
    # Metadados
    source: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relacionamentos
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="client")
    interactions: Mapped[List["Interaction"]] = relationship("Interaction", back_populates="client")
    sales_pipeline: Mapped[List["SalesPipeline"]] = relationship("SalesPipeline", back_populates="client")
    revenues: Mapped[List["Revenue"]] = relationship("Revenue", back_populates="client")
    contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="client")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('sentiment_score >= -1.0 AND sentiment_score <= 1.0', name='valid_sentiment'),
    )


class SalesPipeline(Base):
    """Tabela de Funil de Vendas"""
    __tablename__ = "sales_pipeline"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    probability: Mapped[Optional[int]] = mapped_column(Integer, CheckConstraint('probability >= 0 AND probability <= 100'))
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Campos para análise
    lost_reason: Mapped[Optional[str]] = mapped_column(Text)
    won_date: Mapped[Optional[date]] = mapped_column(Date)
    days_in_pipeline: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    client: Mapped["Client"] = relationship("Client", back_populates="sales_pipeline")


class Interaction(Base):
    """Tabela de Interações - PREPARADA PARA RAG"""
    __tablename__ = "interactions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Conteúdo bruto para RAG
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))  # OpenAI embeddings
    
    # Metadados para contexto da IA
    participants: Mapped[Optional[dict]] = mapped_column(JSONB)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Análise de IA
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    key_topics: Mapped[Optional[dict]] = mapped_column(JSONB)
    action_items: Mapped[Optional[dict]] = mapped_column(JSONB)
    entities_mentioned: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Classificação automática
    is_positive: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_complaint: Mapped[Optional[bool]] = mapped_column(Boolean)
    requires_followup: Mapped[Optional[bool]] = mapped_column(Boolean)
    urgency_level: Mapped[Optional[str]] = mapped_column(String(20))
    
    interaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relacionamentos
    client: Mapped["Client"] = relationship("Client", back_populates="interactions")
    
    # Índices para RAG
    __table_args__ = (
        Index('idx_interactions_client', 'client_id'),
        Index('idx_interactions_date', 'interaction_date'),
        Index('idx_interactions_embedding', 'content_embedding', postgresql_using='ivfflat', postgresql_ops={'content_embedding': 'vector_cosine_ops'}),
    )


# ============================================
# MÓDULO: GESTÃO DE PROJETOS
# ============================================

class Project(Base):
    """Tabela de Projetos"""
    __tablename__ = "projects"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='planning')
    
    # Dados do contrato
    contract_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_frequency: Mapped[Optional[str]] = mapped_column(String(50))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Para projetos recorrentes
    is_recurrent: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_cycle: Mapped[Optional[str]] = mapped_column(String(20))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Análise de rentabilidade
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    actual_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal('0'))
    profit_margin_target: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    actual_profit_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    
    # Marketing & ROI
    product_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0.00'), nullable=False, comment="Preço do produto/serviço (ticket médio) para cálculo de ROI")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relacionamentos
    client: Mapped["Client"] = relationship("Client", back_populates="projects")
    tasks: Mapped[List["ProjectTask"]] = relationship("ProjectTask", back_populates="project")
    revenues: Mapped[List["Revenue"]] = relationship("Revenue", back_populates="project")
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="project")
    project_costs: Mapped[List["ProjectCost"]] = relationship("ProjectCost", back_populates="project")
    contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="project")


class TaskTemplate(Base):
    """Templates de Tarefas"""
    __tablename__ = "task_templates"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_category: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    order_index: Mapped[Optional[int]] = mapped_column(Integer)
    assignee_role: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    tasks: Mapped[List["ProjectTask"]] = relationship("ProjectTask", back_populates="template")


class ProjectTask(Base):
    """Tarefas do Projeto"""
    __tablename__ = "project_tasks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    template_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('task_templates.id'))
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='todo')
    priority: Mapped[str] = mapped_column(String(20), default='medium')
    
    assigned_to: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    actual_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal('0'))
    
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    template: Mapped[Optional["TaskTemplate"]] = relationship("TaskTemplate", back_populates="tasks")


# ============================================
# MÓDULO: FINANCEIRO & ERP
# ============================================

class Revenue(Base):
    """Tabela de Receitas (Contas a Receber)"""
    __tablename__ = "revenues"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'))
    client_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False)
    
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending')
    
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="revenues")
    client: Mapped["Client"] = relationship("Client", back_populates="revenues")


class Expense(Base):
    """Tabela de Despesas (Contas a Pagar)"""
    __tablename__ = "expenses"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'))
    
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending')
    
    # Classificação para análise
    is_fixed_cost: Mapped[bool] = mapped_column(Boolean, default=False)
    is_project_related: Mapped[bool] = mapped_column(Boolean, default=False)
    supplier: Mapped[Optional[str]] = mapped_column(String(255))
    
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="expenses")
    project_costs: Mapped[List["ProjectCost"]] = relationship("ProjectCost", back_populates="expense")


class ProjectCost(Base):
    """Tabela de Custos por Projeto"""
    __tablename__ = "project_costs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    expense_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('expenses.id', ondelete='SET NULL'))
    
    cost_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Rastreabilidade de tempo
    hours_worked: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    project: Mapped["Project"] = relationship("Project", back_populates="project_costs")
    expense: Mapped[Optional["Expense"]] = relationship("Expense", back_populates="project_costs")


# ============================================
# MÓDULO: GERADOR DE CONTRATOS
# ============================================

class ContractTemplate(Base):
    """Templates de Contratos"""
    __tablename__ = "contract_templates"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Conteúdo do template
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Variáveis disponíveis
    available_variables: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Cláusulas opcionais
    optional_clauses: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relacionamentos
    contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="template")


class Contract(Base):
    """Contratos Gerados"""
    __tablename__ = "contracts"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    template_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('contract_templates.id'))
    client_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('clients.id', ondelete='RESTRICT'), nullable=False)
    project_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'))
    
    contract_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Conteúdo final
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Variáveis utilizadas
    variables_used: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Status do contrato
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='draft')
    
    # Datas importantes
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Assinaturas
    client_signature_url: Mapped[Optional[str]] = mapped_column(String(500))
    agency_signature_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relacionamentos
    template: Mapped[Optional["ContractTemplate"]] = relationship("ContractTemplate", back_populates="contracts")
    client: Mapped["Client"] = relationship("Client", back_populates="contracts")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="contracts")


# ============================================
# MÓDULO: AI BRAIN
# ============================================

class AIInsight(Base):
    """Análises de IA (Cache de insights)"""
    __tablename__ = "ai_insights"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    # Insight gerado pela IA
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    
    # Ações sugeridas
    action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    suggested_actions: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadados
    priority: Mapped[str] = mapped_column(String(20), default='medium')
    status: Mapped[str] = mapped_column(String(50), default='active')
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Índices para busca eficiente
    __table_args__ = (
        Index('idx_ai_insights_entity', 'entity_type', 'entity_id'),
        Index('idx_ai_insights_type', 'insight_type'),
    )


# ============================================
# MÓDULO: MARKETING PERFORMANCE
# ============================================

class MarketingMetric(Base):
    """Tabela de Métricas de Marketing"""
    __tablename__ = "marketing_metrics"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    
    # Data da métrica
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Métricas de performance
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    leads: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Custo (opcional - pode ser diferente de expense)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    
    # Metadados
    campaign_name: Mapped[Optional[str]] = mapped_column(String(255))
    platform: Mapped[Optional[str]] = mapped_column(String(100))  # Google Ads, Meta Ads, etc.
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relacionamento
    project: Mapped["Project"] = relationship("Project")
    
    # Índices
    __table_args__ = (
        Index('idx_marketing_metrics_project', 'project_id'),
        Index('idx_marketing_metrics_date', 'date'),
    )
