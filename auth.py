from fastapi import FastAPI, Request, Form, Depends 
from sqlalchemy.orm import Session
from database import get_db 
from models import User
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer 


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