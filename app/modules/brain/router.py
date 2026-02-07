"""
Brain Router — RAG Documental, Busca Semântica e Chat com IA (ponto único de inteligência)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.services import generate_embedding, generate_answer
from app.brain_service import BrainService

router = APIRouter(tags=["Brain"])


# ══════════════════════════════════════════════
# BUSCA SEMÂNTICA EM INTERAÇÕES (RAG legado)
# ══════════════════════════════════════════════

@router.post("/ai/search", response_model=schemas.SearchResponse)
async def semantic_search(request: schemas.SearchRequest, db: Session = Depends(get_db)):
    """
    Busca semântica de interações usando embeddings vetoriais.

    Utiliza pgvector para encontrar as interações mais similares à query.
    """
    query_embedding = await generate_embedding(request.query)

    similar = (
        db.query(models.Interaction)
        .filter(models.Interaction.content_embedding.isnot(None))
        .order_by(models.Interaction.content_embedding.cosine_distance(query_embedding))
        .limit(request.limit)
        .all()
    )

    results = [
        schemas.InteractionResponse(
            id=i.id,
            client_id=i.client_id,
            project_id=None,
            content=i.content,
            interaction_type=i.type,
            created_at=i.created_at,
        )
        for i in similar
    ]

    return schemas.SearchResponse(results=results)


# ══════════════════════════════════════════════
# CHAT COM IA (RAG + Visão Multimodal)
# ══════════════════════════════════════════════

@router.post("/ai/chat", response_model=schemas.ChatResponse)
async def chat_with_rag(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Chat com IA usando RAG (Retrieval-Augmented Generation) e Visão Multimodal.

    O sistema:
    1. Busca interações relevantes no banco usando embeddings
    2. Usa esse contexto para responder via GPT
    3. Suporta imagens (Base64) para análise visual (recibos, notas etc.)
    """
    query_embedding = await generate_embedding(request.query)

    relevant = (
        db.query(models.Interaction)
        .filter(models.Interaction.content_embedding.isnot(None))
        .order_by(models.Interaction.content_embedding.cosine_distance(query_embedding))
        .limit(3)
        .all()
    )

    if relevant:
        context_text = "\n\n---\n\n".join(
            [f"Interação ({i.type}) em {i.interaction_date}:\n{i.content}" for i in relevant]
        )
    else:
        context_text = "Nenhuma informação disponível no banco de dados."

    answer = await generate_answer(
        query=request.query,
        context=context_text,
        db=db,
        image_data=request.image,
    )

    return schemas.ChatResponse(answer=answer)


# ══════════════════════════════════════════════
# DOCUMENT RAG (Ingestão & Busca de PDFs)
# ══════════════════════════════════════════════

@router.post("/brain/search", response_model=schemas.DocumentSearchResponse)
async def brain_search(request: schemas.DocumentSearchRequest, db: Session = Depends(get_db)):
    """
    Busca semântica em documentos ingeridos (PDFs).

    Retorna os 3 fragmentos mais relevantes.
    """
    try:
        results = await BrainService.semantic_search(
            query=request.query,
            db=db,
            limit=request.limit,
            filename_filter=request.filename,
        )

        return schemas.DocumentSearchResponse(
            query=request.query,
            results=[schemas.DocumentChunkResult(**r) for r in results],
            total=len(results),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na busca semântica: {str(exc)}")


@router.post("/brain/upload", response_model=schemas.DocumentIngestResponse)
async def brain_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Recebe um PDF via upload, processa e indexa no banco.

    Pipeline: Upload → extração de texto → chunking → embeddings → pgvector
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    try:
        import io

        contents = await file.read()
        pdf_stream = io.BytesIO(contents)
        result = await BrainService.ingest_pdf(
            file_path=pdf_stream,
            db=db,
            filename=file.filename,
        )
        return schemas.DocumentIngestResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na ingestão: {str(exc)}")


@router.post("/brain/ingest", response_model=schemas.DocumentIngestResponse)
async def brain_ingest(file_path: str, db: Session = Depends(get_db)):
    """
    Ingere um PDF local (caminho no servidor) no banco de dados.
    """
    try:
        result = await BrainService.ingest_pdf(file_path=file_path, db=db)
        return schemas.DocumentIngestResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na ingestão: {str(exc)}")


@router.get("/brain/status")
def brain_status(db: Session = Depends(get_db)):
    """
    Retorna estatísticas da base de conhecimento documental.
    """
    return BrainService.count_chunks(db)
