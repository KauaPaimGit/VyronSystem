# 📡 Módulo Radar de Vendas - Prospecção Ativa

## 🎯 Funcionalidades

O módulo **Radar de Vendas** permite buscar empresas potenciais usando o Google Maps e convertê-las automaticamente em leads no seu Kanban.

### Recursos:
- ✅ Busca empresas por nicho e localização
- ✅ Exibe informações completas (telefone, site, avaliação, endereço)
- ✅ Converte empresas em projetos com 1 clique
- ✅ Leads vão direto para o Kanban (fase "Negociação")
- ✅ Estatísticas da busca em tempo real

## 🚀 Instalação

### 1. Instalar Dependências

```bash
pip install google-search-results
```

Ou instale todas as dependências:

```bash
pip install -r requirements.txt
```

### 2. Configurar SerpApi

1. Crie uma conta gratuita em: https://serpapi.com
   - Plano gratuito: 100 buscas/mês
   - Plano pago: a partir de $50/mês

2. Copie sua API Key no dashboard

3. Adicione no arquivo `.env`:

```env
SERPAPI_KEY=sua_chave_aqui
```

### 3. Reiniciar o Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 Como Usar

### 1. Acesse a aba "📡 Radar de Vendas"

### 2. Preencha os campos de busca:
- **Nicho**: Tipo de negócio (ex: "Pizzaria", "Academia", "Salão de Beleza")
- **Localização**: Cidade (ex: "Passos, MG", "São Paulo, SP")

### 3. Clique em "🔍 Escanear"

O sistema vai buscar até 20 empresas no Google Maps

### 4. Analise os Resultados

Cada empresa mostra:
- ⭐ Avaliação e número de reviews
- 📞 Telefone
- 🌐 Website
- 📍 Endereço

### 5. Capturar Leads

- Defina o **valor do projeto** (padrão: R$ 5.000)
- Clique em **"🎯 Capturar"**
- O lead vai automaticamente para o **Kanban** na fase de **Negociação**

## 🔧 Endpoints da API

### GET `/radar/search`

Busca empresas no Google Maps

**Parâmetros:**
- `query` (string): Tipo de negócio
- `location` (string): Cidade
- `limit` (int, opcional): Máximo de resultados (padrão: 20)

**Resposta:**
```json
{
  "success": true,
  "query": "Pizzaria",
  "location": "Passos, MG",
  "total": 15,
  "businesses": [
    {
      "name": "Pizzaria Bella Massa",
      "address": "Rua Principal, 123",
      "phone": "(35) 3529-1234",
      "website": "https://bellamassa.com.br",
      "rating": 4.5,
      "reviews": 87,
      "type": "Pizzaria",
      "position": 1
    }
  ]
}
```

### POST `/radar/convert`

Converte uma empresa em projeto

**Body:**
```json
{
  "business_name": "Pizzaria Bella Massa",
  "business_type": "Pizzaria",
  "phone": "(35) 3529-1234",
  "website": "https://bellamassa.com.br",
  "address": "Rua Principal, 123",
  "rating": 4.5,
  "reviews": 87,
  "project_value": 5000.0
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Lead 'Pizzaria Bella Massa' capturado com sucesso!",
  "project_id": "uuid-do-projeto",
  "project_name": "Prospecção: Pizzaria Bella Massa",
  "client_id": "uuid-do-cliente",
  "status": "Negociação",
  "value": 5000.0
}
```

## 🎨 Fluxo de Trabalho

```
1. Buscar Empresas (SerpApi) 
   ↓
2. Analisar Resultados
   ↓
3. Capturar Lead
   ↓
4. Cliente criado automaticamente
   ↓
5. Projeto criado (status: Negociação)
   ↓
6. Interação registrada (log de prospecção)
   ↓
7. Lead aparece no Kanban
```

## 💡 Dicas de Uso

### Buscas Eficientes:
- ✅ "Pizzaria" + "Passos, MG"
- ✅ "Academia" + "São Paulo, SP - Zona Sul"
- ✅ "Salão de Beleza" + "Rio de Janeiro, RJ"

### Evite:
- ❌ Buscas muito genéricas: "Loja"
- ❌ Sem localização: apenas "Pizzaria"

### Valores Sugeridos por Nicho:
- 🍕 Pizzaria/Restaurante: R$ 3.000 - R$ 8.000
- 💪 Academia: R$ 5.000 - R$ 15.000
- ✂️ Salão de Beleza: R$ 2.000 - R$ 5.000
- 🏪 Loja/E-commerce: R$ 10.000 - R$ 50.000

## 🔒 Segurança

- ✅ A SERPAPI_KEY é armazenada no servidor (nunca exposta ao frontend)
- ✅ Todas as requisições são autenticadas
- ✅ Validação de dados antes de salvar no banco

## 📊 Limites

### SerpApi - Plano Gratuito:
- 100 buscas/mês
- Até 20 resultados por busca
- Dados em tempo real

### Recomendação:
Para uso profissional intenso, considere o plano pago da SerpApi

## 🐛 Troubleshooting

### Erro: "SERPAPI_KEY não configurada"
**Solução:** Adicione a chave no arquivo `.env`

### Erro: "Serviço de busca não disponível"
**Solução:** Instale: `pip install google-search-results`

### Nenhuma empresa encontrada
**Soluções:**
- Verifique se a localização está correta
- Tente termos de busca mais específicos
- Confirme se há empresas desse tipo na região

## 📈 Próximas Melhorias

- [ ] Busca em múltiplas cidades simultaneamente
- [ ] Exportar resultados para CSV
- [ ] Enriquecimento de dados (LinkedIn, CNPJ)
- [ ] Filtros avançados (avaliação mínima, com website apenas)
- [ ] Histórico de buscas realizadas
- [ ] Análise de concorrentes

## 🎯 Casos de Uso

### Agência de Marketing Digital:
Prospecte pizzarias, salões, academias em sua região

### Consultoria B2B:
Encontre empresas por setor e região específica

### Vendas de Software:
Busque empresas que podem se beneficiar do seu produto

---

**Desenvolvido para AgencyOS v1.1**  
Sistema Inteligente de Gestão Empresarial
