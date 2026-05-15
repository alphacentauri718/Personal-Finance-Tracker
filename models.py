from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
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
    create_date_time = Column(Date, default = date.today())

    accounts = relationship("Account", back_populates="user")

    saved_views = relationship("SavedView",back_populates="user",cascade="all, delete-orphan")

    plaid_items = relationship("PlaidItem",back_populates="user",cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    value = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    plaid_transaction_id = Column(String, unique=True, nullable=True)
    plaid_account_id = Column(String, ForeignKey("accounts.plaid_account_id"))
    create_date_time = Column(Date, default = date.today())


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    category = Column(String)
    amount = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    plaid_transaction_id = Column(String, unique=True, nullable=True)
    plaid_account_id = Column(String, ForeignKey("accounts.plaid_account_id"))
    create_date_time = Column(Date, default = date.today())

class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    net_worth = Column(Float)
    create_date_time = Column(Date, default = date.today())

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plaid_access_token = Column(String, ForeignKey("plaid_items.access_token"), nullable=False)
    item_id = Column(String)  # Plaid item identifier
    name = Column(String)     # e.g. "Chase Checking"
    plaid_account_id = Column(String, unique=True)
    account_type = Column(String)
    subtype = Column(String)
    persistent_account_id = Column(String)
    create_date_time = Column(Date, default = date.today())

    user = relationship("User", back_populates="accounts")
    plaid_items= relationship("PlaidItem", back_populates="accounts")

class SavedView(Base):

    __tablename__ = "saved_views"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    name = Column(String,nullable=False)
    account_ids = Column(JSON,nullable=False)
    create_date_time = Column(Date, default = date.today())
    
    user = relationship("User",back_populates="saved_views")

class PlaidItem(Base):

    __tablename__= "plaid_items"

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    plaid_item_id = Column(String,nullable=False)
    access_token = Column(String,nullable=False, unique=True)
    institution_name = Column(String)
    create_date_time = Column(Date, default = date.today())

    user = relationship("User",back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_items")
