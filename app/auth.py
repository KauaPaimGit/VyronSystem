"""
Módulo de Autenticação
Funções para hash de senhas e verificação de credenciais
"""
import bcrypt
from sqlalchemy.orm import Session
from app.models import User
from datetime import datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado
    
    Args:
        plain_password: Senha fornecida pelo usuário
        hashed_password: Hash armazenado no banco de dados
        
    Returns:
        bool: True se a senha estiver correta, False caso contrário
    """
    # Converte strings para bytes
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    
    # Verifica usando bcrypt
    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """
    Gera um hash bcrypt da senha
    
    Args:
        password: Senha em texto plano
        
    Returns:
        str: Hash da senha para armazenar no banco
    """
    # Converte para bytes
    password_bytes = password.encode('utf-8')
    
    # Gera salt e hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Retorna como string
    return hashed.decode('utf-8')


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Autentica um usuário verificando username e senha
    
    Args:
        db: Sessão do banco de dados
        username: Nome de usuário
        password: Senha em texto plano
        
    Returns:
        User: Objeto User se autenticado com sucesso
        None: Se credenciais inválidas ou usuário não existe
    """
    # Busca o usuário pelo username
    user = db.query(User).filter(User.username == username).first()
    
    # Se não encontrou o usuário ou senha não confere
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    
    # Verifica se o usuário está ativo
    if not user.is_active:
        return None
    
    # Atualiza último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user
