import os

from fastapi import FastAPI, Request, Form, Depends

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, User, Asset, Expense, NetWorthSnapshot
from services import finance as f
from routes import assets, expenses, auth, dashboard, net_worth
from routes.auth import get_current_user

from datetime import date

from dotenv import load_dotenv

Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI()
app.include_router(assets.router)
app.include_router(expenses.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(net_worth.router)

templates = Jinja2Templates(directory="templates")
def format_currency(value):
    if value is None:
        return "$0.00"
    return "${:,.2f}".format(value)

templates.env.filters["currency"] = format_currency

@app.get("/")
def splash(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if user:
        return RedirectResponse("/dashboard")

    return templates.TemplateResponse("splash.html", {"request": request})


@app.post("/assets/delete/{asset_id}")
def delete_asset(request: Request, asset_id: int, db: Session = Depends(get_db)):
    
    user = get_current_user(request, db)

    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == user.id
    ).first()
    if asset:
        db.delete(asset)
        db.commit()
    return RedirectResponse(url="/assets", status_code=302)

@app.post("/expenses/delete/{expense_id}")
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

