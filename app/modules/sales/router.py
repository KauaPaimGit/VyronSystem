"""
Sales Router — CRM (Clientes), Interações e Radar de Vendas (Prospecção)
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from uuid import uuid4

from app.database import get_db
from app import models, schemas
from app.services import (
    generate_embedding,
    search_business,
    export_businesses_to_excel,
    get_client_interactions,
)

router = APIRouter(tags=["Sales"])


# ══════════════════════════════════════════════
# CLIENTES (CRM)
# ══════════════════════════════════════════════

@router.post("/clients", response_model=schemas.ClientResponse, status_code=201)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    """Cria um novo cliente no sistema."""
    existing = db.query(models.Client).filter(models.Client.email == client.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado no sistema")

    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("/clients", response_model=List[schemas.ClientResponse])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista todos os clientes cadastrados."""
    query = db.query(models.Client)
    if status:
        query = query.filter(models.Client.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/clients/{client_id}", response_model=schemas.ClientResponse)
def get_client(client_id: str, db: Session = Depends(get_db)):
    """Retorna os detalhes de um cliente específico pelo ID."""
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.patch("/clients/{client_id}", response_model=schemas.ClientResponse)
def update_client(
    client_id: str,
    client_update: schemas.ClientUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza parcialmente os dados de um cliente."""
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    for field, value in client_update.model_dump(exclude_unset=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/clients/{client_id}", status_code=204)
def delete_client(client_id: str, db: Session = Depends(get_db)):
    """Remove um cliente do sistema."""
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    try:
        db.delete(client)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível deletar cliente com projetos vinculados: {str(e)}",
        )
    return None


# ══════════════════════════════════════════════
# INTERAÇÕES (RAG de Contexto)
# ══════════════════════════════════════════════

@router.post("/interactions/", response_model=schemas.InteractionResponse, status_code=201)
async def create_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Cria uma nova interação com o cliente e gera embedding vetorial."""
    client = db.query(models.Client).filter(models.Client.id == interaction.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if interaction.project_id:
        project = db.query(models.Project).filter(models.Project.id == interaction.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

    embedding = await generate_embedding(interaction.content)

    db_interaction = models.Interaction(
        client_id=interaction.client_id,
        type=interaction.interaction_type.value,
        content=interaction.content,
        content_embedding=embedding,
        interaction_date=datetime.utcnow(),
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)

    return schemas.InteractionResponse(
        id=db_interaction.id,
        client_id=db_interaction.client_id,
        project_id=interaction.project_id,
        content=db_interaction.content,
        interaction_type=schemas.InteractionType(db_interaction.type),  # type: ignore
        created_at=db_interaction.created_at,
    )


@router.get("/interactions/", response_model=List[schemas.InteractionResponse])
def list_interactions(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista todas as interações cadastradas."""
    query = db.query(models.Interaction)
    if client_id:
        query = query.filter(models.Interaction.client_id == client_id)
    query = query.order_by(models.Interaction.interaction_date.desc())
    interactions = query.offset(skip).limit(limit).all()

    return [
        schemas.InteractionResponse(
            id=i.id,
            client_id=i.client_id,
            project_id=None,
            content=i.content,
            interaction_type=schemas.InteractionType(i.type),  # type: ignore
            created_at=i.created_at,
        )
        for i in interactions
    ]


@router.get("/interactions/{interaction_id}", response_model=schemas.InteractionResponse)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    """Retorna os detalhes de uma interação específica pelo ID."""
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interação não encontrada")

    return schemas.InteractionResponse(
        id=interaction.id,
        client_id=interaction.client_id,
        project_id=None,
        content=interaction.content,
        interaction_type=schemas.InteractionType(interaction.type),  # type: ignore
        created_at=interaction.created_at,
    )


@router.delete("/interactions/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    """Remove uma interação do sistema."""
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interação não encontrada")
    db.delete(interaction)
    db.commit()
    return None


@router.get("/clients/{client_id}/interactions")
def get_client_interactions_endpoint(client_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Busca as últimas interações de um cliente para exibir na timeline."""
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    interactions = get_client_interactions(db, client_id, limit)

    return {
        "client_id": client_id,
        "client_name": client.name,
        "total": len(interactions),
        "interactions": interactions,
    }


# ══════════════════════════════════════════════
# RADAR DE VENDAS (PROSPECÇÃO ATIVA)
# ══════════════════════════════════════════════

class RadarSearchRequest(BaseModel):
    query: str
    location: str
    limit: int = 20


class RadarConvertRequest(BaseModel):
    business_name: str
    business_type: str
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    reviews: int = 0
    project_value: float = 5000.0


@router.get("/radar/search")
def search_businesses_endpoint(query: str, location: str, limit: int = 20):
    """Busca empresas usando Google Maps via SerpApi."""
    try:
        if not query or not location:
            raise HTTPException(
                status_code=400,
                detail="Parâmetros 'query' e 'location' são obrigatórios",
            )

        businesses = search_business(query, location, limit)

        return {
            "success": True,
            "query": query,
            "location": location,
            "total": len(businesses),
            "businesses": businesses,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Serviço de busca não disponível: {str(e)}",
        )
    except Exception as e:
        import traceback
        print(f"Erro ao buscar empresas: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar empresas: {str(e)}")


@router.get("/radar/export")
def export_radar_results(query: str, location: str, limit: int = 20):
    """Exporta resultados da busca para Excel."""
    try:
        businesses = search_business(query, location, limit)
        if not businesses:
            raise HTTPException(status_code=404, detail="Nenhuma empresa encontrada para exportar")

        excel_file = export_businesses_to_excel(businesses, query, location)
        filename = f"Radar_Vendas_{query.replace(' ', '_')}_{location.replace(' ', '_')}.xlsx"

        return Response(
            content=excel_file.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {str(e)}")


@router.post("/radar/convert")
def convert_business_to_project(request: RadarConvertRequest, db: Session = Depends(get_db)):
    """Converte uma empresa encontrada em um projeto no Kanban."""
    try:
        # Verifica se o cliente já existe
        client = db.query(models.Client).filter(models.Client.name == request.business_name).first()

        if not client:
            client = models.Client(
                id=uuid4(),
                name=request.business_name,
                company_name=request.business_name,
                email=f"contato@{request.business_name.lower().replace(' ', '')}.com",
                phone=request.phone,
                status="lead",
                source="radar_serpapi",
                created_at=datetime.utcnow(),
            )
            db.add(client)
            db.flush()

        description_parts = [
            "🎯 Lead capturado via Radar de Vendas",
            f"📊 Tipo: {request.business_type}",
            "",
        ]
        if request.phone:
            description_parts.append(f"📞 {request.phone}")
        if request.website:
            description_parts.append(f"🌐 {request.website}")
        if request.address:
            description_parts.append(f"📍 {request.address}")
        if request.rating:
            stars = "⭐" * int(request.rating)
            description_parts.append(f"{stars} {request.rating}/5 ({request.reviews} avaliações)")

        description = "\n".join(description_parts)

        project = models.Project(
            id=uuid4(),
            client_id=client.id,
            name=f"Prospecção: {request.business_name}",
            type="prospection",
            category="vendas",
            status="Negociação",
            contract_value=Decimal(str(request.project_value)),
            start_date=date.today(),
            is_recurrent=False,
            created_at=datetime.utcnow(),
        )
        db.add(project)

        interaction = models.Interaction(
            id=uuid4(),
            client_id=client.id,
            type="system_log",
            subject=f"Lead capturado via Radar",
            content=description,
            interaction_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(interaction)
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "message": f"Lead '{request.business_name}' capturado com sucesso!",
            "project_id": str(project.id),
            "project_name": project.name,
            "client_id": str(client.id),
            "client_name": client.name,
            "status": project.status,
            "value": float(project.contract_value),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar projeto: {str(e)}")
