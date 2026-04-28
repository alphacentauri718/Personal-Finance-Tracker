import os

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from models import NetWorthSnapshot, User, Asset, Expense
from database import get_db
from routes.auth import get_current_user

from datetime import date

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def take_snapshot(user_id, db):
    today = date.today()

    # Prevent duplicates for same day
    existing = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.user_id == user_id,
        NetWorthSnapshot.timestamp == today
    ).first()

    if existing:
        return

    total_assets = sum(a.value for a in db.query(Asset).filter(Asset.user_id == user_id).all())

    total_expenses = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == user_id).all())

    net_worth = total_assets - total_expenses

    snapshot = NetWorthSnapshot(
        user_id=user_id,
        timestamp=today,
        net_worth=net_worth
    )

    db.add(snapshot)
    db.commit()

@router.post("/snapshot")
def snapshot_all_users(request: Request, db: Session = Depends(get_db)):

    secret = request.headers.get("X-CRON-KEY")
    CRON_SECRET = os.getenv("CRON_SECRET")

    if secret != CRON_SECRET:
        return {"error": "unauthorized"}

    users = db.query(User).all()
    for user in users:
        take_snapshot(user.id, db)
    return {"status": "ok"}

@router.get("/net-worth-history")
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