"""
Pydantic Schemas para Validação de Dados
Modelos de entrada/saída da API FastAPI
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, ConfigDict, Field


# ============================================
# SCHEMAS: CLIENTS (CRM)
# ============================================

class ClientBase(BaseModel):
    """Schema base para Cliente"""
    name: str
    company_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    status: str = "lead"  # lead, prospect, client, churned
    segment: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[str] = None


class ClientCreate(ClientBase):
    """Schema para criação de Cliente"""
    pass


class ClientUpdate(BaseModel):
    """Schema para atualização parcial de Cliente"""
    name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    segment: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    profile_summary: Optional[str] = None
    sentiment_score: Optional[Decimal] = None
    health_score: Optional[int] = None
    churn_risk: Optional[str] = None


class ClientResponse(ClientBase):
    """Schema de resposta com dados do Cliente"""
    id: UUID
    profile_summary: Optional[str] = None
    sentiment_score: Optional[Decimal] = None
    health_score: Optional[int] = None
    churn_risk: Optional[str] = None
    lifetime_value: Decimal
    total_spent: Decimal
    average_project_value: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS: PROJECTS
# ============================================

class ProjectType(str, Enum):
    """Enum para tipos de projeto"""
    recurring = "recurring"  # Recorrente
    one_off = "one_off"  # Pontual
    prospection = "prospection"  # Prospecção


class ProjectBase(BaseModel):
    """Schema base para Projeto"""
    name: str
    description: Optional[str] = None
    project_type: ProjectType
    value: Decimal
    start_date: date
    end_date: Optional[date] = None
    product_price: Optional[Decimal] = Field(default=Decimal('0.00'), description="Preço do produto/serviço (ticket médio)")


class ProjectCreate(ProjectBase):
    """Schema para criação de Projeto"""
    client_id: UUID


class ProjectUpdate(BaseModel):
    """Schema para atualização parcial de Projeto"""
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    value: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(ProjectBase):
    """Schema de resposta com dados do Projeto"""
    id: UUID
    client_id: UUID
    client_name: Optional[str] = None  # Nome do cliente para facilitar exibição
    status: Optional[str] = None  # Status do projeto no Kanban
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS: INTERACTIONS
# ============================================

class InteractionType(str, Enum):
    """Enum para tipos de interação"""
    meeting = "meeting"
    call = "call"
    email = "email"
    whatsapp = "whatsapp"


class InteractionBase(BaseModel):
    """Schema base para Interação"""
    content: str
    interaction_type: InteractionType


class InteractionCreate(InteractionBase):
    """Schema para criação de Interação"""
    client_id: UUID
    project_id: Optional[UUID] = None


class InteractionResponse(InteractionBase):
    """Schema de resposta com dados da Interação"""
    id: UUID
    client_id: UUID
    project_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS: FINANCEIRO (REVENUES & EXPENSES)
# ============================================

class RevenueCategory(str, Enum):
    """Enum para categorias de receita"""
    setup_fee = "setup_fee"
    monthly_fee = "monthly_fee"
    consulting = "consulting"
    project_delivery = "project_delivery"
    other = "other"


class ExpenseCategory(str, Enum):
    """Enum para categorias de despesa"""
    software = "software"
    freelancer = "freelancer"
    tax = "tax"
    ads = "ads"
    office = "office"
    infrastructure = "infrastructure"
    salary = "salary"
    other = "other"


class RevenueBase(BaseModel):
    """Schema base para Receita"""
    description: str
    amount: Decimal
    category: RevenueCategory
    received_at: Optional[date] = None


class RevenueCreate(RevenueBase):
    """Schema para criação de Receita"""
    project_id: UUID
    client_id: UUID


class RevenueUpdate(BaseModel):
    """Schema para atualização parcial de Receita"""
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[RevenueCategory] = None
    received_at: Optional[date] = None
    status: Optional[str] = None


class RevenueResponse(RevenueBase):
    """Schema de resposta com dados da Receita"""
    id: UUID
    project_id: Optional[UUID]
    client_id: UUID
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# (Expense schemas consolidados abaixo, seção "Adicional para entrada manual")


# ============================================
# SCHEMAS: DASHBOARD FINANCEIRO
# ============================================

class FinancialSummary(BaseModel):
    """Schema para resumo financeiro de projeto"""
    total_revenue: float
    total_expense: float
    net_profit: float
    margin_percentage: str


# ============================================
# SCHEMAS: AI - BUSCA SEMÂNTICA (RAG)
# ============================================

class SearchRequest(BaseModel):
    """Schema para requisição de busca semântica"""
    query: str
    limit: int = 5


class SearchResponse(BaseModel):
    """Schema para resposta de busca semântica"""
    results: List[InteractionResponse]


class ChatRequest(BaseModel):
    """Schema para requisição de chat com IA (suporta multimodal)"""
    query: str
    image: Optional[str] = None  # Imagem em Base64 (opcional para visão multimodal)


class ChatResponse(BaseModel):
    """Schema para resposta do chat com IA"""
    answer: str


# ============================================
# SCHEMAS: DOCUMENT RAG (Ingestão de Documentos)
# ============================================

class DocumentSearchRequest(BaseModel):
    """Schema para busca semântica em documentos ingeridos"""
    query: str
    limit: int = 3
    filename: Optional[str] = None  # Filtro opcional por arquivo


class DocumentChunkResult(BaseModel):
    """Um chunk retornado pela busca semântica"""
    id: str
    filename: str
    chunk_index: int
    content: str
    score: float
    metadata: Optional[dict] = None


class DocumentSearchResponse(BaseModel):
    """Resposta da busca semântica em documentos"""
    query: str
    results: List[DocumentChunkResult]
    total: int


class DocumentIngestResponse(BaseModel):
    """Resposta da ingestão de um documento"""
    filename: str
    total_pages: int
    total_chunks: int
    status: str


# ============================================
# SCHEMAS: MARKETING METRICS
# ============================================

class MarketingMetricCreate(BaseModel):
    """Schema para criação de Métrica de Marketing"""
    project_id: UUID
    date: datetime
    impressions: int = 0
    clicks: int = 0
    leads: int = 0
    conversions: int = 0
    cost: Optional[Decimal] = None
    campaign_name: Optional[str] = None
    platform: Optional[str] = None
    notes: Optional[str] = None


class MarketingMetricResponse(BaseModel):
    """Schema de resposta com dados da Métrica"""
    id: UUID
    project_id: UUID
    date: datetime
    impressions: int
    clicks: int
    leads: int
    conversions: int
    cost: Optional[Decimal]
    campaign_name: Optional[str]
    platform: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MarketingKPIs(BaseModel):
    """Schema para KPIs de Marketing calculados"""
    total_impressions: int
    total_clicks: int
    total_leads: int
    total_conversions: int
    total_cost: float
    ctr: str  # Click-Through Rate (Clicks/Impressions)
    cpc: str  # Cost Per Click
    cpl: str  # Cost Per Lead (CPA)
    conversion_rate: str  # Taxa de Conversão (Leads/Clicks)
    
    # ROI Metrics
    estimated_revenue: float  # Total de conversões * preço do produto
    roi: str  # Return on Investment ((Revenue - Cost) / Cost * 100)


# ============================================
# SCHEMAS: EXPENSE (Adicional para entrada manual)
# ============================================

class ExpenseCreate(BaseModel):
    """Schema para criação de Despesa"""
    project_id: Optional[UUID] = None
    category: str
    description: str
    amount: Decimal
    due_date: date
    paid_date: Optional[date] = None
    status: str = "pending"
    is_fixed_cost: bool = False
    is_project_related: bool = False
    supplier: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    """Schema de resposta com dados da Despesa"""
    id: UUID
    project_id: Optional[UUID]
    category: str
    description: str
    amount: Decimal
    due_date: date
    paid_date: Optional[date]
    status: str
    is_fixed_cost: bool = False
    is_project_related: bool = False
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS: AUDIT LOGS
# ============================================

class AuditLogResponse(BaseModel):
    """Schema de resposta para logs de auditoria."""
    id: UUID
    timestamp: datetime
    method: str
    path: str
    status_code: int
    duration_ms: Optional[int] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS: SPY MODULE — Inteligência Competitiva (v1.2)
# ============================================

class AdsPlatformEnum(str, Enum):
    """Plataformas de anúncios suportadas."""
    google_ads = "Google Ads"
    meta_ads = "Meta Ads"
    linkedin_ads = "LinkedIn Ads"
    tiktok_ads = "TikTok Ads"
    none = "Nenhum detectado"


class TrafficTierEnum(str, Enum):
    """Faixas estimadas de tráfego."""
    low = "low"
    medium = "medium"
    high = "high"
    very_high = "very_high"


class SpyRequest(BaseModel):
    """Payload para disparar análise de espionagem competitiva."""
    website_url: Optional[str] = Field(None, description="URL do site do lead para análise")
    force_refresh: bool = Field(False, description="Forçar re-análise mesmo se já existir")


class CompetitorIntelResponse(BaseModel):
    """Resposta com dados de inteligência competitiva."""
    id: UUID
    lead_id: UUID
    competitor_name: str
    website_url: Optional[str] = None
    ads_platform: Optional[str] = None
    estimated_traffic_tier: Optional[str] = None
    tech_stack: Optional[str] = None
    market_sentiment: Optional[float] = None
    analysis_summary: Optional[str] = None
    last_spy_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpyAnalysisResponse(BaseModel):
    """Resposta completa de uma análise Spy."""
    success: bool
    lead_name: str
    intel: CompetitorIntelResponse
    rag_indexed: bool = False
    message: str = ""
