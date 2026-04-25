from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from sqlalchemy.orm import Session

from routes.auth import get_current_user
from models import Asset
from models import Expense

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")

    total_assets = sum(a.value for a in db.query(Asset).filter(Asset.user_id == user.id).all())
    total_expenses = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == user.id).all())
    net_worth = total_assets - total_expenses

    return templates.TemplateResponse("home.html", {
        "request": request,
        "total_assets": total_assets,
        "total_expenses": total_expenses,
        "net_worth": net_worth,
        "user": user
    })