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
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest

from routes.auth import get_current_user
from models import Expense, Asset, Account, PlaidItem

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
    
    for item in user.plaid_items:
        for account in user.accounts:
            
            transactions = fetch_transactions(item.access_token)

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
                        plaid_transaction_id=t["transaction_id"],
                        plaid_account_id = account.plaid_account_id
                    )

                    db.add(expense)
                    db.commit()
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
                        plaid_transaction_id=t["transaction_id"],
                        plaid_account_id = account.plaid_account_id
                    )

                    db.add(asset)
                    db.commit()

    
    user.last_synced = datetime.now()

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
    item_id = response["item_id"]

    item_request = ItemGetRequest(access_token=access_token)
    item_response = client.item_get(item_request)
    institution_id = item_response["item"]["institution_id"]
    institution_request = InstitutionsGetByIdRequest(institution_id=institution_id,country_codes=[CountryCode("US")])
    institution_response = client.institutions_get_by_id(institution_request)
    institution_name = institution_response["institution"]["name"]

    accounts_response = client.accounts_get(
        AccountsGetRequest(access_token=access_token)
    )
    
    for acct in accounts_response["accounts"]:
        
        account = Account(
            user_id=user.id,
            plaid_access_token=access_token,
            item_id=item_id,
            plaid_account_id=acct["account_id"],
            name=acct["name"],
            account_type=acct.type.value,
            subtype=acct.subtype.value if acct.subtype else None,
            persistent_account_id = acct.get("persistent_account_id", None),
            mask = acct["mask"]
        )

        existing = db.query(Account).filter(
            Account.name == account.name, 
            Account.persistent_account_id == account.persistent_account_id,
            Account.subtype == account.subtype,
            Account.mask == account.mask,
            Account.user_id == user.id).first()

        if existing:
            print("acct skipped")
            continue # skip duplicate accounts
            
        db.add(account)
    
    plaid_item = PlaidItem(
        user_id = user.id,
        plaid_item_id = item_id,
        access_token = access_token,
        institution_name = institution_name
    )
    db.add(plaid_item)
    db.commit()

    return RedirectResponse("/dashboard", status_code=302)

@router.post("/plaid/sync")
def sync_plaid(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    sync_transactions(db, user)
    user.has_synced = True
    db.commit()
    return RedirectResponse("/dashboard", status_code=302)

@router.post("/toggle-daily-sync")
def toggle_daily_sync(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    user.sync_daily = not user.sync_daily
    db.commit()

    return RedirectResponse("/dashboard", status_code=302)