"""
Finance Router — Projetos, Receitas, Despesas, Dashboard Financeiro, Marketing KPIs e PDF
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import json

from app.database import get_db
from app import models, schemas
from app.services import (
    generate_embedding,
    generate_project_pdf,
    _execute_create_project,
    _execute_add_expense,
    _execute_add_marketing_stats,
)

router = APIRouter(tags=["Finance"])


# ══════════════════════════════════════════════
# PROJETOS
# ══════════════════════════════════════════════

@router.post("/projects/", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Cria um novo projeto vinculado a um cliente."""
    client = db.query(models.Client).filter(models.Client.id == project.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    orm_data = {
        "client_id": project.client_id,
        "name": project.name,
        "type": project.project_type,
        "category": "general",
        "contract_value": project.value,
        "start_date": project.start_date,
        "end_date": project.end_date,
    }

    db_project = models.Project(**orm_data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return schemas.ProjectResponse(
        id=db_project.id,
        client_id=db_project.client_id,
        name=db_project.name,
        description=None,
        project_type=db_project.type,
        value=db_project.contract_value,
        start_date=db_project.start_date,
        end_date=db_project.end_date,
        created_at=db_project.created_at,
    )


@router.get("/projects/", response_model=List[schemas.ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista todos os projetos cadastrados."""
    query = db.query(models.Project)
    if client_id:
        query = query.filter(models.Project.client_id == client_id)

    projects = query.offset(skip).limit(limit).all()

    return [
        schemas.ProjectResponse(
            id=p.id,
            client_id=p.client_id,
            client_name=p.client.name if p.client else "Cliente não encontrado",
            name=p.name,
            description=None,
            project_type=p.type,
            value=p.contract_value,
            status=p.status,
            start_date=p.start_date,
            end_date=p.end_date,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retorna os detalhes de um projeto específico."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return schemas.ProjectResponse(
        id=project.id,
        client_id=project.client_id,
        client_name=project.client.name if project.client else "Cliente não encontrado",
        name=project.name,
        description=None,
        project_type=project.type,
        value=project.contract_value,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
    )


class UpdateStatusRequest(BaseModel):
    status: str


@router.patch("/projects/{project_id}/status")
def update_project_status(project_id: str, request: UpdateStatusRequest, db: Session = Depends(get_db)):
    """Atualiza o status de um projeto no sistema Kanban."""
    valid_statuses = ["Negociação", "Em Produção", "Concluído"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status inválido. Use: {', '.join(valid_statuses)}",
        )

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    project.status = request.status
    db.commit()
    db.refresh(project)

    return {
        "message": "Status atualizado com sucesso",
        "project_id": str(project.id),
        "project_name": project.name,
        "new_status": project.status,
    }


# ══════════════════════════════════════════════
# ENTRADA MANUAL DE DADOS
# ══════════════════════════════════════════════

@router.post("/manual/projects", status_code=201)
async def create_project_manual(
    project_name: str,
    client_name: str,
    budget: float,
    product_price: float = 0.0,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Cria um novo projeto via entrada manual."""
    result_json = await _execute_create_project(
        db=db,
        project_name=project_name,
        client_name=client_name,
        budget=budget,
        product_price=product_price,
        description=description,
    )
    result = json.loads(result_json)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/manual/expenses", status_code=201)
async def create_expense_manual(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """Registra uma nova despesa via entrada manual."""
    project = None
    if expense.project_id:
        project = db.query(models.Project).filter(models.Project.id == expense.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

    db_expense = models.Expense(
        project_id=expense.project_id,
        category=expense.category,
        description=expense.description,
        amount=expense.amount,
        due_date=expense.due_date,
        paid_date=expense.paid_date,
        status=expense.status,
        is_fixed_cost=expense.is_fixed_cost,
        is_project_related=expense.is_project_related,
        supplier=expense.supplier,
        payment_method=expense.payment_method,
        notes=expense.notes,
    )
    db.add(db_expense)
    db.flush()

    log_content = f"SISTEMA: Despesa de R$ {float(expense.amount):,.2f} - {expense.description}"
    if project:
        log_content += f" no projeto '{project.name}'"
    log_content += f". Categoria: {expense.category}. Vencimento: {expense.due_date.strftime('%d/%m/%Y')}."

    embedding = await generate_embedding(log_content)

    client_id = None
    if project and project.client_id:
        client_id = project.client_id
    else:
        first_client = db.query(models.Client).first()
        if first_client:
            client_id = first_client.id

    if client_id:
        interaction = models.Interaction(
            client_id=client_id,
            type="system_log",
            content=log_content,
            content_embedding=embedding,
            interaction_date=datetime.now(),
        )
        db.add(interaction)

    db.commit()
    db.refresh(db_expense)

    return {
        "status": "success",
        "expense_id": str(db_expense.id),
        "message": f"✅ Despesa de R$ {float(expense.amount):,.2f} registrada com sucesso!",
    }


@router.post("/manual/marketing-metrics", status_code=201)
async def create_marketing_metrics_manual(metric: schemas.MarketingMetricCreate, db: Session = Depends(get_db)):
    """Registra métricas de marketing via entrada manual."""
    project = db.query(models.Project).filter(models.Project.id == metric.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    result_json = await _execute_add_marketing_stats(
        db=db,
        project_name=project.name,
        date=metric.date,
        impressions=metric.impressions,
        clicks=metric.clicks,
        leads=metric.leads,
        conversions=metric.conversions,
        cost=float(metric.cost) if metric.cost else None,
        platform=metric.platform,
        source="manual",
    )

    result = json.loads(result_json)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ══════════════════════════════════════════════
# RECEITAS
# ══════════════════════════════════════════════

@router.post("/revenues/", response_model=schemas.RevenueResponse, status_code=201)
def create_revenue(revenue: schemas.RevenueCreate, db: Session = Depends(get_db)):
    """Lança uma receita no sistema."""
    client = db.query(models.Client).filter(models.Client.id == revenue.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    project = db.query(models.Project).filter(models.Project.id == revenue.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    db_revenue = models.Revenue(
        client_id=revenue.client_id,
        project_id=revenue.project_id,
        description=revenue.description,
        amount=revenue.amount,
        due_date=revenue.received_at,
        paid_date=revenue.received_at,
        status="paid",
    )
    db.add(db_revenue)
    db.commit()
    db.refresh(db_revenue)

    return schemas.RevenueResponse(
        id=db_revenue.id,
        project_id=db_revenue.project_id,
        client_id=db_revenue.client_id,
        description=db_revenue.description,
        amount=db_revenue.amount,
        category=revenue.category,
        received_at=db_revenue.paid_date,
        status=db_revenue.status,
        created_at=db_revenue.created_at,
    )


@router.get("/revenues/", response_model=List[schemas.RevenueResponse])
def list_revenues(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = None,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista todas as receitas cadastradas."""
    query = db.query(models.Revenue)
    if project_id:
        query = query.filter(models.Revenue.project_id == project_id)
    if client_id:
        query = query.filter(models.Revenue.client_id == client_id)
    query = query.order_by(models.Revenue.created_at.desc())
    revenues = query.offset(skip).limit(limit).all()

    return [
        schemas.RevenueResponse(
            id=r.id,
            project_id=r.project_id,
            client_id=r.client_id,
            description=r.description,
            amount=r.amount,
            category=schemas.RevenueCategory.other,
            received_at=r.paid_date or r.due_date,
            status=r.status,
            created_at=r.created_at,
        )
        for r in revenues
    ]


@router.get("/revenues/{revenue_id}", response_model=schemas.RevenueResponse)
def get_revenue(revenue_id: str, db: Session = Depends(get_db)):
    """Retorna os detalhes de uma receita específica."""
    revenue = db.query(models.Revenue).filter(models.Revenue.id == revenue_id).first()
    if not revenue:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    return schemas.RevenueResponse(
        id=revenue.id,
        project_id=revenue.project_id,
        client_id=revenue.client_id,
        description=revenue.description,
        amount=revenue.amount,
        category=schemas.RevenueCategory.other,
        received_at=revenue.paid_date or revenue.due_date,
        status=revenue.status,
        created_at=revenue.created_at,
    )


# ══════════════════════════════════════════════
# DESPESAS
# ══════════════════════════════════════════════

@router.post("/expenses/", response_model=schemas.ExpenseResponse, status_code=201)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """Lança uma despesa no sistema."""
    if expense.project_id:
        project = db.query(models.Project).filter(models.Project.id == expense.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")

    is_project_related = expense.project_id is not None

    db_expense = models.Expense(
        project_id=expense.project_id,
        category=expense.category,
        description=expense.description,
        amount=expense.amount,
        due_date=expense.due_date,
        paid_date=expense.paid_date,
        status=expense.status,
        is_fixed_cost=expense.is_fixed_cost,
        is_project_related=is_project_related,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return schemas.ExpenseResponse(
        id=db_expense.id,
        project_id=db_expense.project_id,
        description=db_expense.description,
        amount=db_expense.amount,
        category=db_expense.category,
        due_date=db_expense.due_date,
        paid_date=db_expense.paid_date,
        status=db_expense.status,
        is_fixed_cost=db_expense.is_fixed_cost,
        is_project_related=db_expense.is_project_related,
        created_at=db_expense.created_at,
    )


@router.get("/expenses/", response_model=List[schemas.ExpenseResponse])
def list_expenses(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista todas as despesas cadastradas."""
    query = db.query(models.Expense)
    if project_id:
        query = query.filter(models.Expense.project_id == project_id)
    query = query.order_by(models.Expense.created_at.desc())
    expenses = query.offset(skip).limit(limit).all()

    return [
        schemas.ExpenseResponse(
            id=e.id,
            project_id=e.project_id,
            description=e.description,
            amount=e.amount,
            category=e.category,
            due_date=e.due_date,
            paid_date=e.paid_date,
            status=e.status,
            is_fixed_cost=e.is_fixed_cost,
            is_project_related=e.is_project_related,
            created_at=e.created_at,
        )
        for e in expenses
    ]


@router.get("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def get_expense(expense_id: str, db: Session = Depends(get_db)):
    """Retorna os detalhes de uma despesa específica."""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    return schemas.ExpenseResponse(
        id=expense.id,
        project_id=expense.project_id,
        description=expense.description,
        amount=expense.amount,
        category=expense.category,
        due_date=expense.due_date,
        paid_date=expense.paid_date,
        status=expense.status,
        is_fixed_cost=expense.is_fixed_cost,
        is_project_related=expense.is_project_related,
        created_at=expense.created_at,
    )


# ══════════════════════════════════════════════
# DASHBOARD FINANCEIRO & KPIs
# ══════════════════════════════════════════════

@router.get("/projects/{project_id}/financial-dashboard", response_model=schemas.FinancialSummary)
def get_project_financial_dashboard(project_id: str, db: Session = Depends(get_db)):
    """Retorna um resumo financeiro consolidado do projeto."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    total_revenue = db.query(func.sum(models.Revenue.amount)).filter(
        models.Revenue.project_id == project_id
    ).scalar()

    total_expense = db.query(func.sum(models.Expense.amount)).filter(
        models.Expense.project_id == project_id
    ).scalar()

    total_revenue = float(total_revenue) if total_revenue else 0.0
    total_expense = float(total_expense) if total_expense else 0.0
    net_profit = total_revenue - total_expense

    if total_revenue > 0:
        margin_str = f"{(net_profit / total_revenue) * 100:.1f}%"
    else:
        margin_str = "0.0%"

    return schemas.FinancialSummary(
        total_revenue=total_revenue,
        total_expense=total_expense,
        net_profit=net_profit,
        margin_percentage=margin_str,
    )


@router.get("/projects/{project_id}/marketing-kpis", response_model=schemas.MarketingKPIs)
def get_project_marketing_kpis(project_id: str, db: Session = Depends(get_db)):
    """Retorna KPIs de marketing calculados para um projeto."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    metrics = db.query(models.MarketingMetric).filter(
        models.MarketingMetric.project_id == project_id
    ).all()

    if not metrics:
        return schemas.MarketingKPIs(
            total_impressions=0, total_clicks=0, total_leads=0, total_conversions=0,
            total_cost=0.0, ctr="0.00%", cpc="R$ 0.00", cpl="R$ 0.00",
            conversion_rate="0.00%", estimated_revenue=0.0, roi="0.00%",
        )

    total_impressions = sum(m.impressions for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    total_leads = sum(m.leads for m in metrics)
    total_conversions = sum(m.conversions for m in metrics)
    total_cost = sum(float(m.cost) for m in metrics if m.cost)

    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    cpl = (total_cost / total_leads) if total_leads > 0 else 0
    conversion_rate = (total_leads / total_clicks * 100) if total_clicks > 0 else 0

    product_price = float(project.product_price) if project.product_price else 0.0
    estimated_revenue = total_conversions * product_price
    roi = ((estimated_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0

    return schemas.MarketingKPIs(
        total_impressions=total_impressions, total_clicks=total_clicks,
        total_leads=total_leads, total_conversions=total_conversions,
        total_cost=total_cost, ctr=f"{ctr:.2f}%", cpc=f"{cpc:.2f}",
        cpl=f"{cpl:.2f}", conversion_rate=f"{conversion_rate:.2f}%",
        estimated_revenue=estimated_revenue, roi=f"{roi:.2f}%",
    )


@router.get("/projects/{project_id}/export/pdf")
def export_project_pdf(project_id: str, db: Session = Depends(get_db)):
    """Exporta o relatório executivo financeiro do projeto em PDF."""
    try:
        pdf_bytes = generate_project_pdf(db, project_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=relatorio_projeto_{project_id[:8]}.pdf"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")
