"""
Database Connection Manager
Configuração do SQLAlchemy 2.0 para conexão com PostgreSQL
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# URL de conexão com fallback para default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/agency_os"
)

# Engine com configurações otimizadas
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Desabilitado para logs limpos - apenas erros aparecerão
    pool_pre_ping=True,  # Verifica conexão antes de usar
    pool_size=10,  # Tamanho do pool de conexões
    max_overflow=20,  # Conexões extras permitidas
)

# SessionLocal para criar sessões de banco
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa para os modelos
class Base(DeclarativeBase):
    """Base class para todos os modelos ORM"""
    pass


# Dependency para FastAPI
def get_db():
    """
    Generator para obter sessão do banco de dados.
    Uso em FastAPI: 
        def endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
