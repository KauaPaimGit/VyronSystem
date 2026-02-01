# 🚀 Agency OS - Frontend

Interface Streamlit para o sistema Agency OS.

## 📦 Instalação

1. Entre na pasta do frontend:
```powershell
cd frontend
```

2. Instale as dependências:
```powershell
pip install -r requirements.txt
```

## ▶️ Como Executar

Certifique-se de que a API FastAPI está rodando em `http://localhost:8000`:

```powershell
# No diretório frontend/
streamlit run app.py
```

O aplicativo abrirá automaticamente no navegador em `http://localhost:8501`

## 🎯 Funcionalidades

### 📊 Dashboard Financeiro
- Visualização de métricas financeiras (Receitas, Despesas, Lucro)
- Gráfico de distribuição financeira
- Análise automática da saúde financeira do projeto

### 🤖 Agency Brain (Chat IA)
- Chat inteligente com contexto das interações
- Busca semântica usando embeddings
- Histórico de conversa mantido na sessão
- Respostas baseadas em dados reais do banco

### 📝 Gestão de Interações
- Formulário para adicionar novas interações
- Geração automática de embeddings
- Preview das últimas interações
- Integração completa com a API

## 🔧 Configuração

A URL da API pode ser alterada no arquivo `app.py`:
```python
API_BASE_URL = "http://localhost:8000"
```

## 📝 Notas

- Certifique-se de ter IDs válidos de projetos e clientes
- Use o Swagger da API (`/docs`) para obter IDs se necessário
- O chat mantém histórico apenas durante a sessão
