from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import date
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    plaid_access_token = Column(String, nullable=True)
    has_synced = Column(Boolean, default=False)
    sync_daily = Column(Boolean, default=False)
    last_synced = Column(DateTime, nullable=True)

    accounts = relationship("Account", back_populates="user")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    value = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    plaid_transaction_id = Column(String, unique=True, nullable=True)
    plaid_account_id = Column(String, ForeignKey("accounts.plaid_account_id"))


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    category = Column(String)
    amount = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    plaid_transaction_id = Column(String, unique=True, nullable=True)
    plaid_account_id = Column(String, ForeignKey("accounts.plaid_account_id"))

class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    net_worth = Column(Float)
    timestamp = Column(Date, default = date.today())

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    plaid_access_token = Column(String, nullable=False)
    item_id = Column(String)  # Plaid item identifier
    name = Column(String)     # e.g. "Chase Checking"
    plaid_account_id = Column(String, unique=True)
    account_type = Column(String)
    subtype = Column(String)

    user = relationship("User", back_populates="accounts")