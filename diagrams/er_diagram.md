# Diagrama de Entidades e Relacionamentos - Agency OS

## 📊 Visão Geral dos Relacionamentos

```
┌─────────────┐
│   CLIENTS   │──────────┐
└─────────────┘          │
      │                  │
      │ 1:N              │ 1:N
      ↓                  ↓
┌─────────────┐    ┌──────────────┐
│INTERACTIONS │    │SALES_PIPELINE│
└─────────────┘    └──────────────┘
      │
      │ (AI: embedding)
      ↓
   [RAG/LLM]
```

```
┌─────────────┐
│   CLIENTS   │
└─────────────┘
      │
      │ 1:N
      ↓
┌─────────────┐       1:N        ┌──────────────┐
│  PROJECTS   │─────────────────→│PROJECT_TASKS │
└─────────────┘                  └──────────────┘
      │                                  │
      │ 1:N                             │ N:1
      ↓                                  ↓
┌──────────────┐              ┌─────────────────┐
│PROJECT_COSTS │              │TASK_TEMPLATES   │
└──────────────┘              └─────────────────┘
      │
      │ N:1
      ↓
┌─────────────┐
│  EXPENSES   │
└─────────────┘
```

```
┌─────────────┐
│  PROJECTS   │
└─────────────┘
      │
      │ 1:N
      ↓
┌─────────────┐
│  REVENUES   │
└─────────────┘
```

```
┌──────────────────┐       1:N        ┌──────────────┐
│CONTRACT_TEMPLATES│─────────────────→│  CONTRACTS   │
└──────────────────┘                  └──────────────┘
                                              │
                                              │ N:1
                                              ↓
                                      ┌─────────────┐
                                      │   CLIENTS   │
                                      └─────────────┘
                                      ┌─────────────┐
                                      │  PROJECTS   │
                                      └─────────────┘
```

---

## 📋 Detalhamento das Entidades

### 1. CLIENTS (Centro do Sistema)

```
┌─────────────────────────────────────┐
│            CLIENTS                  │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ • name, company_name, email         │
│ • status (lead/client/churned)      │
│ • segment, industry                 │
│                                     │
│ === CAMPOS DE IA ===                │
│ • profile_summary (TEXT)            │
│ • sentiment_score (DECIMAL)         │
│ • health_score (INTEGER 0-100)      │
│ • churn_risk (low/medium/high)      │
│                                     │
│ === AGREGADOS FINANCEIROS ===       │
│ • lifetime_value (DECIMAL)          │
│ • total_spent (DECIMAL)             │
│ • average_project_value (DECIMAL)   │
└─────────────────────────────────────┘
```

**Relacionamentos**:
- **1:N** → `interactions` (histórico de comunicações)
- **1:N** → `sales_pipeline` (oportunidades de venda)
- **1:N** → `projects` (projetos ativos/históricos)
- **1:N** → `contracts` (contratos gerados)
- **1:N** → `revenues` (receitas recebidas)

---

### 2. INTERACTIONS (Preparada para RAG)

```
┌─────────────────────────────────────┐
│          INTERACTIONS               │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: client_id → clients.id          │
│                                     │
│ • type (meeting/email/call)         │
│ • subject, content (TEXT)           │
│                                     │
│ === VETORIZAÇÃO PARA IA ===         │
│ • content_embedding (VECTOR 1536)   │ ← OpenAI text-embedding-3-small
│                                     │
│ === METADADOS CONTEXTUAIS ===       │
│ • participants (JSONB)              │
│ • duration_minutes, location        │
│                                     │
│ === ANÁLISE DE IA ===               │
│ • sentiment_score (DECIMAL)         │
│ • key_topics (JSONB)                │
│ • action_items (JSONB)              │
│ • entities_mentioned (JSONB)        │
│                                     │
│ • is_positive, is_complaint         │
│ • requires_followup                 │
│ • urgency_level                     │
└─────────────────────────────────────┘
```

**Índices Especiais**:
- `idx_interactions_embedding` (IVFFLAT para busca vetorial)
- `idx_interactions_client` (Performance)
- `idx_interactions_date` (Queries temporais)

**Trigger**:
- `update_health_after_interaction` → Atualiza `clients.health_score` automaticamente

---

### 3. PROJECTS (Centro da Rentabilidade)

```
┌─────────────────────────────────────┐
│            PROJECTS                 │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: client_id → clients.id          │
│                                     │
│ • name, category (trafego/social)   │
│ • type (recurrent/one-time)         │
│ • status (planning/active/...)      │
│                                     │
│ === CONTRATO ===                    │
│ • contract_value (DECIMAL)          │
│ • payment_frequency                 │
│ • start_date, end_date              │
│                                     │
│ === RECORRÊNCIA ===                 │
│ • is_recurrent (BOOLEAN)            │
│ • recurrence_cycle (monthly/...)    │
│ • auto_renew (BOOLEAN)              │
│                                     │
│ === ANÁLISE DE RENTABILIDADE ===    │
│ • estimated_hours (DECIMAL)         │
│ • actual_hours (DECIMAL)            │
│ • profit_margin_target (%)          │
│ • actual_profit_margin (%)          │
└─────────────────────────────────────┘
```

**Relacionamentos**:
- **N:1** → `clients` (projeto pertence a um cliente)
- **1:N** → `project_tasks` (tarefas do projeto)
- **1:N** → `project_costs` (custos detalhados)
- **1:N** → `revenues` (receitas geradas)
- **1:N** → `contracts` (contratos vinculados)

---

### 4. PROJECT_COSTS (Rastreamento de Custos)

```
┌─────────────────────────────────────┐
│         PROJECT_COSTS               │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: project_id → projects.id        │
│ FK: expense_id → expenses.id (opt)  │
│                                     │
│ • cost_type (labor/tool/freelancer) │
│ • description, amount (DECIMAL)     │
│                                     │
│ === MÃO DE OBRA ===                 │
│ • hours_worked (DECIMAL)            │
│ • hourly_rate (DECIMAL)             │ ← Vem de users.hourly_cost
│                                     │
│ • date, notes                       │
└─────────────────────────────────────┘
```

**Uso em Views**:
- `project_profitability` → Calcula `total_costs` por projeto
- `client_lifetime_value` → Agrega custos por cliente

---

### 5. REVENUES (Contas a Receber)

```
┌─────────────────────────────────────┐
│            REVENUES                 │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: project_id → projects.id (opt)  │
│ FK: client_id → clients.id          │
│                                     │
│ • description, amount (DECIMAL)     │
│ • due_date, paid_date               │
│ • status (pending/paid/overdue)     │
│                                     │
│ • payment_method, invoice_number    │
└─────────────────────────────────────┘
```

**View Associada**: `project_profitability`  
**Filtro Importante**: Apenas `status = 'paid'` conta no lucro real

---

### 6. EXPENSES (Contas a Pagar)

```
┌─────────────────────────────────────┐
│            EXPENSES                 │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: project_id → projects.id (opt)  │
│                                     │
│ • category (ferramentas/freela)     │
│ • description, amount (DECIMAL)     │
│ • due_date, paid_date, status       │
│                                     │
│ === CLASSIFICAÇÃO ===               │
│ • is_fixed_cost (BOOLEAN)           │
│ • is_project_related (BOOLEAN)      │
│ • supplier                          │
└─────────────────────────────────────┘
```

**Diferença de `project_costs`**:
- `expenses`: Contas a pagar gerais (pode ou não ter projeto)
- `project_costs`: Sempre vinculado a projeto específico

---

### 7. CONTRACT_TEMPLATES (Sistema de Templates)

```
┌─────────────────────────────────────┐
│       CONTRACT_TEMPLATES            │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│                                     │
│ • name, category (trafego/social)   │
│ • content (TEXT com {{variáveis}})  │
│                                     │
│ === SCHEMA DE VALIDAÇÃO ===         │
│ • available_variables (JSONB)       │
│   {                                 │
│     "client_name": {                │
│       "type": "string",             │
│       "source": "clients.name",     │
│       "required": true              │
│     },                              │
│     "project_value": {...}          │
│   }                                 │
│                                     │
│ • optional_clauses (JSONB)          │
│ • version (INTEGER)                 │
│ • is_active (BOOLEAN)               │
└─────────────────────────────────────┘
```

---

### 8. CONTRACTS (Contratos Gerados)

```
┌─────────────────────────────────────┐
│           CONTRACTS                 │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│ FK: template_id → templates.id      │
│ FK: client_id → clients.id          │
│ FK: project_id → projects.id (opt)  │
│                                     │
│ • contract_number (UNIQUE)          │
│                                     │
│ === CONTEÚDO ===                    │
│ • content_html (TEXT renderizado)   │
│ • content_pdf_path (VARCHAR)        │
│                                     │
│ === AUDITORIA ===                   │
│ • variables_used (JSONB)            │ ← Dados usados na geração
│                                     │
│ • status (draft/sent/signed)        │
│ • generated_at, signed_at           │
│ • client_signature_url              │
│ • agency_signature_url              │
└─────────────────────────────────────┘
```

---

### 9. AI_INSIGHTS (Cache de IA)

```
┌─────────────────────────────────────┐
│          AI_INSIGHTS                │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│                                     │
│ • insight_type (churn_prediction)   │
│ • entity_type (client/project)      │
│ • entity_id (UUID do cliente/proj)  │
│                                     │
│ === INSIGHT ===                     │
│ • title, description (TEXT)         │
│ • confidence_score (DECIMAL 0-1)    │
│                                     │
│ • metadata (JSONB)                  │
│ • severity (info/warning/critical)  │
│ • suggested_actions (JSONB)         │
│                                     │
│ • is_resolved (BOOLEAN)             │
│ • valid_until (TIMESTAMP)           │
└─────────────────────────────────────┘
```

**Índices**:
- `idx_ai_insights_entity` → Busca por cliente/projeto
- `idx_ai_insights_unresolved` → Dashboard de alertas

---

### 10. KNOWLEDGE_BASE (RAG para Docs Internos)

```
┌─────────────────────────────────────┐
│        KNOWLEDGE_BASE               │
├─────────────────────────────────────┤
│ PK: id (UUID)                       │
│                                     │
│ • document_type (process/policy)    │
│ • title, content (TEXT)             │
│ • content_embedding (VECTOR 1536)   │
│                                     │
│ • tags (JSONB) ["pricing", "SOP"]   │
│ • category                          │
│ • version, is_active                │
└─────────────────────────────────────┘
```

**Uso**: IA busca procedimentos internos para responder perguntas da equipe

---

## 🔗 Fluxo de Dados Completo

### Jornada do Cliente (Lead → Fechamento → Execução)

```
1. Lead entra
   ↓
   INSERT INTO clients (status = 'lead')
   
2. Reuniões/Calls
   ↓
   INSERT INTO interactions (content + embedding)
   ↓
   TRIGGER: update_client_health_score()
   ↓
   clients.health_score atualizado
   
3. Oportunidade
   ↓
   INSERT INTO sales_pipeline (stage = 'proposal')
   
4. Venda ganha
   ↓
   UPDATE sales_pipeline SET stage = 'won'
   UPDATE clients SET status = 'client'
   
5. Projeto criado
   ↓
   INSERT INTO projects (contract_value, estimated_hours)
   
6. Contrato gerado
   ↓
   SELECT * FROM contract_templates WHERE category = 'trafego'
   ↓
   Renderiza variáveis (client_name, project_value)
   ↓
   INSERT INTO contracts (content_html, status = 'draft')
   ↓
   Gera PDF
   ↓
   UPDATE contracts SET status = 'sent'
   
7. Execução do projeto
   ↓
   INSERT INTO project_tasks (assigned_to, estimated_hours)
   ↓
   Time registra horas
   ↓
   UPDATE projects SET actual_hours += x
   
8. Custos lançados
   ↓
   INSERT INTO project_costs (cost_type = 'labor', hours_worked, hourly_rate)
   INSERT INTO project_costs (cost_type = 'tool', amount = 300) -- ferramenta
   INSERT INTO expenses (category = 'freelancer', project_id)
   ↓
   INSERT INTO project_costs FROM expenses (vincula custo ao projeto)
   
9. Receitas lançadas
   ↓
   INSERT INTO revenues (project_id, amount, due_date, status = 'pending')
   ↓
   Cliente paga
   ↓
   UPDATE revenues SET status = 'paid', paid_date = NOW()
   
10. Análise de rentabilidade
    ↓
    SELECT * FROM project_profitability WHERE project_id = xxx
    ↓
    Resultado: profit_margin = 15% (abaixo da meta de 40%)
    ↓
    IA gera insight
    ↓
    INSERT INTO ai_insights (
      insight_type = 'profitability_alert',
      title = 'Projeto X com margem 25pp abaixo da meta',
      suggested_actions = ['Renegociar escopo', 'Otimizar processos']
    )
```

---

## 📊 Views Principais

### project_profitability

**Colunas**:
- `project_id`, `project_name`, `client_name`
- `contract_value`
- `revenue_received` (apenas status = 'paid')
- `total_costs` (soma de `project_costs`)
- `profit` (receita - custos)
- `profit_margin_percent`
- `profit_per_hour` (lucro / horas trabalhadas)

**Query Base**:
```sql
SELECT 
    p.name,
    SUM(r.amount) FILTER (WHERE r.status = 'paid') AS revenue_received,
    SUM(pc.amount) AS total_costs,
    revenue_received - total_costs AS profit,
    (profit / revenue_received) * 100 AS profit_margin_percent
FROM projects p
LEFT JOIN revenues r ON r.project_id = p.id
LEFT JOIN project_costs pc ON pc.project_id = p.id
GROUP BY p.id
```

---

### client_lifetime_value

**Colunas**:
- `client_id`, `client_name`, `company_name`
- `total_projects`
- `total_revenue` (pago)
- `total_costs`
- `net_profit` (receita - custos)
- `average_project_value`
- `active_projects`
- `first_project_date`, `last_project_date`
- `relationship_months`

**Uso**:
```sql
-- Top 5 clientes mais lucrativos
SELECT client_name, net_profit
FROM client_lifetime_value
ORDER BY net_profit DESC
LIMIT 5;

-- Clientes com baixa rentabilidade
SELECT client_name, net_profit, total_projects
FROM client_lifetime_value
WHERE net_profit < 10000
  AND total_projects >= 3;
```

---

## 🎯 Índices de Performance

### Mais Importantes

```sql
-- RAG (busca vetorial)
CREATE INDEX idx_interactions_embedding 
ON interactions USING ivfflat (content_embedding vector_cosine_ops);

CREATE INDEX idx_knowledge_embedding 
ON knowledge_base USING ivfflat (content_embedding vector_cosine_ops);

-- Filtros comuns
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_health ON clients(health_score);
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_status ON projects(status);

-- Análise financeira
CREATE INDEX idx_revenues_project ON revenues(project_id);
CREATE INDEX idx_revenues_status ON revenues(status);
CREATE INDEX idx_project_costs_project ON project_costs(project_id);

-- Dashboard de IA
CREATE INDEX idx_ai_insights_entity ON ai_insights(entity_type, entity_id);
CREATE INDEX idx_ai_insights_unresolved ON ai_insights(is_resolved) 
WHERE is_resolved = FALSE;
```

---

## 🔧 Extensões PostgreSQL Necessárias

```sql
-- UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vetores para IA (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";
```

**Como instalar pgvector**:
```bash
# Via Docker (mais fácil)
docker run -d --name agency-os-db \
  -e POSTGRES_PASSWORD=senha \
  -p 5432:5432 \
  ankane/pgvector:latest

# Ou via apt (Ubuntu)
sudo apt install postgresql-15-pgvector
```

---

## 📐 Cardinalidades

| Relação | Cardinalidade | Exemplo |
|---------|---------------|---------|
| `clients` → `interactions` | 1:N | 1 cliente tem N reuniões |
| `clients` → `projects` | 1:N | 1 cliente tem N projetos |
| `projects` → `project_costs` | 1:N | 1 projeto tem N custos |
| `projects` → `revenues` | 1:N | 1 projeto tem N parcelas |
| `projects` → `project_tasks` | 1:N | 1 projeto tem N tarefas |
| `contract_templates` → `contracts` | 1:N | 1 template gera N contratos |
| `task_templates` → `project_tasks` | 1:N | 1 template cria N tarefas |
| `expenses` → `project_costs` | 1:N | 1 despesa pode ser rateada em N projetos |

---

## 🚨 Constraints Importantes

### Validações de Negócio

```sql
-- Sentiment score entre -1 e 1
CONSTRAINT valid_sentiment CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)

-- Health score entre 0 e 100
CHECK (health_score >= 0 AND health_score <= 100)

-- Probability da pipeline entre 0 e 100
CHECK (probability >= 0 AND probability <= 100)

-- Prevent delete de clientes com projetos ativos
FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT
```

---

## 📝 Resumo Visual

```
CLIENTES (Centro)
    ├── Interações (IA analisa sentimento)
    ├── Pipeline de Vendas
    └── Projetos
            ├── Tarefas (horas trabalhadas)
            ├── Custos (rastreamento detalhado)
            ├── Receitas (contas a receber)
            └── Contratos (gerados de templates)
                    
VIEWS
    ├── project_profitability (margem de lucro)
    └── client_lifetime_value (LTV)

IA
    ├── ai_insights (cache de análises)
    └── knowledge_base (RAG docs internos)
```

---

**Diagrama criado por**: Arquiteto de Software Sênior  
**Versão**: 1.0  
**Última atualização**: Janeiro 2026
