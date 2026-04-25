from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from sqlalchemy.orm import Session

from routes.auth import get_current_user
from models import Asset

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/assets")
def assets(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login")
    
    assets = db.query(Asset).filter(Asset.user_id == user.id).all()
    return templates.TemplateResponse("assets.html", {"request": request, "assets": assets})

@router.post("/assets")

def add_asset(
    
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    value: float = Form(...),
    db: Session = Depends(get_db)
):

    user = get_current_user(request, db)
    asset = Asset(name=name, type=type, value=value, user_id=user.id)
    db.add(asset)
    db.commit()

    return RedirectResponse("/assets", status_code=302)


@router.post("/assets/delete/{asset_id}")
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

