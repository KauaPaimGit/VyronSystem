"""
Script de Migração: Atualizar campo 'status' dos projetos para os valores do Kanban

Atualiza os projetos existentes para usar os novos valores de status do sistema Kanban:
- 'planning' → 'Negociação'
- Adiciona suporte para: 'Negociação', 'Em Produção', 'Concluído'
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Erro: DATABASE_URL não encontrada no arquivo .env")
    exit(1)

# Cria engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 60)
print("🔄 MIGRAÇÃO: Atualização de Status para Sistema Kanban")
print("=" * 60)

try:
    # Verifica se a coluna status já existe
    result = session.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'projects' 
        AND column_name = 'status'
    """))
    
    if not result.fetchone():
        print("✅ Coluna 'status' não existe. Nada a fazer - será criada automaticamente pelo SQLAlchemy.")
        session.close()
        exit(0)
    
    # Mapeia valores antigos para novos
    status_mapping = {
        'planning': 'Negociação',
        'active': 'Em Produção',
        'completed': 'Concluído',
        'on_hold': 'Negociação',
        'cancelled': 'Concluído'
    }
    
    # Busca todos os projetos
    projects = session.execute(text("SELECT id, status FROM projects"))
    projects_list = projects.fetchall()
    
    if not projects_list:
        print("ℹ️ Nenhum projeto encontrado no banco.")
        session.close()
        exit(0)
    
    print(f"📊 {len(projects_list)} projeto(s) encontrado(s)\n")
    
    updated_count = 0
    
    for project in projects_list:
        project_id, current_status = project
        
        # Determina o novo status
        if current_status in status_mapping:
            new_status = status_mapping[current_status]
        elif current_status in ['Negociação', 'Em Produção', 'Concluído']:
            # Já está no formato correto
            new_status = current_status
        else:
            # Status desconhecido, deixa como 'Negociação'
            new_status = 'Negociação'
            print(f"⚠️ Status desconhecido '{current_status}' para projeto {project_id} - definido como 'Negociação'")
        
        if current_status != new_status:
            # Atualiza o status
            session.execute(
                text("UPDATE projects SET status = :new_status WHERE id = :project_id"),
                {"new_status": new_status, "project_id": project_id}
            )
            updated_count += 1
            print(f"✅ Projeto {project_id}: '{current_status}' → '{new_status}'")
    
    # Commit das alterações
    session.commit()
    
    print("\n" + "=" * 60)
    print(f"✅ Migração concluída com sucesso!")
    print(f"📝 {updated_count} projeto(s) atualizado(s)")
    print(f"📊 {len(projects_list) - updated_count} projeto(s) já estavam corretos")
    print("=" * 60)
    
    print("\n💡 Valores de status disponíveis:")
    print("   • Negociação")
    print("   • Em Produção")
    print("   • Concluído")
    
except Exception as e:
    session.rollback()
    print(f"\n❌ Erro durante a migração: {e}")
    print("\n⚠️ Rollback realizado - nenhuma alteração foi aplicada")
    exit(1)
finally:
    session.close()
