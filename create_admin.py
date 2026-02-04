"""
Script para criar o primeiro usuário administrador
Execute este script uma única vez para criar o usuário admin padrão.

Uso:
    python create_admin.py
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import User, Base
from app.auth import get_password_hash

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/agency_os"
)

def create_admin_user():
    """
    Cria um usuário administrador padrão no banco de dados
    """
    print("=" * 60)
    print("🔐 CRIAÇÃO DE USUÁRIO ADMINISTRADOR")
    print("=" * 60)
    
    # Conecta ao banco
    print(f"\n📡 Conectando ao banco de dados...")
    print(f"   URL: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Verifica se as tabelas existem
        print("\n🔍 Verificando tabelas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas verificadas/criadas com sucesso")
        
        # Dados do administrador
        admin_username = "admin"
        admin_email = "admin@vyron.com"
        admin_password = "senha123"
        
        # Verifica se já existe um admin
        existing_user = db.query(User).filter(User.username == admin_username).first()
        
        if existing_user:
            print(f"\n⚠️  Usuário '{admin_username}' já existe no banco de dados!")
            print(f"   ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            print(f"   Role: {existing_user.role}")
            print(f"   Criado em: {existing_user.created_at}")
            
            # Pergunta se deseja atualizar a senha
            print("\n❓ Deseja atualizar a senha deste usuário? (s/n): ", end="")
            resposta = input().strip().lower()
            
            if resposta == 's':
                # Atualiza a senha
                existing_user.password_hash = get_password_hash(admin_password)
                db.commit()
                print("\n✅ Senha atualizada com sucesso!")
                print(f"\n🔑 Credenciais:")
                print(f"   Usuário: {admin_username}")
                print(f"   Senha: {admin_password}")
            else:
                print("\n❌ Operação cancelada.")
        else:
            # Cria o novo usuário
            print(f"\n🔨 Criando usuário administrador...")
            
            # Hash da senha
            print(f"   Gerando hash da senha...")
            try:
                password_hash = get_password_hash(admin_password)
                print(f"   ✅ Hash gerado com sucesso")
            except Exception as e:
                print(f"   ❌ Erro ao gerar hash: {e}")
                raise
            
            # Cria o objeto User
            new_admin = User(
                username=admin_username,
                email=admin_email,
                password_hash=password_hash,
                role="admin",
                is_active=True
            )
            
            # Adiciona ao banco
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            
            print("✅ Usuário criado com sucesso!")
            print(f"\n📋 Detalhes do usuário:")
            print(f"   ID: {new_admin.id}")
            print(f"   Usuário: {new_admin.username}")
            print(f"   Email: {new_admin.email}")
            print(f"   Role: {new_admin.role}")
            print(f"   Criado em: {new_admin.created_at}")
            
            print(f"\n🔑 Credenciais de acesso:")
            print(f"   Usuário: {admin_username}")
            print(f"   Senha: {admin_password}")
            
            print("\n⚠️  IMPORTANTE:")
            print("   - Guarde estas credenciais em local seguro")
            print("   - Altere a senha após o primeiro login")
            print("   - Não compartilhe estas informações")
        
        # Fecha a conexão
        db.close()
        
        print("\n" + "=" * 60)
        print("✅ Processo concluído!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        print(f"\n🔍 Detalhes do erro:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print("\n💡 Dicas:")
        print("   - Verifique se o PostgreSQL está rodando")
        print("   - Verifique as credenciais no arquivo .env")
        print("   - Verifique se o banco 'agency_os' existe")
        sys.exit(1)


if __name__ == "__main__":
    create_admin_user()
