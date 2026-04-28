import os
from plaid.api import plaid_api
from plaid import Configuration, ApiClient

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

from routes.auth import get_current_user

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