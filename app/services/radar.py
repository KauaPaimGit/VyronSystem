"""
Serviço de Prospecção Ativa (Radar de Vendas)
Integração com SerpApi para buscar empresas no Google Maps
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("⚠️ google-search-results não instalado. Execute: pip install google-search-results")


def search_business(query: str, location: str, limit: int = 20) -> List[Dict]:
    """
    Busca empresas usando Google Maps via SerpApi
    
    Args:
        query: Termo de busca (ex: "Pizzaria", "Academia")
        location: Localização (ex: "Passos, MG", "São Paulo, SP")
        limit: Número máximo de resultados (padrão: 20)
        
    Returns:
        Lista de dicionários com dados das empresas:
        - name: Nome da empresa
        - address: Endereço completo
        - phone: Telefone (se disponível)
        - website: Site (se disponível)
        - rating: Avaliação (se disponível)
        - reviews: Número de avaliações
        - type: Tipo de negócio
        - position: Posição nos resultados
        
    Raises:
        ValueError: Se SERPAPI_KEY não estiver configurada
        Exception: Erro na busca
    """
    
    if not SERPAPI_AVAILABLE:
        raise ImportError("Biblioteca google-search-results não instalada")
    
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError(
            "SERPAPI_KEY não configurada. "
            "Adicione no .env: SERPAPI_KEY=sua_chave_aqui"
        )
    
    # Monta a query completa
    search_query = f"{query} in {location}"
    
    # Parâmetros da busca
    params = {
        "engine": "google_maps",
        "q": search_query,
        "type": "search",
        "api_key": api_key,
        "hl": "pt-br",
        "gl": "br"
    }
    
    try:
        # Executa a busca
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extrai os resultados locais
        local_results = results.get("local_results", [])
        
        if not local_results:
            return []
        
        # Formata os resultados
        businesses = []
        for idx, result in enumerate(local_results[:limit]):
            business = {
                "name": result.get("title", "Nome não disponível"),
                "address": result.get("address", "Endereço não disponível"),
                "phone": result.get("phone", None),
                "website": result.get("website", None),
                "rating": result.get("rating", None),
                "reviews": result.get("reviews", 0),
                "type": result.get("type", "Negócio Local"),
                "position": idx + 1,
                "place_id": result.get("place_id", None),
                "gps_coordinates": result.get("gps_coordinates", None),
                "service_options": result.get("service_options", None),
                "hours": result.get("hours", None)
            }
            businesses.append(business)
        
        return businesses
        
    except Exception as e:
        raise Exception(f"Erro ao buscar empresas: {str(e)}")


def format_contact_info(business: Dict) -> str:
    """
    Formata as informações de contato em texto
    
    Args:
        business: Dicionário com dados da empresa
        
    Returns:
        String formatada com as informações
    """
    info_parts = []
    
    if business.get("phone"):
        info_parts.append(f"📞 {business['phone']}")
    
    if business.get("website"):
        info_parts.append(f"🌐 {business['website']}")
    
    if business.get("address"):
        info_parts.append(f"📍 {business['address']}")
    
    if business.get("rating"):
        stars = "⭐" * int(business['rating'])
        info_parts.append(f"{stars} {business['rating']} ({business.get('reviews', 0)} avaliações)")
    
    return "\n".join(info_parts) if info_parts else "Informações de contato não disponíveis"


def create_project_from_business(business: Dict, default_value: float = 5000.0) -> Dict:
    """
    Converte dados de uma empresa em dados para criar um projeto
    
    Args:
        business: Dicionário com dados da empresa
        default_value: Valor padrão do projeto (R$)
        
    Returns:
        Dicionário formatado para criar projeto
    """
    
    # Nome do projeto = Nome da empresa
    project_name = business.get("name", "Empresa sem nome")
    
    # Cliente = Nome da empresa (será criado automaticamente)
    client_name = project_name
    
    # Descrição com todas as informações
    description_parts = [
        f"🎯 Lead capturado via Radar de Vendas",
        f"📊 Tipo: {business.get('type', 'Negócio Local')}",
        "",
        "📋 Informações de Contato:",
        format_contact_info(business)
    ]
    
    if business.get("hours"):
        description_parts.append(f"\n⏰ Horário: {business['hours']}")
    
    description = "\n".join(description_parts)
    
    return {
        "project_name": project_name,
        "client_name": client_name,
        "description": description,
        "value": default_value,
        "project_type": "prospection",  # Tipo específico para prospecção
        "contact_phone": business.get("phone"),
        "contact_website": business.get("website"),
        "contact_address": business.get("address"),
        "rating": business.get("rating"),
        "source": "radar_serpapi"
    }
