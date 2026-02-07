"""
BrainService — Ingestão e busca semântica de documentos (RAG)

Responsável por:
  1. Extrair texto de PDFs (pypdf)
  2. Dividir em chunks (langchain-text-splitters)
  3. Gerar embeddings (OpenAI text-embedding-3-small)
  4. Persistir chunks + vetores no PostgreSQL/pgvector
  5. Busca de similaridade por cosseno (operador <=>)
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import DocumentChunk

load_dotenv()

# ── OpenAI client ────────────────────────────────────────────────
_api_key = os.getenv("OPENAI_API_KEY")
_openai: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=_api_key) if _api_key else None

# ── Text Splitter ────────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


class BrainService:
    """Serviço de ingestão e busca semântica para o Agency Brain."""

    # ────────────────────────────────────────────────────────────
    # 1. PROCESS_PDF — Extração + Chunking (sem side effects)
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def process_pdf(
        source: str | Path | io.BytesIO,
        filename: str | None = None,
    ) -> dict:
        """
        Extrai texto de um PDF e divide em chunks.

        Aceita tanto um caminho de arquivo quanto bytes em memória
        (útil para uploads via API/Streamlit).

        Args:
            source: Caminho do arquivo ou BytesIO com o conteúdo do PDF.
            filename: Nome do arquivo (obrigatório se source for BytesIO).

        Returns:
            dict com keys: filename, full_text, chunks (list[str]), total_pages.

        Raises:
            FileNotFoundError: Se o caminho não existir.
            ValueError: Se nenhum texto puder ser extraído.
        """
        # Resolve reader e filename
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {path}")
            reader = PdfReader(str(path))
            filename = filename or path.name
        else:
            # BytesIO (upload)
            reader = PdfReader(source)
            if not filename:
                filename = "upload.pdf"

        # Extrai texto de cada página
        pages_text: list[str] = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pages_text.append(extracted)

        full_text = "\n\n".join(pages_text)
        if not full_text.strip():
            raise ValueError(
                f"Nenhum texto extraído de {filename}. "
                "O PDF pode conter apenas imagens (não suportado ainda)."
            )

        # Divide em chunks
        chunks = _splitter.split_text(full_text)

        return {
            "filename": filename,
            "full_text": full_text,
            "chunks": chunks,
            "total_pages": len(reader.pages),
        }

    # ────────────────────────────────────────────────────────────
    # 2. GENERATE_EMBEDDINGS — Vetorização em batch
    # ────────────────────────────────────────────────────────────

    @staticmethod
    async def generate_embeddings(texts: list[str]) -> list[list[float]]:
        """
        Gera embeddings em batch usando OpenAI text-embedding-3-small.

        Args:
            texts: Lista de strings para vetorizar.

        Returns:
            Lista de vetores (1 536 dims cada).

        Fallback:
            Se não houver chave API ou ocorrer erro, retorna vetores zerados.
        """
        if not _openai:
            print("⚠️  OPENAI_API_KEY não configurada. Retornando vetores zerados.")
            return [[0.0] * 1536 for _ in texts]

        try:
            response = await _openai.embeddings.create(
                input=texts,
                model="text-embedding-3-small",
            )
            sorted_data = sorted(response.data, key=lambda d: d.index)
            return [item.embedding for item in sorted_data]
        except Exception as exc:
            print(f"⚠️  Erro ao gerar embeddings: {exc}")
            return [[0.0] * 1536 for _ in texts]

    # ────────────────────────────────────────────────────────────
    # 3. INGEST — Pipeline completo (process + embed + persist)
    # ────────────────────────────────────────────────────────────

    @classmethod
    async def ingest_pdf(
        cls,
        file_path: str | Path | io.BytesIO,
        db: Session,
        *,
        filename: str | None = None,
        batch_size: int = 50,
    ) -> dict:
        """
        Pipeline completo de ingestão.

        Args:
            file_path: Caminho do PDF (str/Path) ou BytesIO para uploads.
            db: Sessão SQLAlchemy.
            filename: Nome override (útil para uploads via BytesIO).
            batch_size: Quantos chunks por batch na API de embeddings.

        Returns:
            Dicionário com estatísticas da ingestão.

        Raises:
            FileNotFoundError: Se o caminho informado não existir.
            RuntimeError: Se a leitura do PDF ou a geração de embeddings falhar.
        """
        # ── 1. Processar PDF (extrair + chunkar) ────────────────
        try:
            processed = cls.process_pdf(file_path, filename=filename)
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Falha ao ler/processar o PDF: {exc}. "
                "Verifique se o arquivo é um PDF válido e não está corrompido."
            ) from exc

        fname = processed["filename"]
        chunks = processed["chunks"]
        total_pages = processed["total_pages"]
        print(f"📄  {fname}: {len(chunks)} chunks de {total_pages} páginas")

        # ── 2. Gerar embeddings em batches ──────────────────────
        all_embeddings: list[list[float]] = []
        try:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(chunks) - 1) // batch_size + 1
                print(f"🔢  Embeddings batch {batch_num}/{total_batches}...")
                batch_emb = await cls.generate_embeddings(batch)
                all_embeddings.extend(batch_emb)
        except Exception as exc:
            raise RuntimeError(
                f"Falha ao gerar embeddings via OpenAI: {exc}. "
                "Verifique sua OPENAI_API_KEY e conectividade."
            ) from exc

        # ── 3. Persistir no banco ───────────────────────────────
        print(f"💾  Salvando {len(chunks)} chunks...")
        records: list[DocumentChunk] = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks, all_embeddings)):
            records.append(
                DocumentChunk(
                    id=uuid4(),
                    filename=fname,
                    chunk_index=idx,
                    content=chunk_text,
                    embedding=embedding,
                    metadata_json={
                        "total_pages": total_pages,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk_text),
                    },
                )
            )

        try:
            db.add_all(records)
            db.commit()
        except Exception as exc:
            db.rollback()
            raise RuntimeError(f"Erro ao salvar chunks no banco: {exc}") from exc

        summary = {
            "filename": fname,
            "total_pages": total_pages,
            "total_chunks": len(chunks),
            "status": "success",
        }
        print(f"✅  Ingestão concluída: {summary}")
        return summary

    # ────────────────────────────────────────────────────────────
    # 4. SEMANTIC_SEARCH — Busca por cosseno (<=>)
    # ────────────────────────────────────────────────────────────

    @classmethod
    async def semantic_search(
        cls,
        query: str,
        db: Session,
        *,
        limit: int = 3,
        filename_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Busca os chunks mais relevantes usando distância de cosseno.

        Usa o operador <=> do pgvector para calcular a distância.

        Args:
            query: Texto da pergunta em linguagem natural.
            db: Sessão SQLAlchemy.
            limit: Quantidade máxima de resultados (default: 3).
            filename_filter: (Opcional) Filtrar por nome de arquivo.

        Returns:
            Lista de dicts com: id, filename, chunk_index, content, score, metadata.
        """
        query_embedding = (await cls.generate_embeddings([query]))[0]

        base_query = (
            db.query(
                DocumentChunk.id,
                DocumentChunk.filename,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                DocumentChunk.metadata_json,
                DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .filter(DocumentChunk.embedding.isnot(None))
        )

        if filename_filter:
            base_query = base_query.filter(DocumentChunk.filename == filename_filter)

        results = base_query.order_by("distance").limit(limit).all()

        return [
            {
                "id": str(row.id),
                "filename": row.filename,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "score": round(1 - row.distance, 4),
                "metadata": row.metadata_json,
            }
            for row in results
        ]

    # ────────────────────────────────────────────────────────────
    # 5. CONTAGEM DE CHUNKS INDEXADOS
    # ────────────────────────────────────────────────────────────

    @staticmethod
    def count_chunks(db: Session) -> dict:
        """
        Retorna estatísticas dos documentos indexados.

        Returns:
            dict com total_chunks, total_files, files (lista de nomes).
        """
        try:
            total = db.query(func.count(DocumentChunk.id)).scalar() or 0
            files_query = (
                db.query(
                    DocumentChunk.filename,
                    func.count(DocumentChunk.id).label("chunks"),
                )
                .group_by(DocumentChunk.filename)
                .all()
            )
            files = [{"filename": r.filename, "chunks": r.chunks} for r in files_query]
            return {
                "total_chunks": total,
                "total_files": len(files),
                "files": files,
            }
        except Exception:
            return {"total_chunks": 0, "total_files": 0, "files": []}
