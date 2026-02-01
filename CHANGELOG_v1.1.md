# Atualização: Entrada Manual e Métricas de Marketing

**Data:** 28/01/2026  
**Versão:** 1.1.0

## 📋 Resumo das Mudanças

Esta atualização adiciona duas funcionalidades críticas ao Agency OS:

1. **Interface de Entrada Manual de Dados** - Permite que usuários registrem informações diretamente, sem depender apenas do chat com IA
2. **Métricas de Marketing (Performance)** - Rastreamento completo de campanhas com KPIs calculados automaticamente

### ✅ Garantias Implementadas

- ✓ **Memória RAG Universal**: Entrada manual gera logs automáticos para a IA
- ✓ **Funções Reutilizáveis**: Mesma lógica para IA e entrada manual
- ✓ **Integridade Total**: Todas as operações são atômicas (commit/rollback)
- ✓ **Auditoria Completa**: Timestamps e rastreabilidade de todas as operações

---

## 🆕 Novos Recursos

### 1. Modelo de Dados: MarketingMetric

**Localização:** [`app/models.py`](app/models.py)

```python
class MarketingMetric(Base):
    """Tabela de Métricas de Marketing"""
    __tablename__ = "marketing_metrics"
    
    # Campos principais
    - project_id (UUID, FK)
    - date (datetime)
    - impressions (int)
    - clicks (int)
    - leads (int)
    - conversions (int)
    - cost (Decimal, opcional)
    - platform (str) - Google Ads, Meta Ads, etc.
```

**Migration SQL:** [`migrations/001_add_marketing_metrics.sql`](migrations/001_add_marketing_metrics.sql)

---

### 2. Funções de Serviço Reutilizáveis

**Localização:** [`app/services.py`](app/services.py)

#### `_execute_create_project()`
- ✓ Cria/busca cliente automaticamente
- ✓ Cria projeto
- ✓ Registra receita inicial
- ✓ **Gera log RAG** para memória da IA

#### `_execute_add_expense()`
- ✓ Vincula despesa ao projeto
- ✓ Calcula impacto financeiro
- ✓ **Gera log RAG** com detalhes

#### `_execute_add_marketing_stats()` (NOVO)
- ✓ Registra métricas de marketing
- ✓ Calcula KPIs (CTR, CPC, CPL, Taxa de Conversão)
- ✓ **Gera log RAG** com análise de performance

**Importante:** Todas as funções são `async` e trabalham com a mesma sessão do banco de dados, garantindo atomicidade.

---

### 3. Endpoints REST da API

**Localização:** [`main.py`](main.py)

#### POST `/manual/projects`
Cria novo projeto via entrada manual.

**Payload:**
```json
{
  "project_name": "Campanha Black Friday",
  "client_name": "Loja ABC",
  "budget": 10000.0,
  "description": "Campanha de vendas para BF"
}
```

#### POST `/manual/expenses`
Registra nova despesa.

**Payload:**
```json
{
  "project_id": "uuid-do-projeto",
  "category": "Publicidade",
  "description": "Google Ads - Novembro",
  "amount": 2500.00,
  "due_date": "2026-11-30",
  "status": "pending"
}
```

#### POST `/manual/marketing-metrics`
Registra métricas de marketing.

**Payload:**
```json
{
  "project_id": "uuid-do-projeto",
  "date": "2026-01-28T00:00:00",
  "impressions": 50000,
  "clicks": 1500,
  "leads": 75,
  "conversions": 15,
  "cost": 3000.00,
  "platform": "Google Ads"
}
```

#### GET `/projects/{project_id}/marketing-kpis`
Retorna KPIs calculados de marketing.

**Resposta:**
```json
{
  "total_impressions": 50000,
  "total_clicks": 1500,
  "total_leads": 75,
  "total_conversions": 15,
  "total_cost": 3000.00,
  "ctr": "3.00%",
  "cpc": "R$ 2.00",
  "cpl": "R$ 40.00",
  "conversion_rate": "5.00%"
}
```

---

### 4. Nova Aba no Frontend: "✍️ Lançamentos Manuais"

**Localização:** [`frontend/app.py`](frontend/app.py)

Interface com 3 formulários organizados em tabs:

#### Tab 1: 💼 Novo Projeto
- Nome do projeto
- Nome do cliente (criado automaticamente se não existir)
- Orçamento
- Descrição opcional

#### Tab 2: 💸 Nova Despesa
- SelectBox com projetos existentes
- Descrição da despesa
- Valor e data de vencimento
- Categoria (Publicidade, Freelancer, Software, etc.)
- Status (Pendente/Pago)

#### Tab 3: 📊 Métricas de Marketing
- SelectBox com projetos existentes
- Data das métricas
- Impressões, Cliques, Leads, Conversões
- Custo da campanha
- Plataforma (Google Ads, Meta Ads, TikTok Ads, etc.)

**Funcionalidades:**
- ✓ Validação de campos obrigatórios
- ✓ Feedback visual (success/error)
- ✓ Animações (balloons) em operações bem-sucedidas
- ✓ Mensagens de KPIs calculados automaticamente

---

### 5. Dashboard Financeiro com KPIs de Marketing

**Localização:** [`frontend/app.py`](frontend/app.py) - Página "📊 Dashboard Financeiro"

Nova seção adicionada após o resumo financeiro:

#### Métricas Exibidas:
- **👁️ Impressões** - Total de visualizações
- **🖱️ Cliques** - Com badge de CTR
- **🎯 Leads** - Com badge de Taxa de Conversão
- **💰 Custo Total** - Investimento em marketing

#### KPIs Calculados:
- **CPC Médio** (Cost Per Click) - Custo / Cliques
- **CPA/CPL Médio** (Cost Per Lead) - Custo / Leads
- **Taxa de Conversão** - Leads / Cliques × 100
  - 🟢 Excelente: > 5%
  - 🟡 Saudável: 2-5%
  - 🔴 Baixa: < 2%

#### Análise Inteligente:
O sistema fornece feedback automático sobre a performance:
- ✅ "Excelente taxa de conversão!" (> 5%)
- ℹ️ "Taxa de conversão saudável." (2-5%)
- ⚠️ "Taxa de conversão baixa. Considere otimizar." (< 2%)

---

## 🔄 Como Usar

### 1. Criar a Tabela no Banco

```bash
psql -h localhost -U postgres -d agency_os -f migrations/001_add_marketing_metrics.sql
```

### 2. Reiniciar a API

```bash
# Backend
cd c:\Users\Kauã\Desktop\SOG
uvicorn main:app --reload
```

### 3. Iniciar o Frontend

```bash
# Frontend
cd c:\Users\Kauã\Desktop\SOG\frontend
streamlit run app.py
```

### 4. Workflow Completo

1. **Criar Projeto**
   - Acesse "✍️ Lançamentos Manuais" → Tab "💼 Novo Projeto"
   - Preencha: Nome, Cliente, Orçamento
   - Clique em "Criar Projeto"
   - Copie o ID do projeto gerado

2. **Registrar Despesas**
   - Tab "💸 Nova Despesa"
   - Selecione o projeto
   - Informe descrição, valor, categoria
   - Sistema gera log RAG automaticamente

3. **Adicionar Métricas de Marketing**
   - Tab "📊 Métricas de Marketing"
   - Selecione o projeto
   - Informe impressões, cliques, leads
   - Sistema calcula KPIs e gera log RAG

4. **Visualizar Dashboard**
   - Acesse "📊 Dashboard Financeiro"
   - Cole o ID do projeto
   - Veja resumo financeiro + KPIs de marketing

5. **Consultar via IA**
   - Acesse "🤖 Agency Brain"
   - Pergunte: "Qual a performance de marketing do projeto X?"
   - A IA usa os logs RAG gerados pela entrada manual

---

## 🧠 Integração com IA

### Como a IA Usa os Dados Manuais

Todos os lançamentos manuais geram **interactions** do tipo `system_log` com:

1. **Conteúdo Estruturado**: Descrição clara da operação
2. **Embedding Vetorial**: Indexado para busca semântica
3. **Timestamp**: Rastreabilidade temporal

**Exemplo de Log RAG (Métrica de Marketing):**
```
SISTEMA: Métricas de marketing registradas para o projeto 'Campanha Black Friday'.
Data: 28/01/2026
Performance: 50,000 impressões, 1,500 cliques, 75 leads
Plataforma: Google Ads
Custo: R$ 3,000.00
KPIs: CTR 3.00%, CPC R$ 2.00, CPL R$ 40.00
```

### Perguntas que a IA Pode Responder

- "Qual projeto tem melhor taxa de conversão?"
- "Quanto gastamos em marketing este mês?"
- "O CPC do projeto X está dentro da meta?"
- "Liste todos os projetos com CPL acima de R$ 50"

---

## 📊 Schemas Adicionados

**Localização:** [`app/schemas.py`](app/schemas.py)

### MarketingMetricCreate
```python
class MarketingMetricCreate(BaseModel):
    project_id: UUID
    date: datetime
    impressions: int = 0
    clicks: int = 0
    leads: int = 0
    conversions: int = 0
    cost: Optional[Decimal] = None
    platform: Optional[str] = None
```

### MarketingKPIs
```python
class MarketingKPIs(BaseModel):
    total_impressions: int
    total_clicks: int
    total_leads: int
    total_conversions: int
    total_cost: float
    ctr: str  # "3.00%"
    cpc: str  # "R$ 2.00"
    cpl: str  # "R$ 40.00"
    conversion_rate: str  # "5.00%"
```

### ExpenseCreate
```python
class ExpenseCreate(BaseModel):
    project_id: Optional[UUID] = None
    category: str
    description: str
    amount: Decimal
    due_date: date
    status: str = "pending"
```

---

## 🔒 Garantias de Integridade

### Operações Atômicas
Todas as funções usam:
```python
db.flush()  # Garante IDs gerados
db.commit()  # Confirma transação
db.rollback()  # Reverte em caso de erro
```

### Validações
- ✓ Projeto existe antes de vincular despesa/métrica
- ✓ Valores numéricos são positivos
- ✓ Datas são válidas
- ✓ Campos obrigatórios são verificados

### Logs RAG
- ✓ Sempre gerados, mesmo em caso de entrada manual
- ✓ Embedding vetorial para busca semântica
- ✓ Vinculado ao cliente correto (via projeto)
- ✓ Timestamp UTC para consistência

---

## 🎯 Próximos Passos Sugeridos

1. **Dashboard Analítico**
   - Gráficos de evolução temporal (impressões ao longo do tempo)
   - Comparação entre projetos
   - Benchmarks de performance

2. **Alertas Inteligentes**
   - Notificar quando CPL ultrapassa limite
   - Avisar sobre queda de conversão
   - Sugerir otimizações

3. **Exportação de Dados**
   - CSV de métricas de marketing
   - Relatórios de performance em PDF
   - Integração com Google Sheets

4. **Integração Automática**
   - Conectar APIs de plataformas (Google Ads API, Meta API)
   - Import automático de métricas
   - Sincronização bidirecional

---

## 📝 Checklist de Implementação

- [x] Modelo MarketingMetric criado
- [x] Migration SQL gerada
- [x] Função _execute_add_marketing_stats implementada
- [x] Endpoints REST criados
- [x] Schemas adicionados
- [x] Frontend com aba de lançamentos manuais
- [x] Dashboard com KPIs de marketing
- [x] Memória RAG integrada
- [x] Validações e tratamento de erros
- [x] Documentação completa

---

## 🐛 Troubleshooting

### Erro: "Tabela marketing_metrics não existe"
**Solução:** Execute a migration:
```bash
psql -h localhost -U postgres -d agency_os -f migrations/001_add_marketing_metrics.sql
```

### Erro: "API não está respondendo"
**Solução:** Verifique se o backend está rodando:
```bash
curl http://localhost:8000/
```

### Erro: "Projeto não encontrado"
**Solução:** Use o endpoint GET /projects/ para listar projetos disponíveis.

---

## 👨‍💻 Informações Técnicas

**Linguagem:** Python 3.11+  
**Framework Backend:** FastAPI 0.109+  
**Framework Frontend:** Streamlit 1.30+  
**Banco de Dados:** PostgreSQL 15+ com pgvector  
**IA:** OpenAI GPT-4o-mini + text-embedding-3-small

---

**Desenvolvido por:** Senior Full Stack Engineer  
**Data:** 28 de Janeiro de 2026
