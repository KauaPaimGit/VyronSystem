"""
run_migrations.py — Executa migrations SQL via Python (sem acesso ao console SQL)

Projetado para ambientes como Render Free Tier onde não há acesso direto
ao psql. Usa o engine SQLAlchemy do projeto para executar DDL.

Uso:
    python scripts/run_migrations.py

Pipeline:
    1. Garante extensões (vector, uuid-ossp)
    2. Cria tabelas via SQLAlchemy metadata (models.py)
    3. Executa migration SQL incremental (004_add_document_chunks.sql)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que o projeto raiz está no sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text, inspect
from app.database import engine
from app import models  # noqa: F401  — registra todos os modelos na metadata


MIGRATIONS_DIR = ROOT_DIR / "migrations"


def run() -> None:
    """Executa todas as migrations pendentes."""

    print("=" * 60)
    print("🔧  Vyron System — Migration Runner")
    print("=" * 60)

    with engine.connect() as conn:
        # ──────────────────────────────────────────────────
        # 1. EXTENSÕES
        # ──────────────────────────────────────────────────
        print("\n📦  Verificando extensões PostgreSQL...")

        for ext in ("uuid-ossp", "vector"):
            try:
                conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}";'))
                conn.commit()
                print(f"   ✅  {ext}")
            except Exception as exc:
                conn.rollback()
                print(f"   ⚠️  {ext} — {exc}")

        # ──────────────────────────────────────────────────
        # 2. TABELAS VIA SQLALCHEMY (metadata.create_all)
        # ──────────────────────────────────────────────────
        print("\n🗄️  Criando/verificando tabelas via ORM...")
        try:
            models.Base.metadata.create_all(bind=engine)
            print("   ✅  Todas as tabelas verificadas")
        except Exception as exc:
            print(f"   ⚠️  Erro no create_all: {exc}")

        # ──────────────────────────────────────────────────
        # 3. MIGRATION SQL INCREMENTAL
        # ──────────────────────────────────────────────────
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # Lista de migrations a executar (ordem importa)
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        if not migration_files:
            print("\n📂  Nenhum arquivo .sql encontrado em migrations/")
        else:
            print(f"\n📂  {len(migration_files)} migration(s) encontrada(s)")

            for sql_file in migration_files:
                print(f"\n   📄  {sql_file.name}")

                # Heurística simples: se a migration cria uma tabela que já existe,
                # pula para não gerar conflito de índice IVFFlat em tabela vazia.
                sql_content = sql_file.read_text(encoding="utf-8")

                # Executa cada statement separado por ";"
                statements = [
                    s.strip()
                    for s in sql_content.split(";")
                    if s.strip() and not s.strip().startswith("--")
                ]

                success = 0
                skipped = 0
                errors = 0

                for stmt in statements:
                    # Pula índices IVFFlat — eles falham em tabelas vazias
                    # e o pgvector faz seq scan automaticamente nesse caso.
                    if "ivfflat" in stmt.lower():
                        print(f"      ⏭️  IVFFlat index — adiado (requer dados)")
                        skipped += 1
                        continue

                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                        success += 1
                    except Exception as exc:
                        conn.rollback()
                        err_msg = str(exc).split("\n")[0]
                        # "already exists" é esperado em re-runs
                        if "already exists" in err_msg.lower():
                            skipped += 1
                        else:
                            print(f"      ⚠️  {err_msg[:120]}")
                            errors += 1

                print(f"      ✅ {success} executado(s) | ⏭️ {skipped} pulado(s) | ⚠️ {errors} erro(s)")

    # ──────────────────────────────────────────────────
    # 4. VERIFICAÇÃO FINAL
    # ──────────────────────────────────────────────────
    print("\n" + "─" * 60)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊  Tabelas no banco: {len(tables)}")
    for t in sorted(tables):
        print(f"   • {t}")

    has_chunks = "document_chunks" in tables
    print(f"\n{'✅' if has_chunks else '❌'}  document_chunks: {'OK' if has_chunks else 'NÃO CRIADA'}")
    print("─" * 60)
    print("🏁  Migration concluída.\n")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"\n❌  Erro fatal: {exc}")
        sys.exit(1)
