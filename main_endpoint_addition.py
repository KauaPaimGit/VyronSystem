# Adicione este endpoint ao final do arquivo main.py, após o delete_interaction

@app.get("/clients/{client_id}/interactions")
def get_client_interactions_endpoint(client_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Busca as últimas interações de um cliente para exibir na timeline.
    
    Args:
        client_id: UUID do cliente
        limit: Número máximo de interações (padrão: 10)
        
    Returns:
        Lista de interações com date, type, description, sentiment
    """
    from app.services import get_client_interactions
    
    # Valida se o cliente existe
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Busca as interações
    interactions = get_client_interactions(db, client_id, limit)
    
    return {
        "client_id": client_id,
        "client_name": client.name,
        "total": len(interactions),
        "interactions": interactions
    }
