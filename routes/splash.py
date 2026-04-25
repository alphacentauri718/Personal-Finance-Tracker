from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from database import get_db
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
def splash(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if user:
        return RedirectResponse("/dashboard")

    return templates.TemplateResponse("splash.html", {"request": request})