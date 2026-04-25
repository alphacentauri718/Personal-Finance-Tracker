from fastapi import FastAPI, Request, Form, Depends, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db 
from models import User

from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer 

templates = Jinja2Templates(directory="templates")
router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def create_session(response, user_id: int):
    token = serializer.dumps({"user_id": user_id})
    response.set_cookie(key="session", value=token, httponly=True)

def get_current_user(request: Request, db: Session):
    token = request.cookies.get("session")
    if not token:
        print("No session cookie found")
        return None
    try:
        data = serializer.loads(token)
        print("Decoded session:", data)

        user = db.query(User).filter(User.id == data["user_id"]).first()

        return user
    except Exception as e:
        print("Session error:", e)
        return None

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

SECRET_KEY = "wowsuchkey"  # Replace with a strong random value
serializer = URLSafeSerializer(SECRET_KEY, salt="session")

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
def signup(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...), 
           confirm_password: str = Form(...)):
    
    if db.query(User).filter(User.email == email).first():

        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Email already registered"
        })
        
        
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match"
        })
    
    user = User(email=email, hashed_password=hash_password(password))
    
    db.add(user)
    db.commit()
    db.refresh(user)

    response = RedirectResponse(url="/dashboard", status_code=302)
    create_session(response, user.id)
    return response
    
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return HTMLResponse("Invalid credentials", status_code=400)

    response = RedirectResponse(url="/dashboard", status_code=302)
    create_session(response, user.id)
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("session")
    return response
