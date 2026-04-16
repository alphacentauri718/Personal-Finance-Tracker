from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    value = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    category = Column(String)
    amount = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))

class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    net_worth = Column(Float)
    timestamp = Column(DateTime)