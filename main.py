from fastapi import FastAPI


from database import engine
from models import Base
from routes import assets, expenses, auth, dashboard, net_worth, splash

from dotenv import load_dotenv

Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI()
app.include_router(assets.router)
app.include_router(expenses.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(net_worth.router)
app.include_router(splash.router)




