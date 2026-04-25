from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from sqlalchemy.orm import Session

from routes.auth import get_current_user
from models import Expense

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/expenses")
def expenses(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")
    
    expenses_list = db.query(Expense).filter(Expense.user_id == user.id).all()

    return templates.TemplateResponse(
        "expenses.html",
        {"request": request, "expenses": expenses_list}
    )

@router.post("/expenses")
def add_expense(
    request: Request,
    description: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")
    
    expense = Expense(
        description=description,  # match your model field
        category=category,
        amount=amount,
        user_id=user.id
    )
    db.add(expense)
    db.commit()

    return RedirectResponse("/expenses", status_code=302)

@router.post("/expenses/delete/{expense_id}")
def delete_expense(request: Request,expense_id: int, db: Session = Depends(get_db)):
    
    user = get_current_user(request, db)

    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user.id).first()
    if expense:
        db.delete(expense)
        db.commit()
    db.close()

    return RedirectResponse(url="/expenses", status_code=302)