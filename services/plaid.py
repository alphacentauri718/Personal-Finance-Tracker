import os
from plaid.api import plaid_api
from plaid import Configuration, ApiClient

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from datetime import datetime, timedelta

from routes.auth import get_current_user
from models import Expense, Asset

from database import get_db

from pydantic import BaseModel

class TokenRequest(BaseModel):
    public_token: str

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
    }
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

router = APIRouter()

def fetch_transactions(access_token):
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=(datetime.now() - timedelta(days=30)).date(),
        end_date=datetime.now().date()
    )

    response = client.transactions_get(request)
    return response["transactions"]

def sync_transactions(db, user):

    if not user.plaid_access_token:
        return

    transactions = fetch_transactions(user.plaid_access_token)

    for t in transactions:

        #Deduplication check
        if t["amount"] > 0:
            existing = db.query(Expense).filter(
                Expense.plaid_transaction_id == t["transaction_id"]
            ).first()

            if existing:
                continue  # skip duplicates

            expense = Expense(
                description=t["name"],
                category=t["category"][0] if t["category"] else "Other",
                amount=t["amount"],
                user_id=user.id,
                plaid_transaction_id=t["transaction_id"]
            )

            db.add(expense)
        else:
            existing = db.query(Asset).filter(
                Asset.plaid_transaction_id == t["transaction_id"]
            ).first()

            if existing:
                continue  # skip duplicates

            asset = Asset(
                name=t["name"],
                type=t["category"][0] if t["category"] else "Other",
                value=abs(t["amount"]),
                user_id=user.id,
                plaid_transaction_id=t["transaction_id"]
            )

            db.add(asset)


    db.commit()

@router.post("/plaid/link-token")
def create_link_token(user=Depends(get_current_user)):

    request = LinkTokenCreateRequest(
        user={"client_user_id": str(user.id)},
        client_name="Personal Finance Tracker",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en"
    )

    response = client.link_token_create(request)

    return response.to_dict()


@router.post("/plaid/exchange-token")
def exchange_token(data: TokenRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):

    request = ItemPublicTokenExchangeRequest(public_token=data.public_token)

    response = client.item_public_token_exchange(request)

    access_token = response["access_token"]

    user.plaid_access_token = access_token
    db.commit()

    return {"status": "ok"}

@router.post("/plaid/sync")
def sync_plaid(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    sync_transactions(db, user)
    user.has_synced = True
    db.commit()
    return RedirectResponse("/dashboard", status_code=302)