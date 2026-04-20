from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer

from database import get_db, engine
from models import Base, User, Asset, Expense, NetWorthSnapshot

from auth import get_current_user, create_session, hash_password, verify_password

from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI()


templates = Jinja2Templates(directory="templates")

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    def dashboard(request: Request, db: Session = Depends(get_db)):
        if db.query(User).filter(User.email == email).first():
            return HTMLResponse("Email already registered", status_code=400)
    
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    response = RedirectResponse(url="/dashboard", status_code=302)
    create_session(response, user.id)
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return HTMLResponse("Invalid credentials", status_code=400)

    response = RedirectResponse(url="/dashboard", status_code=302)
    create_session(response, user.id)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("session")
    return response

@app.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if not user:
        return templates.TemplateResponse("splash.html", {"request": request})

    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")

    total_assets = sum(a.value for a in db.query(Asset).filter(Asset.user_id == user.id).all())
    total_expenses = sum(e.amount for e in db.query(Expense).filter(Expense.user_id == user.id).all())
    net_worth = total_assets - total_expenses
    print(total_assets, total_expenses, net_worth)
    return templates.TemplateResponse("home.html", {
        "request": request,
        "total_assets": total_assets,
        "total_expenses": total_expenses,
        "net_worth": net_worth,
        "user": user
    })

@app.get("/assets")
def assets(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")
    
    assets = db.query(Asset).filter(Asset.user_id == user.id).all()
    return templates.TemplateResponse("assets.html", {"request": request, "assets": assets})

@app.post("/assets")

def add_asset(
    
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    value: float = Form(...),
    db: Session = Depends(get_db)
):
    
    def calculate_net_worth(db, user_id):
        assets = db.query(Asset).filter(Asset.user_id == user_id).all()
        expenses = db.query(Expense).filter(Expense.user_id == user_id).all()

        total_assets = sum(a.value for a in assets)
        total_expenses = sum(e.amount for e in expenses)

        return total_assets - total_expenses

    user = get_current_user(request, db)
    asset = Asset(name=name, type=type, value=value, user_id=user.id)
    db.add(asset)
    db.commit()

    snapshot = NetWorthSnapshot(
    user_id=user.id,
    net_worth=calculate_net_worth(db, user.id),
    timestamp=datetime.now()
    )

    db.add(snapshot)
    db.commit()
    return RedirectResponse("/assets", status_code=302)

@app.get("/expenses")
def expenses(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")
    
    expenses_list = db.query(Expense).filter(Expense.user_id == user.id).all()

    return templates.TemplateResponse(
        "expenses.html",
        {"request": request, "expenses": expenses_list}
    )

@app.post("/expenses")
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
    
    def calculate_net_worth(db, user_id):
        assets = db.query(Asset).filter(Asset.user_id == user_id).all()
        expenses = db.query(Expense).filter(Expense.user_id == user_id).all()

        total_assets = sum(a.value for a in assets)
        total_expenses = sum(e.amount for e in expenses)

        return total_assets - total_expenses
    
    expense = Expense(
        description=description,  # match your model field
        category=category,
        amount=amount,
        user_id=user.id
    )
    db.add(expense)
    db.commit()

    snapshot = NetWorthSnapshot(
    user_id=user.id,
    net_worth=calculate_net_worth(db, user.id),
    timestamp=datetime.now()
    )

    db.add(snapshot)
    db.commit()

    return RedirectResponse("/expenses", status_code=302)

@app.get("/net-worth-history")
def net_worth_history(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")

    snapshots = db.query(NetWorthSnapshot)\
        .filter(NetWorthSnapshot.user_id == user.id)\
        .order_by(NetWorthSnapshot.timestamp)\
        .all()

    dates = [s.timestamp.strftime("%Y-%m-%d %H:%M") for s in snapshots]
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

