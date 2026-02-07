<div align="center">

# 🚀 Vyron System v1.1

### Enterprise AI ERP — Plataforma Modular de Gestão Inteligente

[![Status](https://img.shields.io/badge/Status-Produção-brightgreen?style=for-the-badge)]()
[![Version](https://img.shields.io/badge/Versão-1.1.0-blue?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Modular-009688?style=for-the-badge&logo=fastapi&logoColor=white)]()

**Arquitetura baseada em Domínios (DDD) com Inteligência Artificial Multimodal, RAG nativo e 29 endpoints distribuídos em 4 pilares funcionais.**  
**Sistema enterprise-grade para escalar operações de agências digitais com governança, rastreabilidade e inteligência contextual.**

</div>

---

## Índice

- [Arquitetura Modular v1.1](#arquitetura-modular-v11)
- [Tech Stack](#tech-stack)
- [Instalação e Configuração](#instalação-e-configuração)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Funcionalidades Principais](#funcionalidades-principais)
- [API REST — Endpoints por Módulo](#api-rest--endpoints-por-módulo)
- [Banco de Dados](#banco-de-dados)
- [Documentação Técnica](#documentação-técnica)

---

## 🏗️ Nova Arquitetura Modular (v1.1)

O **Vyron System v1.1** foi reestruturado para garantir **escalabilidade enterprise e isolamento de responsabilidades** através de uma arquitetura modular baseada em **Domain-Driven Design (DDD)** e **APIRouter (FastAPI)**. A nova estrutura reduz o acoplamento, facilita manutenção e permite escalabilidade horizontal com middleware de auditoria centralizado.

### Os 4 Pilares Funcionais

| Módulo | Responsabilidade | Endpoints |
|--------|------------------|-----------|
| **🚀 Growth & Sales** | Módulo de prospecção ativa (Radar B2B), Caçador de Leads, CRM Inteligente e gestão de interações com clientes | 12 endpoints |
| **🧠 Agency Brain** | Núcleo de IA unificado com RAG (Retrieval-Augmented Generation) para PDFs e imagens via `pgvector`, chat contextual e busca semântica | 6 endpoints |
| **💰 Finance & Ops** | Dashboards de ROI, Fluxo de Caixa, Kanban Visual, gestão de projetos, receitas, despesas e KPIs de marketing | 9 endpoints |
| **⚙️ System Core** | Autenticação JWT, Middleware de Auditoria (Logs de Rastreabilidade), diagnóstico de banco de dados e configurações | 2 endpoints + Middleware |

**Total:** 29 endpoints REST distribuídos em 4 routers modulares (`app/modules/`), com **middleware de auditoria** interceptando todas as operações de escrita (POST/PUT/PATCH/DELETE) e registrando em `audit_logs`.

---

## Tech Stack

| Camada | Tecnologia | Versão | Função |
|--------|------------|--------|--------|
| **Backend** | FastAPI | 0.109+ | API modular com APIRouter |
| **ORM** | SQLAlchemy | 2.x (sync) | Mapeamento objeto-relacional |
| **Database** | PostgreSQL 16 | + pgvector 0.5+ | Banco relacional + busca vetorial |
| **AI/ML** | OpenAI API | GPT-4o-mini + text-embedding-3-small | Chat + embeddings (1536 dims) |
| **Frontend** | Streamlit | 1.30+ | Interface web responsiva |
| **Containerização** | Docker | + Docker Compose | Orquestração de infraestrutura |
| **Python** | 3.11+ | CPython | Runtime principal |

---

## Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- PostgreSQL 16+ com extensão pgvector
- Docker e Docker Compose (recomendado)
- OpenAI API Key
- Git

### Passo 1 — Clone o repositório

```bash
git clone https://github.com/KauaPaimGit/VyronSystem.git
cd VyronSystem
```

### Passo 2 — Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Database
DATABASE_URL=postgresql://admin:password123@localhost:5432/agency_os

# OpenAI
OPENAI_API_KEY=sk-proj-...

# SerpAPI (Radar de Vendas)
SERPAPI_KEY=your_serpapi_key_here
```

### Passo 3 — Iniciar PostgreSQL com pgvector (Docker)

```bash
docker compose up -d db
```

> Aguarde ~10 segundos para o PostgreSQL inicializar completamente.

**Habilitar pgvector:**

```bash
docker exec agency_os_db psql -U admin -d agency_os -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Passo 4 — Executar migrations (Automação de Banco de Dados)

```bash
python scripts/run_migrations.py
```

> **⚡ Crítico:** Este comando automatiza a criação do banco de dados, habilitando as extensões `vector` e `uuid-ossp`, criando as **16 tabelas** (incluindo `audit_logs` e `document_chunks`) e os **índices vetoriais IVFFlat** necessários para o RAG. Essencial para garantir compatibilidade com ambientes sem console interativo (ex: Render.com).

### Passo 5 — Criar usuário admin

```bash
python scripts/_create_admin_quick.py
```

> Cria o usuário `admin` com senha `senha123`.

### Passo 6 — Instalar dependências Python

```bash
pip install -r requirements.txt
```

### Passo 7 — Iniciar o backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Passo 8 — Iniciar o frontend (novo terminal)

```bash
streamlit run frontend/app.py --server.port 8501
```

### Passo 9 — Ingestão de Conhecimento (Opcional)

Para alimentar o **Vyron Agency Brain** com documentos locais:

```bash
python scripts/ingest_document.py "caminho/do/seu/documento.pdf"
```

### Acessos

| Interface | URL |
|-----------|-----|
| **Frontend Streamlit** | `http://localhost:8501` |
| **API Backend** | `http://localhost:8000` |
| **Swagger Docs** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |

---

## Estrutura de Diretórios

```
VyronSystem/
├── main.py                      # Entrypoint FastAPI modular (~75 linhas)
├── requirements.txt             # Dependências Python
├── Dockerfile                   # Build da API
├── docker-compose.yml           # PostgreSQL + pgvector + API
├── .env                         # Variáveis de ambiente (não versionado)
│
├── app/
│   ├── models.py                # 16 modelos ORM (incluindo AuditLog, DocumentChunk)
│   ├── schemas.py               # Schemas Pydantic v2
│   ├── database.py              # Engine SQLAlchemy (sync)
│   ├── auth.py                  # bcrypt + autenticação
│   ├── services.py              # Serviços legados (em processo de modularização)
│   ├── brain_service.py         # RAG Engine (PDF → chunks → embeddings → pgvector)
│   │
│   ├── modules/                 # ⚡ Nova Arquitetura Modular v1.1
│   │   ├── auth/
│   │   │   └── router.py        # POST /login, GET /db-test
│   │   ├── sales/
│   │   │   └── router.py        # CRM, interações, Radar de Vendas
│   │   ├── brain/
│   │   │   └── router.py        # RAG multimodal (PDF + imagens)
│   │   └── finance/
│   │       └── router.py        # Projetos, receitas, despesas, KPIs
│   │
│   ├── middleware/
│   │   └── audit.py             # AuditMiddleware (intercepta POST/PUT/PATCH/DELETE)
│   │
│   └── services/
│       └── radar.py             # Google Maps B2B Scraper
│
├── frontend/
│   ├── app.py                   # Interface Streamlit v2.0 (1255 linhas)
│   └── app_backup.py            # Backup da versão anterior
│
├── docs/
│   ├── database_schema.sql      # Schema SQL completo
│   ├── architecture_docs.md     # Arquitetura detalhada
│   ├── AUTH_README.md
│   ├── RADAR_README.md
│   └── CHANGELOG_v1.1.md
│
├── scripts/
│   ├── run_migrations.py        # Executor de migrations via Python
│   ├── ingest_document.py       # CLI para ingestão de PDFs no RAG
│   ├── _create_admin_quick.py   # Criação rápida de admin (não-interativo)
│   └── create_admin.py          # Criação interativa de admin
│
└── migrations/
    ├── 001_add_marketing_metrics.sql
    ├── 002_add_product_price_to_projects.sql
    ├── 003_add_users_table.sql
    ├── 004_add_document_chunks.sql       # Tabela RAG + índice IVFFlat
    └── 005_add_audit_logs.sql            # Sistema de auditoria
```

---

## Funcionalidades Principais

### 🧠 Vyron Agency Brain — RAG System

O **Vyron Agency Brain** é o motor de inteligência do sistema — um pipeline de **Retrieval-Augmented Generation (RAG)** que processa documentos de forma contextual e escalável, combinando busca vetorial (pgvector) com modelos de linguagem (GPT-4o-mini) para fornecer respostas fundamentadas em conhecimento real.

#### Capacidades

| Recurso | Tecnologia | Descrição |
|---------|------------|-----------|
| **Ingestão de PDFs** | pypdf + langchain-text-splitters | Extração de texto, chunking semântico (500 tokens), geração de embeddings (1536 dims) |
| **Busca Semântica** | pgvector + IVFFlat | Consulta por similaridade de cosseno em espaço vetorial de alta dimensão |
| **Análise de Imagens** | GPT-4o Vision | Extração de informações de recibos, notas fiscais, documentos escaneados |
| **Chat Contextual** | OpenAI Chat API | Respostas fundamentadas em documentos reais + histórico de interações |
| **Knowledge Base** | PostgreSQL + Vector Index | Base de conhecimento persistente com versionamento de documentos |

#### Pipeline de Ingestão e Recuperação

```
📄 PDF Upload → Extração de Texto (pypdf) → Chunking Semântico (500 tokens) 
    → 🔢 Embeddings (text-embedding-3-small, 1536 dims) 
    → 💾 Armazenamento (document_chunks + pgvector)
    → 🔍 Busca por Similaridade (distância de cosseno via IVFFlat)
    → 🤖 Contexto para LLM → ✅ Resposta Fundamentada em Documentos Reais
```

#### Endpoints

- `POST /brain/upload` — Upload e ingestão automática de PDF
- `POST /brain/search` — Busca semântica em documentos indexados
- `POST /ai/chat` — Chat contextual com function calling
- `GET /brain/status` — Métricas da base de conhecimento (total de chunks, documentos, etc.)

---

### �️ Sistema de Auditoria Automática

O **AuditMiddleware** garante **conformidade e rastreabilidade total** de operações no sistema. Ele intercepta todas as requisições de escrita (POST, PUT, PATCH, DELETE) e registra automaticamente na tabela `audit_logs` os seguintes dados:

- **Timestamp** da operação
- **Método HTTP** e **path** acessado
- **Status code** da resposta
- **Duração** da requisição (em ms)
- **IP do cliente**
- **User-Agent** (opcional)

#### Cobertura

**16 tabelas auditadas:**
- `users`, `clients`, `projects`, `interactions`, `revenues`, `expenses`
- `marketing_metrics`, `document_chunks`, `kanban_cards`, e demais

#### Casos de Uso

- Compliance e rastreabilidade de alterações
- Debugging de operações críticas
- Análise de performance de endpoints
- Auditoria de segurança e acesso

---

### 📡 Radar de Vendas — Prospecção B2B Automatizada

Motor de inteligência comercial que utiliza a Google Maps API (via SerpAPI) para identificar e qualificar leads automaticamente.

#### Funcionalidades

- **Busca geolocalizada** por nicho (ex: "Pizzaria em São Paulo")
- **Extração estruturada** de dados de contato (telefone, website, email)
- **Conversão 1-click** para o CRM (cria cliente + projeto automaticamente)
- **Export Excel** com avaliações, endereço e dados de contato

#### Endpoints

- `GET /radar/search` — Busca empresas no Google Maps
- `POST /radar/convert` — Converte resultado em lead/projeto
- `GET /radar/export` — Gera planilha Excel para follow-up

---

### 💰 Dashboard Financeiro & KPIs de Marketing

Painel centralizado com cálculos automatizados de performance financeira e métricas de marketing digital.

#### Métricas Calculadas

| Métrica | Fórmula | Descrição |
|---------|---------|-----------|
| **CTR** | (Cliques ÷ Impressões) × 100 | Taxa de cliques |
| **CPC** | Custo Total ÷ Cliques | Custo por clique |
| **CPL** | Custo Total ÷ Leads | Custo por lead |
| **Conversion Rate** | (Conversões ÷ Leads) × 100 | Taxa de conversão |
| **ROI** | ((Receita − Custo) ÷ Custo) × 100 | Retorno sobre investimento |
| **Margem de Lucro** | (Receita − Despesas) ÷ Receita × 100 | Lucratividade líquida |

#### Recursos

- **Gráficos interativos** (Plotly)
- **Export PDF** dos relatórios financeiros
- **Comparação período a período**
- **Alertas de margem negativa**

---

## API REST — Endpoints por Módulo

### 🚀 Growth & Sales (`app/modules/sales/router.py`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/clients` | Criar cliente |
| `GET` | `/clients` | Listar clientes (com filtros) |
| `GET` | `/clients/{id}` | Detalhes do cliente |
| `PUT` | `/clients/{id}` | Atualizar cliente |
| `DELETE` | `/clients/{id}` | Remover cliente |
| `POST` | `/interactions/` | Registrar interação |
| `GET` | `/interactions/` | Listar interações |
| `GET` | `/clients/{id}/interactions` | Interações de um cliente |
| `GET` | `/radar/search` | Buscar empresas no Google Maps |
| `POST` | `/radar/convert` | Converter resultado em lead |
| `GET` | `/radar/export` | Exportar planilha Excel |

### 🧠 Agency Brain (`app/modules/brain/router.py`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/brain/upload` | Upload de PDF + ingestão automática |
| `POST` | `/brain/search` | Busca semântica em documentos |
| `POST` | `/brain/ingest` | Ingestão manual de arquivo |
| `GET` | `/brain/status` | Estatísticas da base RAG |
| `POST` | `/ai/chat` | Chat contextual com GPT-4o |
| `POST` | `/ai/search` | Busca híbrida (vetorial + keyword) |

### 💰 Finance & Ops (`app/modules/finance/router.py`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/projects/` | Criar projeto |
| `GET` | `/projects/` | Listar projetos |
| `GET` | `/projects/{id}` | Detalhes do projeto |
| `PATCH` | `/projects/{id}/status` | Atualizar status (Kanban) |
| `POST` | `/revenues/` | Registrar receita |
| `GET` | `/revenues/` | Listar receitas |
| `POST` | `/expenses/` | Registrar despesa |
| `GET` | `/expenses/` | Listar despesas |
| `GET` | `/projects/{id}/financial-dashboard` | Dashboard financeiro do projeto |
| `GET` | `/projects/{id}/marketing-kpis` | KPIs de marketing do projeto |
| `GET` | `/projects/{id}/export/pdf` | Exportar relatório PDF |
| `POST` | `/manual/projects` | Lançamento manual de projeto |
| `POST` | `/manual/expenses` | Lançamento manual de despesa |
| `POST` | `/manual/marketing-metrics` | Lançamento manual de métricas |

### ⚙️ System Core (`app/modules/auth/router.py`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/login` | Autenticação (retorna token) |
| `GET` | `/db-test` | Diagnóstico de banco + pgvector |

---

## Banco de Dados

### Schema — 16 Tabelas

```sql
-- Core
users, clients, projects, interactions

-- Financeiro
revenues, expenses, marketing_metrics

-- IA & Conhecimento
document_chunks (com vector(1536))

-- Auditoria
audit_logs

-- Kanban
kanban_cards

-- Outros
project_costs, roi_insights, ai_memory, radar_search_history, sentiment_scores, pricing_tiers
```

### Índices Vetoriais

```sql
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

> **IVFFlat:** Approximate Nearest Neighbor (ANN) search com 100 clusters para busca sub-linear em datasets grandes.

---

## Documentação Técnica

- **[Arquitetura Modular](docs/architecture_docs.md)** — Fluxo de dados, decisões de design, diagramas
- **[Autenticação](docs/AUTH_README.md)** — JWT, bcrypt, gerenciamento de sessões
- **[Radar de Vendas](docs/RADAR_README.md)** — Integração Google Maps, fluxo de conversão
- **[Changelog v1.1](docs/CHANGELOG_v1.1.md)** — Histórico de mudanças da v1.1
- **[Schema SQL](docs/database_schema.sql)** — DDL completo de todas as tabelas

---

## Roadmap

- [ ] **Módulo de Relatórios Agendados** — Export automático de dashboards via cron
- [ ] **Webhooks para eventos de CRM** — Integração com Zapier/Make
- [ ] **Multi-tenant** — Suporte a múltiplas agências em uma instância
- [ ] **Autenticação OAuth2** — Login com Google/Microsoft
- [ ] **Análise Preditiva** — Churn prediction com scikit-learn
- [ ] **Dashboard Mobile** — PWA + React Native

---

<div align="center">

---

**Desenvolvido por [Kauã Pereira Paim](https://github.com/KauaPaimGit) — 2026**

**Proprietário — Todos os direitos reservados.**

</div>
