"""
ingest_document.py — CLI para ingestão de PDFs no Vyron System

Uso:
    python scripts/ingest_document.py "C:/Users/Kauã/Desktop/proposta.pdf"
    python scripts/ingest_document.py ./docs/manual.pdf

O script:
  1. Lê o PDF informado
  2. Divide o conteúdo em chunks de ~1 000 caracteres
  3. Gera embeddings via OpenAI (text-embedding-3-small)
  4. Persiste tudo na tabela document_chunks (PostgreSQL + pgvector)
"""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path

# Garante que o projeto raiz está no sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal
from app.brain_service import BrainService


async def main(file_path: str) -> None:
    """Pipeline principal de ingestão."""

    path = Path(file_path)

    # ── Validações ──────────────────────────
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {path}")
        sys.exit(1)

    if path.suffix.lower() != ".pdf":
        print(f"❌ Formato não suportado: {path.suffix}. Apenas PDFs são aceitos.")
        sys.exit(1)

    print("=" * 60)
    print(f"📥  Vyron System — Ingestão de Documento")
    print(f"📄  Arquivo : {path.resolve()}")
    print("=" * 60)

    db = SessionLocal()
    try:
        result = await BrainService.ingest_pdf(
            file_path=path,
            db=db,
            filename=path.name,
        )
        print()
        print("─" * 60)
        print(f"✅  Ingestão finalizada com sucesso!")
        print(f"    Arquivo  : {result['filename']}")
        print(f"    Páginas  : {result['total_pages']}")
        print(f"    Chunks   : {result['total_chunks']}")
        print("─" * 60)
    except FileNotFoundError as exc:
        print(f"\n❌ Arquivo não encontrado: {exc}")
        sys.exit(1)
    except RuntimeError as exc:
        print(f"\n❌ Erro no pipeline: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ Erro inesperado durante ingestão: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/ingest_document.py <caminho_do_pdf>")
        print('  Ex: python scripts/ingest_document.py "C:/Users/Kauã/Desktop/proposta.pdf"')
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
