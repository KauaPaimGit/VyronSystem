# Vyron System

**Enterprise AI ERP - Sistema Inteligente de Gestão Empresarial**

**Versão:** 1.1.0 | **Última Atualização:** 29/01/2026

---

## ⚡ Início Rápido

### 1. Configure a API da OpenAI
Edite o arquivo `.env` e adicione sua chave:
```env
OPENAI_API_KEY=sk-proj-...sua-chave-aqui...
```

### 2. Inicie o Backend
```bash
uvicorn main:app --reload
```
Acesse: http://127.0.0.1:8000

### 3. Inicie o Frontend
```bash
cd frontend
streamlit run app.py
```
Acesse: http://localhost:8501

---

## 🎯 Visão Geral

O **Vyron System** é uma plataforma Enterprise AI ERP focada em eficiência operacional e inteligência de dados, projetada para empresas que precisam:

- Gerenciar clientes e vendas com **análise de sentimento por IA**
- Calcular **margem de lucro real** de cada projeto (receita vs custos detalhados)
- **Rastrear performance de campanhas** com métricas de marketing (CTR, CPC, CPL, Taxa de Conversão)
- Gerar **contratos automaticamente** a partir de templates
- **Entrada manual de dados** com memória RAG integrada
- Obter **insights preditivos** sobre churn, rentabilidade e saúde do negócio

---

## 📦 Módulos Principais

### 1️⃣ CRM Inteligente
- Cadastro de leads e clientes com funil de vendas
- **Diferencial**: Registro de interações (reuniões, calls) com análise de IA
- Campos preparados para RAG (Retrieval-Augmented Generation):
  - Embeddings vetoriais para busca semântica
  - Análise de sentimento automática
  - Extração de tópicos-chave e action items

### 2️⃣ Gestão de Projetos Híbrida
- Suporte para serviços **recorrentes** (Tráfego, Social Media)
- Suporte para serviços **pontuais** (Branding, Vídeo)
- Templates de tarefas por categoria
- Rastreamento de horas por projeto

### 3️⃣ Financeiro & ERP
- Fluxo de caixa completo (contas a pagar/receber)
- Vinculação de custos a projetos específicos
- Cálculo de **LTV (Lifetime Value)** por cliente
- Views de análise de rentabilidade
- **Exportação de relatórios em PDF**

### 4️⃣ Marketing Performance (NOVO 🆕)
- **Rastreamento de métricas**: Impressões, Cliques, Leads, Conversões
- **KPIs Automáticos**: CTR, CPC, CPL/CPA, Taxa de Conversão
- Suporte multi-plataforma (Google Ads, Meta Ads, TikTok, LinkedIn)
- Dashboard visual com análise de performance
- Comparação de campanhas por projeto

### 5️⃣ Entrada Manual de Dados (NOVO 🆕)
- **Interface completa** para lançamento direto de informações
- Formulários para: Projetos, Despesas, Métricas de Marketing
- **Memória RAG integrada**: Entrada manual gera logs para a IA
- Validação e feedback visual em tempo real

### 6️⃣ Gerador de Contratos
- Templates com variáveis dinâmicas (ex: `{{client_name}}`)
- Validação automática de campos obrigatórios
- Geração de PDF com dados do CRM/Projeto
- Versionamento e rastreabilidade

### 7️⃣ AI Brain (Preparado para LLM)
- Estrutura para conectar APIs de IA (OpenAI, Anthropic, etc)
- Cache de insights para evitar reprocessamento
- **Consulta unificada**: IA acessa dados manuais e automáticos
- Respostas à perguntas como:
  - *"Qual cliente é mais lucrativo vs qual dá mais trabalho?"*
  - *"Quais projetos têm margem abaixo da meta?"*
  - *"Qual campanha teve melhor taxa de conversão?"*
  - *"Quanto gastamos em marketing este mês?"*

---

## 🛠 Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | Python 3.11+ com FastAPI |
| **Database** | PostgreSQL 15+ com extensão pgvector |
| **IA/LLM** | OpenAI API (text-embedding-3-small, GPT-4o-mini) |
| **PDF Generation** | ReportLab |
| **Frontend** | Streamlit |
| **Validação** | Pydantic v2 |
| **Migrations** | SQL Scripts |

---

## 📂 Estrutura de Arquivos

```
SOG/
├── database_schema.sql       # Schema completo do banco de dados
├── architecture_docs.md      # Documentação técnica detalhada
├── CHANGELOG_v1.1.md        # Histórico de mudanças (v1.1)
├── README.md                 # Este arquivo
├── main.py                   # API FastAPI principal
├── requirements.txt          # Dependências Python
├── diagrams/
│   └── er_diagram.md         # Diagrama de Entidades e Relacionamentos
├── migrations/               # Scripts SQL de migrations
│   └── 001_add_marketing_metrics.sql
├── app/                      # Código da aplicação
│   ├── models.py            # Modelos SQLAlchemy ORM
│   ├── schemas.py           # Schemas Pydantic
│   ├── services.py          # Lógica de negócio
│   └── database.py          # Configuração do banco
├── frontend/                 # Interface Streamlit
│   ├── app.py               # Aplicação principal
│   └── requirements.txt     # Dependências do frontend
└── scripts/                  # Scripts utilitários
```

---

## 🚀 Como Começar

### 1. Criar o Banco de Dados

```bash
# Instalar PostgreSQL com pgvector (via Docker)
docker run -d \
  --name agency-os-db \
  -e POSTGRES_PASSWORD=senha_segura \
  -e POSTGRES_DB=agency_os \
  -p 5432:5432 \
  ankane/pgvector:latest

# Executar o schema principal
psql -h localhost -U postgres -d agency_os -f database_schema.sql

# Executar migrations (incluindo tabela de métricas de marketing)
psql -h localhost -U postgres -d agency_os -f migrations/001_add_marketing_metrics.sql
```

### 2. Instalar Dependências Python

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências do backend
pip install -r requirements.txt

# Instalar dependências do frontend
cd frontend
pip install -r requirements.txt
cd ..
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env`:

```env
DATABASE_URL=postgresql://postgres:senha_segura@localhost:5432/agency_os
OPENAI_API_KEY=sk-...
SECRET_KEY=sua_chave_secreta_aqui
```

### 4. Iniciar os Serviços

```bash
# Terminal 1: Iniciar Backend (API FastAPI)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Iniciar Frontend (Streamlit)
cd frontend
streamlit run app.py
```

### 5. Acessar a Aplicação

- **API Backend**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend (Streamlit)**: http://localhost:8501

---

## 🆕 Novidades da Versão 1.1.0

### ✍️ Entrada Manual de Dados
Interface completa para registrar informações sem depender do chat:

- **Formulário de Projetos**: Criar novos projetos com cliente e orçamento
- **Formulário de Despesas**: Registrar gastos vinculados a projetos
- **Formulário de Métricas**: Adicionar dados de campanhas de marketing

**Diferencial**: Todos os lançamentos manuais geram logs RAG para a IA consultar!

### 📊 Marketing Performance
Rastreamento completo de campanhas com KPIs automáticos:

**Métricas Rastreadas**:
- Impressões totais
- Cliques
- Leads gerados
- Conversões

**KPIs Calculados Automaticamente**:
- **CTR** (Click-Through Rate): Cliques / Impressões × 100
- **CPC** (Cost Per Click): Custo / Cliques
- **CPL/CPA** (Cost Per Lead): Custo / Leads
- **Taxa de Conversão**: Leads / Cliques × 100

**Endpoints Disponíveis**:
```
POST /manual/marketing-metrics  - Registrar métricas
GET  /projects/{id}/marketing-kpis - Obter KPIs calculados
```

### 📄 Exportação de Relatórios
Gere PDFs executivos com resumo financeiro completo:

```
GET /projects/{id}/export/pdf
```

**Conteúdo do PDF**:
- Dados do projeto e cliente
- Resumo financeiro (receitas, despesas, lucro, margem)
- Tabela detalhada de despesas
- Timestamp e informações de auditoria

---

## 📊 Exemplos de Queries Úteis

### Clientes em Risco de Churn
```sql
SELECT name, health_score, sentiment_score
FROM clients
WHERE status = 'client' AND health_score < 50
ORDER BY health_score ASC;
```

### Projetos com Margem Abaixo da Meta
```sql
SELECT project_name, profit_margin_percent, profit
FROM project_profitability
WHERE profit_margin_percent < 30
ORDER BY profit_margin_percent ASC;
```

### Top 5 Clientes por LTV
```sql
SELECT client_name, net_profit, total_projects
FROM client_lifetime_value
ORDER BY net_profit DESC
LIMIT 5;
```

### KPIs de Marketing por Projeto
```sql
SELECT 
    project_id,
    total_impressions,
    total_clicks,
    ctr_percentage,
    cpl as cost_per_lead
FROM marketing_kpis
WHERE month = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY conversion_rate_percentage DESC;
```

---

## 🧠 Funcionalidades de IA

### 1. Chat Inteligente com RAG
Converse naturalmente com a IA sobre seus dados:

**Exemplos de Perguntas**:
- "Qual projeto tem melhor taxa de conversão?"
- "Quanto gastamos em marketing este mês?"
- "Liste projetos com margem abaixo de 30%"
- "Qual cliente está com health score baixo?"

**Como Funciona**:
1. IA gera embedding da pergunta
2. Busca interações relevantes no banco (RAG)
3. Usa contexto para gerar resposta precisa
4. Pode executar ações (criar projeto, registrar despesa)

### 2. Function Calling (Automação)
A IA pode executar ações automaticamente:

```python
# Exemplo de conversa:
Usuário: "Crie um projeto de R$ 10.000 para a Empresa XYZ"
IA: [Executa create_project automaticamente]
IA: "✅ Projeto criado com sucesso! ID: abc-123..."
```

**Funções Disponíveis**:
- `create_project()` - Criar novo projeto
- `list_projects()` - Listar/buscar projetos
- `add_expense()` - Registrar despesa
- `add_marketing_stats()` - Adicionar métricas de marketing (em breve)

### 3. Análise de Sentimento (Interações)
Toda interação registrada pode ter seu sentimento analisado automaticamente:

```python
# Exemplo de integração
from openai import OpenAI
client = OpenAI(api_key="sua_key")

def analyze_sentiment(text: str) -> float:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "Analise o sentimento do texto e retorne um número de -1.0 (muito negativo) a 1.0 (muito positivo)."
        }, {
            "role": "user",
            "content": text
        }]
    )
    return float(response.choices[0].message.content)
```

### 2. Busca Semântica (RAG)
Encontre interações relevantes usando busca vetorial:

```python
def search_interactions(query: str, client_id: str = None):
    # 1. Gerar embedding da pergunta
    embedding = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding
    
    # 2. Buscar no banco
    sql = """
        SELECT content, subject, interaction_date
        FROM interactions
        WHERE (:client_id IS NULL OR client_id = :client_id)
        ORDER BY content_embedding <=> :embedding
        LIMIT 5
    """
    return db.execute(sql, {"embedding": embedding, "client_id": client_id})
```

### 3. Insights Automáticos
O sistema pode gerar insights baseados em dados:

- **Churn Prediction**: Clientes sem interação há 60+ dias + health_score baixo
- **Profitability Alert**: Projetos com margem < 20%
- **Upsell Opportunity**: Clientes fiéis (12+ meses) sem novos projetos

---

## 📈 KPIs e Métricas Disponíveis

| KPI | Fonte de Dados |
|-----|----------------|
| Taxa de Conversão (Lead → Cliente) | `sales_pipeline` |
| Ciclo Médio de Vendas | `sales_pipeline.days_in_pipeline` |
| LTV por Cliente | View `client_lifetime_value` |
| Margem de Lucro por Projeto | View `project_profitability` |
| MRR (Monthly Recurring Revenue) | `projects` + `revenues` (projetos recorrentes) |
| Health Score Médio | `clients.health_score` |
| Churn Rate | Clientes com status `churned` |

---

## 🔐 Segurança e Compliance

### LGPD (Lei Geral de Proteção de Dados)
- **Dados Sensíveis**: Campo `content` em `interactions` pode conter dados pessoais
- **Recomendação**: Implementar criptografia para dados sensíveis
- **Auditoria**: Todos os registros têm `created_by` e `created_at`

### Boas Práticas
- ✅ Senhas com bcrypt (nunca em texto puro)
- ✅ Soft delete (campo `deleted_at`) em vez de DELETE
- ✅ Backups automáticos do PostgreSQL
- ✅ Logs de acesso e modificações

---

## 🗺 Roadmap

### Fase 1: Banco de Dados ✅
- [x] Schema completo
- [x] Views de análise
- [x] Triggers de atualização automática

### Fase 2: Backend (Em Desenvolvimento)
- [ ] API FastAPI com autenticação JWT
- [ ] Endpoints CRUD para todos os módulos
- [ ] Integração OpenAI (embeddings + chat)
- [ ] Geração de contratos em PDF

### Fase 3: Frontend (Planejado)
- [ ] Dashboard executivo (React ou Streamlit)
- [ ] Interface de CRM
- [ ] Kanban de projetos
- [ ] Relatórios financeiros

### Fase 4: IA Avançada (Futuro)
- [ ] Chatbot interno para consultas
- [ ] Previsão de churn com ML
- [ ] Recomendação de pricing por projeto
- [ ] Análise de competitividade

---

## 📞 Suporte

Para dúvidas sobre a arquitetura, consulte:
- [architecture_docs.md](architecture_docs.md) - Documentação técnica detalhada
- [database_schema.sql](database_schema.sql) - Schema com comentários

---

## 📄 Licença

Uso interno - Todos os direitos reservados.

---

**Desenvolvido com ❤️ para otimizar agências de marketing digital**
