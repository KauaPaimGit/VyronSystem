# Agency OS - Documentação da Arquitetura de Dados

## 📋 Visão Geral

Este documento descreve as decisões arquiteturais do banco de dados do **Agency OS**, focando em três pilares fundamentais:

1. **Preparação para IA (RAG - Retrieval-Augmented Generation)**
2. **Análise de Rentabilidade (Margem de Lucro Real)**
3. **Sistema de Templates Dinâmicos (Geração de Contratos)**

---

## 🧠 1. Estrutura para IA e RAG

### 1.1 Tabela `interactions` - Design para Consumo por IA

**Problema**: Como estruturar dados de reuniões/notas para que uma LLM possa:
- Buscar contexto relevante (semantic search)
- Analisar sentimento
- Extrair entidades e tópicos-chave
- Gerar insights acionáveis

**Solução Implementada**:

```sql
CREATE TABLE interactions (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    type VARCHAR(50), -- meeting, email, call, whatsapp, note
    
    -- CORE RAG: Conteúdo bruto + Embedding
    content TEXT NOT NULL, -- Transcrição completa
    content_embedding VECTOR(1536), -- OpenAI text-embedding-3-small
    
    -- METADADOS CONTEXTUAIS
    subject VARCHAR(255),
    participants JSONB, -- ["João Silva", "Maria CEO"]
    duration_minutes INTEGER,
    interaction_date TIMESTAMP,
    
    -- ANÁLISE DE IA (pré-computada)
    sentiment_score DECIMAL(3,2), -- -1.0 a 1.0
    key_topics JSONB, -- ["pricing", "timeline", "concerns"]
    action_items JSONB, -- [{"task": "enviar proposta", "deadline": "2026-01-20"}]
    entities_mentioned JSONB, -- ["Google Ads", "Instagram", "Concorrente X"]
    
    -- CLASSIFICAÇÃO AUTOMÁTICA
    is_complaint BOOLEAN,
    requires_followup BOOLEAN,
    urgency_level VARCHAR(20) -- low, medium, high, critical
);

-- Índice vetorial para busca semântica
CREATE INDEX idx_interactions_embedding 
ON interactions USING ivfflat (content_embedding vector_cosine_ops);
```

#### Por que essa estrutura?

**Campo `content`**: Mantém o texto original completo para:
- Re-embedding se mudar o modelo de IA
- Auditoria e contexto humano
- Fine-tuning futuro

**Campo `content_embedding`**: Usa o tipo `VECTOR` da extensão **pgvector**:
- Permite busca por similaridade semântica (não apenas keywords)
- Exemplo de query RAG:
  ```sql
  SELECT content, sentiment_score
  FROM interactions
  WHERE client_id = 'xxx'
  ORDER BY content_embedding <=> '[embedding_da_pergunta]'
  LIMIT 5;
  ```

**Campos JSONB**: Flexibilidade para evoluir sem alterar schema:
- `key_topics`: IA pode detectar novos tópicos sem adicionar colunas
- `action_items`: Estrutura variável (task, responsável, deadline)

**Análise Pré-computada**: Evita processar toda vez que acessar:
- `sentiment_score`: Atualiza health_score do cliente via trigger
- `urgency_level`: Prioriza follow-ups automaticamente

---

### 1.2 Tabela `knowledge_base` - RAG com Documentos Internos

```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY,
    document_type VARCHAR(100), -- process, policy, best_practice, case_study
    title VARCHAR(255),
    content TEXT NOT NULL, -- Seu SOP, processo de onboarding, etc
    content_embedding VECTOR(1536),
    tags JSONB, -- ["social_media", "pricing", "onboarding"]
    is_active BOOLEAN DEFAULT TRUE
);
```

**Caso de Uso**: Quando a IA precisa responder "Como fazemos onboarding de clientes de tráfego?":
1. Faz busca vetorial em `knowledge_base` com o embedding da pergunta
2. Recupera os 3 documentos mais relevantes
3. Usa como contexto para responder (RAG pattern)

---

### 1.3 Tabela `ai_insights` - Cache de Análises

```sql
CREATE TABLE ai_insights (
    id UUID PRIMARY KEY,
    insight_type VARCHAR(100), -- client_health, churn_prediction, profitability_alert
    entity_type VARCHAR(50), -- client, project, financial
    entity_id UUID, -- ID do cliente/projeto analisado
    
    title VARCHAR(255), -- "Cliente XPTO mostra sinais de churn"
    description TEXT, -- Explicação detalhada
    confidence_score DECIMAL(3,2), -- Confiança da IA (0.0 a 1.0)
    
    metadata JSONB, -- Dados usados na análise (para explicabilidade)
    severity VARCHAR(20), -- info, warning, critical
    suggested_actions JSONB, -- ["Agendar reunião", "Oferecer desconto"]
    
    is_resolved BOOLEAN DEFAULT FALSE,
    valid_until TIMESTAMP -- Insights expiram (ex: análise mensal)
);
```

**Vantagens**:
- **Performance**: Não recalcula análises caras toda vez
- **Histórico**: Vê evolução dos insights ao longo do tempo
- **Alertas**: Interface pode mostrar apenas insights não resolvidos

---

## 💰 2. Estrutura Financeiro ↔ Projeto (Margem de Lucro Real)

### 2.1 Problema a Resolver

**Pergunta**: "Quanto realmente ganhamos com cada projeto depois de pagar ferramentas, freelancers e contar as horas da equipe?"

**Desafio**: Ligar receitas, custos diretos e custos indiretos ao projeto.

### 2.2 Arquitetura Implementada

#### Tabela `projects`
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    contract_value DECIMAL(12,2), -- Valor que o cliente paga
    
    -- Análise de rentabilidade
    estimated_hours DECIMAL(8,2),
    actual_hours DECIMAL(8,2) DEFAULT 0, -- Rastreado via tasks
    profit_margin_target DECIMAL(5,2), -- % esperada (ex: 40%)
    actual_profit_margin DECIMAL(5,2) -- % real (calculada)
);
```

#### Tabela `revenues` (Contas a Receber)
```sql
CREATE TABLE revenues (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id), -- VÍNCULO DIRETO
    client_id UUID REFERENCES clients(id),
    amount DECIMAL(12,2),
    status VARCHAR(50) -- pending, paid, overdue
);
```

#### Tabela `expenses` (Contas a Pagar)
```sql
CREATE TABLE expenses (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id), -- CHAVE: Liga custo ao projeto
    category VARCHAR(100), -- ferramentas, freelancer, infraestrutura
    amount DECIMAL(12,2),
    is_fixed_cost BOOLEAN, -- Diferencia fixo (escritório) vs variável (ads)
    is_project_related BOOLEAN -- Se FALSE, é overhead geral
);
```

#### Tabela `project_costs` (Detalhamento de Custos)
```sql
CREATE TABLE project_costs (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    expense_id UUID REFERENCES expenses(id), -- Rastreabilidade
    
    cost_type VARCHAR(100), -- labor, tool, freelancer, ads_budget
    amount DECIMAL(12,2),
    
    -- Para custos de mão de obra
    hours_worked DECIMAL(8,2),
    hourly_rate DECIMAL(10,2), -- Vem de users.hourly_cost
    
    date DATE
);
```

### 2.3 View de Análise: `project_profitability`

```sql
CREATE VIEW project_profitability AS
SELECT 
    p.name AS project_name,
    p.contract_value,
    
    -- Total RECEBIDO (apenas status = 'paid')
    SUM(r.amount) FILTER (WHERE r.status = 'paid') AS revenue_received,
    
    -- Total de CUSTOS
    SUM(pc.amount) AS total_costs,
    
    -- LUCRO LÍQUIDO
    SUM(r.amount) FILTER (WHERE r.status = 'paid') - SUM(pc.amount) AS profit,
    
    -- MARGEM PERCENTUAL
    ((SUM(r.amount) FILTER (WHERE r.status = 'paid') - SUM(pc.amount)) / 
     SUM(r.amount) FILTER (WHERE r.status = 'paid')) * 100 AS profit_margin_percent,
    
    -- EFICIÊNCIA (lucro por hora trabalhada)
    (SUM(r.amount) FILTER (WHERE r.status = 'paid') - SUM(pc.amount)) / 
    NULLIF(p.actual_hours, 0) AS profit_per_hour

FROM projects p
LEFT JOIN revenues r ON r.project_id = p.id
LEFT JOIN project_costs pc ON pc.project_id = p.id
GROUP BY p.id;
```

### 2.4 Fluxo de Dados

**Cenário: Projeto de Tráfego Pago**

1. **Projeto criado**: `contract_value = R$ 5.000/mês`
2. **Custos registrados em `project_costs`**:
   - `cost_type = 'labor'`: 20h × R$ 80/h = R$ 1.600 (designer)
   - `cost_type = 'labor'`: 15h × R$ 120/h = R$ 1.800 (gestor tráfego)
   - `cost_type = 'tool'`: R$ 300 (assinatura ferramenta)
   - `cost_type = 'ads_budget'`: R$ 500 (budget de anúncios)
   - **Total custos**: R$ 4.200

3. **Receita registrada em `revenues`**:
   - `status = 'paid'`: R$ 5.000

4. **View calcula**:
   - **Profit**: R$ 5.000 - R$ 4.200 = R$ 800
   - **Margin**: 16% (bem abaixo da meta de 40% → alerta!)
   - **Profit per hour**: R$ 800 / 35h = R$ 22,86/h

**IA pode alertar**: "Projeto XPTO tem margem de 16%, 24pp abaixo da meta. Sugestão: renegociar valor ou otimizar processos."

---

### 2.5 View `client_lifetime_value`

```sql
CREATE VIEW client_lifetime_value AS
SELECT 
    c.name AS client_name,
    COUNT(DISTINCT p.id) AS total_projects,
    SUM(r.amount) FILTER (WHERE r.status = 'paid') AS total_revenue,
    SUM(pc.amount) AS total_costs,
    SUM(r.amount) FILTER (WHERE r.status = 'paid') - SUM(pc.amount) AS net_profit,
    
    -- TICKET MÉDIO
    SUM(r.amount) FILTER (WHERE r.status = 'paid') / COUNT(DISTINCT p.id) AS avg_project_value,
    
    -- TEMPO DE RELACIONAMENTO
    EXTRACT(MONTH FROM AGE(MAX(p.start_date), MIN(p.start_date))) AS relationship_months

FROM clients c
LEFT JOIN projects p ON p.client_id = c.id
LEFT JOIN revenues r ON r.project_id = p.id
LEFT JOIN project_costs pc ON pc.project_id = p.id
GROUP BY c.id;
```

**Pergunta que responde**: "Qual cliente é mais lucrativo vs qual dá mais trabalho?"

**Exemplo de análise**:
- Cliente A: R$ 50k receita, R$ 30k custos, 8 meses → **Ótimo!**
- Cliente B: R$ 60k receita, R$ 58k custos, 12 meses → **Problema!**

---

## 📄 3. Sistema de Templates Dinâmicos (Contratos)

### 3.1 Tabela `contract_templates`

```sql
CREATE TABLE contract_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255), -- "Contrato Tráfego Pago Mensal"
    category VARCHAR(100), -- trafego, social, branding
    
    -- CONTEÚDO COM VARIÁVEIS
    content TEXT, -- HTML/Markdown com {{variáveis}}
    
    -- SCHEMA DAS VARIÁVEIS (validação)
    available_variables JSONB
    /*
    {
      "client_name": {
        "type": "string",
        "source": "clients.name",
        "required": true
      },
      "project_value": {
        "type": "decimal",
        "source": "projects.contract_value",
        "required": true,
        "format": "currency"
      },
      "start_date": {
        "type": "date",
        "source": "projects.start_date",
        "required": true,
        "format": "DD/MM/YYYY"
      },
      "payment_method": {
        "type": "enum",
        "source": "manual",
        "options": ["PIX", "Boleto", "Cartão"],
        "required": false
      },
      "custom_clause": {
        "type": "text",
        "source": "manual",
        "required": false
      }
    }
    */
);
```

### 3.2 Exemplo de Template (campo `content`)

```html
<h1>CONTRATO DE PRESTAÇÃO DE SERVIÇOS - TRÁFEGO PAGO</h1>

<p>Pelo presente instrumento particular, de um lado:</p>
<p><strong>CONTRATANTE:</strong> {{client_name}}, empresa {{company_name}}, 
   inscrita no CNPJ {{client_cnpj}}, com sede em {{client_address}}.</p>

<p><strong>CONTRATADA:</strong> [SUA AGÊNCIA], inscrita no CNPJ ...</p>

<h2>CLÁUSULA 1ª - OBJETO</h2>
<p>A CONTRATADA prestará serviços de gerenciamento de tráfego pago 
   (Google Ads, Meta Ads) conforme escopo do projeto {{project_name}}.</p>

<h2>CLÁUSULA 2ª - VALOR E PAGAMENTO</h2>
<p>O valor mensal dos serviços é de {{project_value}} ({{project_value_extenso}}), 
   a ser pago todo dia {{payment_day}} via {{payment_method}}.</p>

<h2>CLÁUSULA 3ª - VIGÊNCIA</h2>
<p>Este contrato tem vigência de {{start_date}} a {{end_date}}, 
   renovável automaticamente {{#if auto_renew}}por igual período{{/if}}.</p>

{{#if custom_clause}}
<h2>CLÁUSULA ESPECIAL</h2>
<p>{{custom_clause}}</p>
{{/if}}

<p>Data: {{contract_date}}</p>
<p>_______________________<br>{{client_name}}</p>
<p>_______________________<br>[SUA AGÊNCIA]</p>
```

### 3.3 Tabela `contracts` (Contratos Gerados)

```sql
CREATE TABLE contracts (
    id UUID PRIMARY KEY,
    template_id UUID REFERENCES contract_templates(id),
    client_id UUID REFERENCES clients(id),
    project_id UUID REFERENCES projects(id),
    
    contract_number VARCHAR(100) UNIQUE, -- "CTR-2026-001"
    
    -- CONTEÚDO FINAL (após substituir variáveis)
    content_html TEXT, -- HTML renderizado
    content_pdf_path VARCHAR(500), -- /storage/contracts/CTR-2026-001.pdf
    
    -- VARIÁVEIS USADAS (auditoria)
    variables_used JSONB,
    /*
    {
      "client_name": "XPTO Ltda",
      "project_value": "5000.00",
      "start_date": "2026-02-01",
      "payment_method": "PIX",
      "custom_clause": "Cliente terá acesso ao painel em tempo real"
    }
    */
    
    status VARCHAR(50), -- draft, sent, signed, active
    generated_at TIMESTAMP,
    signed_at TIMESTAMP
);
```

### 3.4 Fluxo de Geração (Backend FastAPI)

```python
# Pseudo-código do endpoint
@app.post("/contracts/generate")
async def generate_contract(
    template_id: UUID,
    client_id: UUID,
    project_id: UUID,
    custom_variables: dict
):
    # 1. Busca template
    template = db.query(ContractTemplate).get(template_id)
    
    # 2. Busca dados do cliente e projeto
    client = db.query(Client).get(client_id)
    project = db.query(Project).get(project_id)
    
    # 3. Monta dicionário de variáveis
    variables = {
        "client_name": client.name,
        "company_name": client.company_name,
        "project_value": format_currency(project.contract_value),
        "start_date": project.start_date.strftime("%d/%m/%Y"),
        **custom_variables  # Sobrescreve/adiciona valores manuais
    }
    
    # 4. Valida contra available_variables
    validate_variables(template.available_variables, variables)
    
    # 5. Renderiza template (usa Jinja2 ou similar)
    content_html = render_template(template.content, variables)
    
    # 6. Gera PDF (usa WeasyPrint ou similar)
    pdf_path = generate_pdf(content_html)
    
    # 7. Salva contrato
    contract = Contract(
        template_id=template_id,
        client_id=client_id,
        project_id=project_id,
        contract_number=generate_contract_number(),
        content_html=content_html,
        content_pdf_path=pdf_path,
        variables_used=variables,
        status="draft"
    )
    db.add(contract)
    db.commit()
    
    return {"contract_id": contract.id, "pdf_url": pdf_path}
```

### 3.5 Vantagens do Sistema

✅ **Reutilização**: Cria template 1x, usa N vezes  
✅ **Consistência**: Todos os contratos seguem mesmo padrão legal  
✅ **Rastreabilidade**: `variables_used` mostra exatamente o que foi usado  
✅ **Versionamento**: Campo `version` em templates permite evoluir contratos  
✅ **Auditoria**: Sabe quem gerou, quando, e com quais dados  

---

## 🔗 4. Integrações Entre Módulos

### 4.1 Fluxo de Dados: Lead → Cliente → Projeto → Contrato → Financeiro

```
1. Lead entra no sistema (CRM)
   ↓
2. Interações registradas (meetings, calls) → IA analisa sentimento
   ↓
3. Lead vira cliente (status = 'client')
   ↓
4. Projeto criado (projects) → Contrato gerado (contracts)
   ↓
5. Tarefas criadas (project_tasks) → Horas registradas
   ↓
6. Custos lançados (project_costs) → Receitas lançadas (revenues)
   ↓
7. Views calculam: profit_margin, LTV, health_score
   ↓
8. IA gera insights (ai_insights) → "Margem baixa, renegociar?"
```

### 4.2 Trigger: Atualização Automática de Health Score

```sql
CREATE TRIGGER update_health_after_interaction
AFTER INSERT OR UPDATE ON interactions
FOR EACH ROW 
EXECUTE FUNCTION update_client_health_score();
```

**Como funciona**:
1. Nova interação registrada com `sentiment_score = -0.7` (negativo)
2. Trigger calcula média dos últimos 90 dias
3. Atualiza `clients.health_score` e `clients.sentiment_score`
4. Se health_score < 30, IA cria insight tipo `churn_prediction`

---

## 🚀 5. Queries Úteis para o "AI Brain"

### 5.1 Clientes em Risco de Churn

```sql
SELECT 
    c.name,
    c.health_score,
    c.sentiment_score,
    COUNT(i.id) AS interactions_last_30days,
    MAX(i.interaction_date) AS last_contact
FROM clients c
LEFT JOIN interactions i ON i.client_id = c.id 
    AND i.interaction_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE c.status = 'client'
GROUP BY c.id
HAVING 
    c.health_score < 50 
    OR MAX(i.interaction_date) < CURRENT_DATE - INTERVAL '60 days'
ORDER BY c.health_score ASC;
```

### 5.2 Projetos com Margem Abaixo da Meta

```sql
SELECT 
    pp.project_name,
    pp.client_name,
    pp.profit_margin_percent,
    p.profit_margin_target,
    pp.profit_margin_percent - p.profit_margin_target AS margin_gap
FROM project_profitability pp
JOIN projects p ON pp.project_id = p.id
WHERE p.status = 'active'
  AND pp.profit_margin_percent < p.profit_margin_target
ORDER BY margin_gap ASC;
```

### 5.3 Top 5 Clientes por LTV (Mais Lucrativos)

```sql
SELECT 
    client_name,
    total_revenue,
    total_costs,
    net_profit,
    relationship_months,
    net_profit / NULLIF(relationship_months, 0) AS profit_per_month
FROM client_lifetime_value
WHERE total_projects > 0
ORDER BY net_profit DESC
LIMIT 5;
```

### 5.4 Busca Semântica (RAG) - Encontrar Interações Relevantes

```sql
-- Exemplo: "Quais clientes reclamaram de prazos?"
SELECT 
    c.name AS client_name,
    i.subject,
    i.content,
    i.sentiment_score,
    i.interaction_date
FROM interactions i
JOIN clients c ON i.client_id = c.id
WHERE i.content_embedding <=> '[embedding_da_pergunta]'::vector < 0.3
  AND i.is_complaint = TRUE
ORDER BY i.content_embedding <=> '[embedding_da_pergunta]'::vector
LIMIT 10;
```

---

## 📊 6. Extensões PostgreSQL Necessárias

### 6.1 Instalação

```sql
-- UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vetores para RAG (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";
```

### 6.2 pgvector - Configuração

**Instalação (Linux/Docker)**:
```bash
# Via Docker (recomendado)
docker run -d \
  --name agency-os-db \
  -e POSTGRES_PASSWORD=senha_segura \
  -p 5432:5432 \
  ankane/pgvector:latest
```

**Ou via apt (Ubuntu)**:
```bash
sudo apt install postgresql-15-pgvector
```

**Depois no SQL**:
```sql
CREATE EXTENSION vector;

-- Teste
SELECT '[1,2,3]'::vector;
```

---

## 🎯 7. Próximos Passos (Implementação Backend)

### 7.1 Estrutura de Pastas Sugerida (FastAPI)

```
agency-os/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── interaction.py
│   │   ├── contract.py
│   │   └── financial.py
│   ├── schemas/
│   │   └── (pydantic schemas)
│   ├── routers/
│   │   ├── crm.py
│   │   ├── projects.py
│   │   ├── financial.py
│   │   ├── contracts.py
│   │   └── ai.py
│   ├── services/
│   │   ├── ai_service.py (OpenAI API, embeddings)
│   │   ├── pdf_service.py (WeasyPrint)
│   │   └── analytics_service.py
│   └── utils/
│       ├── template_renderer.py
│       └── embeddings.py
├── alembic/ (migrations)
├── requirements.txt
└── .env
```

### 7.2 Bibliotecas Python Recomendadas

```txt
# requirements.txt
fastapi[all]==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# IA e Embeddings
openai==1.10.0
langchain==0.1.5
pgvector==0.2.4

# Geração de PDF
weasyprint==60.2
jinja2==3.1.3

# Análise de dados
pandas==2.2.0
numpy==1.26.3

# Validação
pydantic==2.5.3
pydantic-settings==2.1.0

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

### 7.3 Configuração OpenAI (embeddings.py)

```python
from openai import OpenAI
import numpy as np

client = OpenAI(api_key="sua_key")

def generate_embedding(text: str) -> list[float]:
    """Gera embedding vetorial do texto para RAG"""
    response = client.embeddings.create(
        model="text-embedding-3-small",  # 1536 dimensões
        input=text
    )
    return response.data[0].embedding

def semantic_search(query: str, table: str, limit: int = 5):
    """Busca semântica usando pgvector"""
    query_embedding = generate_embedding(query)
    
    # Query SQL com pgvector
    sql = f"""
        SELECT *, content_embedding <=> %s AS distance
        FROM {table}
        ORDER BY distance
        LIMIT %s
    """
    return db.execute(sql, (query_embedding, limit))
```

---

## 📈 8. Métricas-Chave que o Sistema Responde

### Para Gestão Comercial:
- ✅ Qual o LTV médio dos clientes?
- ✅ Qual o ticket médio por tipo de serviço?
- ✅ Quantos leads viram clientes (taxa de conversão)?
- ✅ Qual o ciclo de vendas médio (days_in_pipeline)?

### Para Gestão Financeira:
- ✅ Qual a margem de lucro real por projeto?
- ✅ Qual serviço é mais lucrativo (tráfego vs social vs branding)?
- ✅ Quanto custa cada hora de trabalho?
- ✅ Qual a projeção de receita recorrente (MRR)?

### Para Gestão de Clientes:
- ✅ Quais clientes estão em risco de churn?
- ✅ Qual cliente tem melhor ROI (menos trabalho, mais lucro)?
- ✅ Quais são os principais problemas relatados?
- ✅ Qual o sentimento geral nas interações?

### Para IA:
- ✅ "Me mostre clientes similares a [Cliente X]" (busca vetorial)
- ✅ "Quais foram os principais tópicos discutidos nas reuniões?" (key_topics)
- ✅ "Liste projetos onde mencionaram orçamento" (semantic search)

---

## 🔐 9. Considerações de Segurança

1. **Dados Sensíveis**: Nunca armazene senhas em texto puro (use bcrypt)
2. **LGPD**: Campo `content` em `interactions` pode conter dados pessoais → considere criptografia
3. **Auditoria**: Campos `created_by` permitem rastrear quem fez o quê
4. **Soft Delete**: Adicione campo `deleted_at` em vez de DELETE real
5. **Backups**: Configure backup automático do PostgreSQL (dados críticos do negócio)

---

## 📝 10. Resumo Executivo

### Diferencial 1: RAG-Ready
- Embeddings vetoriais em `interactions` e `knowledge_base`
- Busca semântica nativa no PostgreSQL
- Análise de sentimento e extração de entidades

### Diferencial 2: Análise Financeira Profunda
- Margem de lucro **real** por projeto (custos diretos + indiretos)
- LTV calculado com receita **vs custos** (não só receita bruta)
- Views otimizadas para dashboards executivos

### Diferencial 3: Contratos Inteligentes
- Sistema de templates com validação de variáveis
- Rastreabilidade completa (quem gerou, quando, com quais dados)
- Versionamento para evolução do negócio

### Próximo: Backend + IA
- Implementar API FastAPI
- Conectar OpenAI para embeddings e insights
- Criar dashboards (Streamlit ou React)

---

**Documentação criada por**: Arquiteto de Software Sênior  
**Data**: Janeiro 2026  
**Versão**: 1.0  
**Stack**: PostgreSQL + FastAPI + OpenAI
