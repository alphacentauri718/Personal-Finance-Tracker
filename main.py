import os

from fastapi import FastAPI, Request, Form, Depends

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, User, Asset, Expense, NetWorthSnapshot
from services import finance as f
from routes import assets, expenses, auth
from routes.auth import get_current_user

from datetime import date

from dotenv import load_dotenv

Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI()
app.include_router(assets.router)
app.include_router(expenses.router)
app.include_router(auth.router)

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


@app.get("/dashboard", response_class=HTMLResponse)
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

def take_snapshot(db, user_id):
    today = date.today()

    # Prevent duplicates for same day
    existing = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.user_id == user_id,
        NetWorthSnapshot.timestamp == today
    ).first()

    if existing:
        return

    net_worth = f.calculate_net_worth(user_id)

    snapshot = NetWorthSnapshot(
        user_id=user_id,
        timestamp=today,
        net_worth=net_worth
    )

    db.add(snapshot)
    db.commit()

@app.post("/snapshot")
def snapshot_all_users(request: Request, db: Session = Depends(get_db)):

    secret = request.headers.get("X-CRON-KEY")
    CRON_SECRET = os.getenv("CRON_SECRET")

    if secret != CRON_SECRET:
        return {"error": "unauthorized"}

    users = db.query(User).all()
    for user in users:
        take_snapshot(db, user.id)
    return {"status": "ok"}

@app.get("/net-worth-history")
def net_worth_history(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")

    snapshots = db.query(NetWorthSnapshot).filter(NetWorthSnapshot.user_id == user.id).order_by(NetWorthSnapshot.timestamp).all()

    dates = [s.timestamp.strftime("%Y-%m-%d") for s in snapshots]
    values = [s.net_worth for s in snapshots]

    return templates.TemplateResponse("history.html", {
        "request": request,
        "dates": dates,
        "values": values
    })

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

