<div align="center">

# Vyron System

### Enterprise AI ERP — Gestão Inteligente de Agências

`v1.0.0`

[![Status](https://img.shields.io/badge/Status-Produção-brightgreen?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)]()
[![AI](https://img.shields.io/badge/AI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)]()

---

**Plataforma ERP com inteligência artificial embarcada, projetada para escalar operações de agências digitais.**
**CRM, Financeiro, Marketing, Prospecção B2B e IA contextual (RAG) em um único sistema.**

</div>

---

## Índice

- [Descrição Executiva](#descrição-executiva)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Tech Stack](#tech-stack)
- [Instalação](#instalação)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Módulos do Sistema](#módulos-do-sistema)
- [API REST](#api-rest)
- [Banco de Dados](#banco-de-dados)
- [Documentação](#documentação)
- [Roadmap](#roadmap)
- [Licença](#licença)

---

## Descrição Executiva

O **Vyron System** é uma plataforma Enterprise AI ERP que consolida **10 módulos funcionais**, **50+ endpoints REST**, **18 tabelas** relacionais com suporte vetorial (pgvector) e **RAG nativo** para inteligência artificial contextual.

Projetado para agências digitais que precisam de:

- **Visão 360° do cliente** — CRM com Health Score, Sentiment Analysis e LTV automatizados.
- **Controle financeiro granular** — Receitas, despesas, custos por projeto e margem de lucro em tempo real.
- **Performance de marketing mensurável** — KPIs calculados automaticamente (CTR, CPC, CPL, ROI).
- **Automação via IA** — Chat com Function Calling que executa ações no sistema por linguagem natural.
- **Prospecção ativa** — Radar de Vendas integrado com Google Maps para captação B2B.

---

## Funcionalidades Principais

### Agency Brain — Inteligência Artificial com RAG

O núcleo de IA do Vyron System. Utiliza **Retrieval-Augmented Generation** com embeddings armazenados via pgvector para fornecer respostas contextuais baseadas nos dados reais da operação.

| Capacidade | Descrição |
|---|---|
| **Chat Contextual** | Busca semântica em interações, projetos e histórico de clientes |
| **Multimodal** | Suporte a envio de imagens e PDFs para análise |
| **Function Calling** | Criação de projetos, registro de despesas e consultas via linguagem natural |
| **Knowledge Base** | Base de conhecimento interna com versionamento de documentos |
| **Insights Automatizados** | Alertas de churn, saúde do cliente e rentabilidade |

### Módulo Radar — Prospecção B2B

Motor de prospecção ativa que conecta diretamente ao Google Maps para identificar oportunidades de negócio.

| Capacidade | Descrição |
|---|---|
| **Busca Geolocalizada** | Pesquisa por nicho de mercado e localização |
| **Extração de Dados** | Telefone, website, avaliação, endereço completo |
| **Conversão 1-Click** | Transforma resultado em lead/projeto no CRM |
| **Exportação Excel** | Dados estruturados para follow-up comercial |

### Kanban Visual

Gestão visual de projetos com quadro Kanban integrado à API.

| Capacidade | Descrição |
|---|---|
| **Fases Configuráveis** | Planejamento → Produção → Entrega → Finalizado |
| **Cartões Informativos** | Nome, cliente, valor contratado, status do projeto |
| **Filtros e Busca** | Por nome de projeto, cliente ou status |
| **Atualização via API** | Status sincronizado entre frontend e backend |

---

## Tech Stack

| Camada | Tecnologia | Versão |
|---|---|---|
| **Linguagem** | Python | 3.11+ |
| **API** | FastAPI | 0.109+ |
| **ORM** | SQLAlchemy | 2.x |
| **Validação** | Pydantic | v2 |
| **Banco de Dados** | PostgreSQL + pgvector | 16+ |
| **Frontend** | Streamlit | 1.30+ |
| **Visualização** | Plotly | — |
| **IA — Chat** | OpenAI GPT-4o-mini | — |
| **IA — Embeddings** | text-embedding-3-small | 1536 dims |
| **PDF** | FPDF2 | — |
| **Containerização** | Docker + Docker Compose | — |

---

## Instalação

### Pré-requisitos

- Python 3.11+
- Docker (para o banco de dados)
- Chave de API OpenAI
- Git

### Passo 1 — Clonar o repositório

```bash
git clone https://github.com/KauaPaimGit/VyronSystem.git
cd VyronSystem
```

### Passo 2 — Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
DATABASE_URL=postgresql://admin:password123@localhost:5432/agency_os
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=sua_chave_secreta_aqui
```

### Passo 3 — Iniciar o banco de dados

```bash
docker run -d \
  --name vyron-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=agency_os \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### Passo 4 — Executar o schema do banco

```bash
psql -h localhost -U admin -d agency_os -f docs/database_schema.sql
```

> **Nota:** O schema completo com as 18 tabelas, views, triggers e índices vetoriais está em `docs/database_schema.sql`.

### Passo 5 — Instalar dependências

```bash
pip install -r requirements.txt
```

### Passo 6 — Iniciar o backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Passo 7 — Iniciar o frontend (novo terminal)

```bash
cd frontend
streamlit run app.py
```

### Acessos

| Interface | URL |
|---|---|
| API Backend | `http://localhost:8000` |
| Swagger UI (Docs) | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Frontend Streamlit | `http://localhost:8501` |

### Alternativa — Docker Compose (stack completa)

```bash
docker-compose up --build
```

> Sobe o PostgreSQL + pgvector e a API automaticamente.

---

## Estrutura de Diretórios

```
VyronSystem/
├── main.py                  # Entrypoint FastAPI — 50+ endpoints
├── requirements.txt         # Dependências Python
├── Dockerfile               # Build da API
├── docker-compose.yml       # Orquestração (DB + API)
├── .env                     # Variáveis de ambiente (não versionado)
│
├── app/                     # Lógica do Backend
│   ├── __init__.py
│   ├── auth.py              # Autenticação JWT + bcrypt
│   ├── database.py          # Conexão SQLAlchemy + Engine
│   ├── models.py            # Modelos ORM (18 tabelas)
│   ├── schemas.py           # Schemas Pydantic v2
│   ├── services.py          # Serviços de IA, PDF, embeddings
│   └── services/
│       └── radar.py         # Módulo Radar (Google Maps API)
│
├── frontend/                # Interface Streamlit
│   ├── app.py               # Aplicação frontend completa
│   ├── requirements.txt     # Dependências do frontend
│   └── README.md
│
├── docs/                    # Documentação e Schema SQL
│   ├── database_schema.sql  # Schema completo do banco (18 tabelas + views)
│   ├── architecture_docs.md # Arquitetura técnica detalhada
│   ├── INSTALL.md           # Guia de instalação estendido
│   ├── AUTH_README.md       # Documentação de autenticação
│   ├── RADAR_README.md      # Documentação do Módulo Radar
│   ├── CHANGELOG_v1.1.md    # Histórico de versões
│   ├── FEATURE_ROI_v1.2.md  # Especificação ROI Intelligence
│   └── FIXES_v1.1.md        # Registro de correções
│
├── scripts/                 # Utilitários de administração
│   ├── create_admin.py      # Criar usuário admin local
│   ├── create_remote_admin.py
│   ├── fix_users_table.py
│   ├── force_admin_creation.py
│   ├── remove_duplicates.py
│   ├── add_kanban_status.py
│   └── main_endpoint_addition.py
│
├── migrations/              # Migrations SQL incrementais
│   ├── 001_add_marketing_metrics.sql
│   ├── 002_add_product_price_to_projects.sql
│   └── 003_add_users_table.sql
│
└── diagrams/
    └── er_diagram.md        # Diagrama Entidade-Relacionamento
```

---

## Módulos do Sistema

| # | Módulo | Descrição |
|---|---|---|
| 1 | **Autenticação** | JWT + bcrypt, roles (admin/user), controle de sessão |
| 2 | **CRM Inteligente** | CRUD de clientes, Health Score, LTV, funil de vendas |
| 3 | **Gestão de Projetos** | Tipos recorrente/pontual, templates de tarefas, Kanban |
| 4 | **Financeiro (ERP)** | Receitas, despesas, custos por projeto, margem de lucro |
| 5 | **Marketing** | Métricas de campanha, KPIs automáticos (CTR, CPC, ROI) |
| 6 | **Entrada Manual** | Formulários com memória RAG integrada |
| 7 | **Contratos** | Templates dinâmicos com variáveis, geração PDF |
| 8 | **Agency Brain (IA)** | RAG + Function Calling + análise multimodal |
| 9 | **Radar de Vendas** | Prospecção B2B via Google Maps, export Excel |
| 10 | **Kanban Visual** | Quadro de gestão visual com filtros e busca |

---

## API REST

### Endpoints Principais (50+)

```
# Autenticação
POST   /login                              Autenticar usuário

# CRM
POST   /clients                            Criar cliente
GET    /clients                            Listar clientes
GET    /clients/{id}                       Detalhes do cliente
PATCH  /clients/{id}                       Atualizar cliente
DELETE /clients/{id}                       Remover cliente

# Projetos
POST   /projects                           Criar projeto
GET    /projects                           Listar projetos
GET    /projects/{id}                      Detalhes do projeto
PATCH  /projects/{id}                      Atualizar projeto
PATCH  /projects/{id}/status               Atualizar status (Kanban)
GET    /projects/{id}/financial-dashboard   Dashboard financeiro
GET    /projects/{id}/marketing-kpis       KPIs de marketing

# Entrada Manual
POST   /manual/projects                    Criar projeto (formulário)
POST   /manual/expenses                    Registrar despesa
POST   /manual/marketing-metrics           Adicionar métricas

# Inteligência Artificial
POST   /ai/search                          Busca semântica (RAG)
POST   /ai/chat                            Chat com IA (multimodal)

# Radar de Vendas
POST   /radar/search                       Buscar empresas (Google Maps)
POST   /radar/convert                      Converter em lead/projeto
POST   /radar/export                       Exportar para Excel

# Interações
POST   /interactions                       Criar interação
GET    /clients/{id}/interactions           Listar interações
DELETE /interactions/{id}                   Remover interação
```

### Exemplos de Uso

```bash
# Autenticar
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@agency.com", "password": "senha"}'

# Criar projeto via entrada manual
curl -X POST http://localhost:8000/manual/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Campanha Digital Q1",
    "client_name": "Empresa XYZ",
    "budget": 15000,
    "product_price": 500
  }'

# Chat com IA (Agency Brain)
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual projeto tem melhor ROI este mês?"}'
```

---

## Banco de Dados

**PostgreSQL 16+ com pgvector** — 18 tabelas, 3 views materializadas, triggers de auditoria.

### Extensões

| Extensão | Finalidade |
|---|---|
| `pgvector` | Busca vetorial para embeddings (1536 dims) |
| `uuid-ossp` | Geração de UUIDs |

### Tabelas Principais

| Tabela | Módulo |
|---|---|
| `users` | Autenticação |
| `clients` | CRM |
| `sales_pipeline` | CRM — Funil |
| `interactions` | CRM — Histórico (vetorial) |
| `projects` | Projetos |
| `project_tasks` | Projetos |
| `task_templates` | Projetos |
| `revenues` | Financeiro |
| `expenses` | Financeiro |
| `project_costs` | Financeiro |
| `marketing_metrics` | Marketing |
| `contract_templates` | Contratos |
| `contracts` | Contratos |
| `ai_insights` | IA |
| `knowledge_base` | IA — RAG |

### Views SQL

| View | Descrição |
|---|---|
| `project_profitability` | Rentabilidade por projeto com margem calculada |
| `client_lifetime_value` | LTV agregado por cliente |
| `marketing_kpis` | CTR, CPC, CPL, ROI automatizados |

> Schema completo: [`docs/database_schema.sql`](docs/database_schema.sql)

---

## Documentação

| Documento | Descrição |
|---|---|
| [`docs/architecture_docs.md`](docs/architecture_docs.md) | Arquitetura técnica completa |
| [`docs/database_schema.sql`](docs/database_schema.sql) | Schema do banco (18 tabelas + views + triggers) |
| [`docs/INSTALL.md`](docs/INSTALL.md) | Guia detalhado de instalação |
| [`docs/AUTH_README.md`](docs/AUTH_README.md) | Sistema de autenticação |
| [`docs/RADAR_README.md`](docs/RADAR_README.md) | Módulo Radar de Vendas |
| [`docs/CHANGELOG_v1.1.md`](docs/CHANGELOG_v1.1.md) | Histórico de versões |
| [`docs/FEATURE_ROI_v1.2.md`](docs/FEATURE_ROI_v1.2.md) | Especificação ROI Intelligence |
| [`diagrams/er_diagram.md`](diagrams/er_diagram.md) | Diagrama Entidade-Relacionamento |

---

## Roadmap

| Prioridade | Feature | Status |
|---|---|---|
| P0 | Ingestão de Documentos Longos (PDF chunking + embeddings incrementais) | Planejado |
| P1 | Multi-tenancy — Isolamento de dados por agência | Planejado |
| P1 | Dashboard de ROI consolidado cross-project | Planejado |
| P2 | Webhooks para integração com ferramentas externas | Planejado |
| P2 | Notificações em tempo real (WebSocket) | Planejado |
| P3 | App mobile (React Native) | Backlog |

---

<div align="center">

## Licença

**Proprietário — Todos os direitos reservados.**

---

Vyron System v1.0.0 — Enterprise AI ERP

Desenvolvido para escalar operações de agências digitais.

</div>
