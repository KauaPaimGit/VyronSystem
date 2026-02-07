"""
Vyron System — Core API (Modular)

Entry point da aplicação FastAPI.
Toda lógica de rotas foi movida para app/modules/<domain>/router.py.
Este arquivo apenas:
  1. Cria as tabelas
  2. Configura CORS
  3. Registra os routers
  4. Adiciona o middleware de auditoria
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app import models

# ── Routers modulares ────────────────────────────────────────────
from app.modules.auth.router import router as auth_router
from app.modules.sales.router import router as sales_router
from app.modules.brain.router import router as brain_router
from app.modules.finance.router import router as finance_router

# ── Middleware de auditoria ──────────────────────────────────────
from app.middleware.audit import AuditMiddleware

# ============================================
# CRIA AS TABELAS NO BANCO DE DADOS
# ============================================
# print("[INFO] Criando tabelas no banco de dados...")
try:
    models.Base.metadata.create_all(bind=engine)
    # print("[OK] Tabelas criadas/verificadas com sucesso!")
except Exception as e:
    print(f"[ERROR] Erro ao criar tabelas: {e}")
    raise

# ============================================
# APP FASTAPI
# ============================================
app = FastAPI(
    title="Vyron System - Core API",
    description="Enterprise AI ERP — Sistema Inteligente de Gestão Empresarial (Modular)",
    version="1.2.0",
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Audit Middleware ───────────────────────────────────────────
app.add_middleware(AuditMiddleware)


# ── Health-check ─────────────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "running", "service": "Vyron System API", "version": "1.2.0"}


# ── Registro dos Routers ───────────────────────────────────────
app.include_router(auth_router)      # /login, /db-test
app.include_router(sales_router)     # /clients/*, /interactions/*, /radar/*
app.include_router(brain_router)     # /ai/*, /brain/*
app.include_router(finance_router)   # /projects/*, /revenues/*, /expenses/*, /manual/*
