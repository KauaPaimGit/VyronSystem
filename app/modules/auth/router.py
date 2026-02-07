"""
Auth Router — Login, Segurança e Diagnóstico de Banco
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import authenticate_user

router = APIRouter(tags=["Auth"])


# ── Schemas locais (leves, específicos do router) ────────────
class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Schema para resposta de login"""
    message: str
    user_role: str
    username: str
    token: str


# ── Rotas ────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de autenticação — Login.

    Recebe username e password, verifica as credenciais e retorna
    informações do usuário autenticado.
    """
    user = authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas. Verifique seu usuário e senha.",
        )

    return LoginResponse(
        message="Login realizado com sucesso",
        user_role=user.role,
        username=user.username,
        token=f"fake-jwt-token-{user.id}",  # Em produção, use JWT real
    )


@router.get("/db-test")
def test_database_connection(db: Session = Depends(get_db)):
    """Testa a conexão com o banco e verifica se o pgvector está ativo."""
    try:
        result = db.execute(text("SELECT 1")).scalar()
        vector_check = db.execute(
            text("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")
        ).scalar()

        return {
            "database_connection": "OK" if result == 1 else "FAIL",
            "pgvector_extension": "INSTALLED" if vector_check > 0 else "MISSING",
            "sqlalchemy_mode": "Working",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
