# 🚀 Guia Rápido de Instalação - Agency OS v1.1

## ⚡ Setup em 5 Minutos

### Pré-requisitos
- Python 3.11+
- PostgreSQL 15+ com extensão pgvector
- Git

---

## 📥 Passo 1: Clone o Repositório

```bash
git clone https://github.com/KauaPaimGit/AgencyOS.git
cd AgencyOS
```

---

## 🐘 Passo 2: Configure o Banco de Dados

### Opção A: Docker (Recomendado)

```bash
docker run -d \
  --name agency-os-db \
  -e POSTGRES_PASSWORD=senha123 \
  -e POSTGRES_DB=agency_os \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### Opção B: PostgreSQL Local

1. Instale o PostgreSQL 15+
2. Crie o banco:
   ```bash
   createdb agency_os
   ```

---

## 🗄️ Passo 3: Execute os Scripts SQL

```bash
# Schema principal
psql -h localhost -U postgres -d agency_os -f database_schema.sql

# Migration: Tabela de Marketing Metrics
psql -h localhost -U postgres -d agency_os -f migrations/001_add_marketing_metrics.sql
```

**Saída esperada:**
```
✅ Migration 001_add_marketing_metrics.sql executada com sucesso!
📊 Tabela marketing_metrics criada
📈 View marketing_kpis criada
🔧 Índices e triggers configurados
```

---

## 🐍 Passo 4: Instale as Dependências Python

```bash
# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências do backend
pip install -r requirements.txt

# Instale as dependências do frontend
cd frontend
pip install -r requirements.txt
cd ..
```

---

## 🔑 Passo 5: Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Banco de Dados
DATABASE_URL=postgresql://postgres:senha123@localhost:5432/agency_os

# OpenAI (obtenha sua chave em: https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-...

# Segurança
SECRET_KEY=seu-secret-key-super-seguro-aqui
```

---

## ▶️ Passo 6: Inicie os Serviços

### Terminal 1: Backend (FastAPI)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Aguarde até ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

### Terminal 2: Frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```

**Aguarde até ver:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

---

## ✅ Passo 7: Teste a Instalação

### 1. Acesse a API
Abra: http://localhost:8000

Você deve ver:
```json
{
  "status": "running",
  "service": "Agency OS API"
}
```

### 2. Teste a Documentação da API
Abra: http://localhost:8000/docs

Você verá o Swagger UI com todos os endpoints.

### 3. Acesse o Frontend
Abra: http://localhost:8501

Você verá a interface do Agency OS com as abas:
- 📊 Dashboard Financeiro
- 🤖 Agency Brain
- ✍️ Lançamentos Manuais
- 📝 Gestão

---

## 🎯 Primeiros Passos

### 1. Crie um Cliente

**Via API (Swagger)**:
1. Acesse http://localhost:8000/docs
2. Encontre `POST /clients`
3. Clique em "Try it out"
4. Use o JSON:
   ```json
   {
     "name": "João Silva",
     "email": "joao@exemplo.com",
     "company_name": "Empresa Teste LTDA",
     "phone": "11999999999",
     "status": "lead"
   }
   ```
5. Clique em "Execute"

### 2. Crie um Projeto

**Via Frontend**:
1. Acesse http://localhost:8501
2. Vá para "✍️ Lançamentos Manuais"
3. Tab "💼 Novo Projeto"
4. Preencha:
   - Nome: "Campanha de Vendas Q1"
   - Cliente: "Empresa Teste LTDA"
   - Orçamento: 10000
5. Clique em "Criar Projeto"
6. **Copie o ID do projeto gerado**

### 3. Registre Métricas de Marketing

**Via Frontend**:
1. Ainda em "✍️ Lançamentos Manuais"
2. Tab "📊 Métricas de Marketing"
3. Selecione o projeto criado
4. Preencha:
   - Data: hoje
   - Impressões: 50000
   - Cliques: 1500
   - Leads: 75
   - Custo: 3000
   - Plataforma: Google Ads
5. Clique em "Salvar Métricas"

### 4. Visualize o Dashboard

**Via Frontend**:
1. Vá para "📊 Dashboard Financeiro"
2. Cole o ID do projeto copiado
3. Clique em "Carregar Dados"
4. Veja:
   - Resumo Financeiro
   - KPIs de Marketing (CTR, CPC, CPL, Taxa de Conversão)
   - Análise de performance

### 5. Converse com a IA

**Via Frontend**:
1. Vá para "🤖 Agency Brain"
2. Pergunte: "Qual a taxa de conversão da Campanha de Vendas Q1?"
3. A IA responderá usando os dados que você registrou!

---

## 🔧 Resolução de Problemas

### Erro: "Connection refused" no banco

**Solução:**
```bash
# Verifique se o PostgreSQL está rodando
docker ps  # Deve mostrar o container agency-os-db

# Se não estiver, inicie:
docker start agency-os-db
```

### Erro: "API não está respondendo" no frontend

**Solução:**
```bash
# Verifique se o backend está rodando
curl http://localhost:8000/

# Se não, inicie:
uvicorn main:app --reload
```

### Erro: "ModuleNotFoundError"

**Solução:**
```bash
# Certifique-se de que o ambiente virtual está ativado
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Reinstale as dependências
pip install -r requirements.txt
```

### Erro: "Tabela não existe"

**Solução:**
```bash
# Execute os scripts SQL novamente
psql -h localhost -U postgres -d agency_os -f database_schema.sql
psql -h localhost -U postgres -d agency_os -f migrations/001_add_marketing_metrics.sql
```

---

## 📚 Próximos Passos

1. **Leia a documentação completa**: [README.md](README.md)
2. **Veja o histórico de mudanças**: [CHANGELOG_v1.1.md](CHANGELOG_v1.1.md)
3. **Explore os endpoints da API**: http://localhost:8000/docs
4. **Configure sua chave OpenAI** para habilitar a IA

---

## 🆘 Precisa de Ajuda?

- **Documentação**: Veja o README.md
- **Issues**: https://github.com/KauaPaimGit/AgencyOS/issues
- **Arquitetura**: Leia architecture_docs.md

---

## ✅ Checklist de Instalação

- [ ] PostgreSQL instalado e rodando
- [ ] Banco de dados `agency_os` criado
- [ ] Schema principal executado
- [ ] Migration de marketing executada
- [ ] Ambiente virtual Python criado
- [ ] Dependências instaladas (backend + frontend)
- [ ] Arquivo `.env` configurado
- [ ] Backend rodando em localhost:8000
- [ ] Frontend rodando em localhost:8501
- [ ] Primeiro cliente criado
- [ ] Primeiro projeto criado
- [ ] Primeira métrica registrada

**Instalação completa! 🎉**
