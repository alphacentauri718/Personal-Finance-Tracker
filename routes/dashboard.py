from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from sqlalchemy.orm import Session

from routes.auth import get_current_user
from models import Asset, Expense, SavedView, Account

templates = Jinja2Templates(directory="templates")
router = APIRouter()   

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")

    query_expenses = db.query(Expense).filter(Expense.user_id == user.id)
    query_assets = db.query(Asset).filter(Asset.user_id == user.id)


    expenses = query_expenses.all()
    assets = query_assets.all()

    total_assets = sum(a.value for a in assets)
    total_expenses = sum(e.amount for e in expenses)

    net_worth = total_assets - total_expenses

    return templates.TemplateResponse("home.html", {
        "request": request,
        "total_assets": total_assets,
        "total_expenses": total_expenses,
        "net_worth": net_worth,
        "user": user
    })

@router.post("/views/save")
def save_view(
    data: dict,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    view = SavedView(
        user_id=user.id,
        name=data["name"],
        account_ids=data["account_ids"]
    )

    db.add(view)
    db.commit()

    return {"status": "ok"}

@router.post("/views/delete/{view_id}")
def delete_view(
    view_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    view = db.query(SavedView).filter(SavedView.id == view_id, SavedView.user_id == user.id).first()

    if view:
        db.delete(view)
        db.commit()

    return {"success": "true"}

@router.post("/dashboard-data")
def dashboard_data(
    data: dict,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    ids = data.get("account_ids", [])

    # get accounts
    accounts = db.query(Account).filter(
    Account.id.in_(ids),
    Account.user_id == user.id
    ).all()
    
    #get plaid_account_ids
    plaid_account_ids = [
    acct.plaid_account_id
    for acct in accounts
    ]

    #query asset and expenses tables
    expenses = db.query(Expense).filter(
    Expense.user_id == user.id,
    Expense.plaid_account_id.in_(plaid_account_ids)
    ).all()
    
    assets = db.query(Asset).filter(
    Asset.user_id == user.id,
    Asset.plaid_account_id.in_(plaid_account_ids)
    ).all()

    total_expenses = sum(e.amount for e in expenses)
    total_assets = sum(a.value for a in assets)
    net_worth = total_assets - total_expenses
    
    return{
        "total_expenses": total_expenses,
        "expenses": [
            {
                "description": e.description,
                "category": e.category,
                "amount": float(e.amount)
            } for e in expenses
        ],
        "total_assets": total_assets,
        "assets": [
            {
                "description": a.name,
                "category": a.type,
                "amount": float(a.value)
            } for a in assets
        ],
        "net_worth": net_worth
    }