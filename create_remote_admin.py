"""
Script para criar usuário administrador em banco de dados REMOTO (Render)
Execute este script uma única vez após o deploy no Render

Uso:
    python create_remote_admin.py
"""
import os
import sys
import bcrypt
from uuid import uuid4
from sqlalchemy import create_engine, text
from getpass import getpass

def create_remote_admin():
    """
    Cria um usuário administrador no banco de dados remoto (Render)
    """
    print("=" * 70)
    print("🌐 CRIAÇÃO DE ADMIN NO BANCO REMOTO (RENDER)")
    print("=" * 70)
    
    # Solicita a URL do banco de dados
    print("\n📋 Cole a External Database URL do Render:")
    print("   (Formato: postgres://user:pass@host:port/database)")
    db_url = input("\n🔗 Database URL: ").strip()
    
    if not db_url:
        print("❌ URL não pode ser vazia!")
        sys.exit(1)
    
    # Fix para compatibilidade com SQLAlchemy 2.0
    # O Render retorna postgres://, mas SQLAlchemy 2.0 requer postgresql://
    if db_url.startswith("postgres://"):
        print("\n🔧 Convertendo postgres:// para postgresql://")
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        print("   ✅ URL convertida")
    
    # Solicita credenciais do admin
    print("\n" + "=" * 70)
    print("👤 CREDENCIAIS DO ADMINISTRADOR")
    print("=" * 70)
    
    admin_username = input("\n📝 Nome de usuário (padrão: admin): ").strip() or "admin"
    admin_email = input("📧 Email (padrão: admin@agencyos.com): ").strip() or "admin@agencyos.com"
    
    # Solicita senha com confirmação
    while True:
        admin_password = getpass("🔒 Senha (mínimo 8 caracteres): ")
        
        if len(admin_password) < 8:
            print("❌ Senha muito curta! Mínimo 8 caracteres.")
            continue
        
        password_confirm = getpass("🔒 Confirme a senha: ")
        
        if admin_password != password_confirm:
            print("❌ Senhas não conferem! Tente novamente.")
            continue
        
        break
    
    # Gera hash bcrypt da senha
    print("\n🔐 Gerando hash bcrypt da senha...")
    try:
        password_bytes = admin_password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        print(f"   ✅ Hash gerado com sucesso")
        
        # Testa o hash
        test_verify = bcrypt.checkpw(password_bytes, password_hash.encode('utf-8'))
        if not test_verify:
            print("❌ Erro na validação do hash!")
            sys.exit(1)
        print(f"   ✅ Hash validado")
        
    except Exception as e:
        print(f"❌ Erro ao gerar hash: {e}")
        sys.exit(1)
    
    # Conecta ao banco remoto
    print(f"\n📡 Conectando ao banco de dados remoto...")
    print(f"   Host: {db_url.split('@')[1].split(':')[0] if '@' in db_url else 'N/A'}")
    
    try:
        # Cria engine com configuração para conexões remotas
        engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,  # Verifica conexão antes de usar
            pool_size=5,
            max_overflow=10,
            connect_args={
                "connect_timeout": 30,
                "options": "-c statement_timeout=30000"
            }
        )
        
        print("   ✅ Conexão estabelecida")
        
        with engine.connect() as conn:
            # Verifica se a tabela users existe
            print("\n🔍 Verificando tabela users...")
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("⚠️  Tabela 'users' não existe!")
                print("🔨 Criando tabela users...")
                
                conn.execute(text("""
                    CREATE TABLE users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username VARCHAR(100) NOT NULL UNIQUE,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL DEFAULT 'user',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """))
                
                conn.execute(text("CREATE INDEX idx_users_username ON users(username)"))
                conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))
                conn.execute(text("CREATE INDEX idx_users_role ON users(role)"))
                conn.commit()
                
                print("   ✅ Tabela criada com sucesso")
            else:
                print("   ✅ Tabela encontrada")
            
            # Verifica se o usuário já existe
            result = conn.execute(
                text("SELECT id, username, email, role FROM users WHERE username = :username"),
                {"username": admin_username}
            )
            existing = result.fetchone()
            
            if existing:
                print(f"\n⚠️  Usuário '{admin_username}' já existe no banco remoto!")
                print(f"   ID: {existing[0]}")
                print(f"   Email: {existing[2]}")
                print(f"   Role: {existing[3]}")
                
                print("\n❓ Deseja atualizar a senha deste usuário? (s/n): ", end="")
                resposta = input().strip().lower()
                
                if resposta == 's':
                    conn.execute(
                        text("UPDATE users SET password_hash = :hash, updated_at = CURRENT_TIMESTAMP WHERE username = :username"),
                        {"hash": password_hash, "username": admin_username}
                    )
                    conn.commit()
                    print("\n✅ Senha atualizada no banco remoto!")
                else:
                    print("\n❌ Operação cancelada.")
                    return
            else:
                # Cria novo usuário
                print(f"\n🔨 Criando usuário administrador no banco remoto...")
                user_id = str(uuid4())
                
                conn.execute(
                    text("""
                        INSERT INTO users (id, username, email, password_hash, role, is_active)
                        VALUES (:id, :username, :email, :hash, :role, :active)
                    """),
                    {
                        "id": user_id,
                        "username": admin_username,
                        "email": admin_email,
                        "hash": password_hash,
                        "role": "admin",
                        "active": True
                    }
                )
                conn.commit()
                
                print("   ✅ Usuário criado no banco remoto!")
                print(f"\n📋 Detalhes do usuário:")
                print(f"   ID: {user_id}")
                print(f"   Usuário: {admin_username}")
                print(f"   Email: {admin_email}")
                print(f"   Role: admin")
            
            print(f"\n🔑 Credenciais de acesso:")
            print(f"   Usuário: {admin_username}")
            print(f"   Senha: {'*' * len(admin_password)}")
            
            print("\n" + "=" * 70)
            print("🎉 Sucesso: Admin criado na nuvem!")
            print("=" * 70)
            
            print("\n⚠️  IMPORTANTE:")
            print("   - Guarde estas credenciais em local seguro")
            print("   - Use essas credenciais para fazer login no sistema")
            print("   - Não compartilhe estas informações")
            
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        print(f"\n🔍 Detalhes do erro:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print("\n💡 Dicas:")
        print("   - Verifique se a URL está correta")
        print("   - Verifique se o banco está acessível")
        print("   - Verifique as credenciais do banco")
        print("   - Verifique se a extensão gen_random_uuid() está disponível")
        sys.exit(1)


if __name__ == "__main__":
    print("\n💡 DICA: Cole a External Database URL do painel do Render")
    print("   Exemplo: postgres://user:pass@dpg-xxxxx.oregon-postgres.render.com/dbname")
    print()
    
    try:
        create_remote_admin()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário.")
        sys.exit(0)
