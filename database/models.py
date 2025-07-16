from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Key(Base):
    __tablename__ = "keys"
    id = Column(Integer, primary_key=True)
    owner = Column(Integer)
    end = Column(DateTime)
    url = Column(Text)


class CryptopayPayment(Base):
    __tablename__ = "cryptopay"
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer)
    invoice_id = Column(Integer)


class PromoCode(Base):
    __tablename__ = "promocodes"
    id = Column(Integer, primary_key=True)
    promocode = Column(Text)
    number_of_uses = Column(Integer)


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    date = Column(DateTime, default=(datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0))
