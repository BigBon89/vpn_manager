from datetime import datetime, timedelta, timezone
from typing import Type

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from database.models import Base, Key, Log, CryptopayPayment


class Database:
    def __init__(self, db_path="sqlite:///database.db") -> None:
        self.engine = create_engine(db_path, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_key(self, owner: int, end: datetime, url: str) -> None:
        session: Session = self.Session()
        key = Key(owner=owner, end=end, url=url)
        session.add(key)
        session.commit()
        session.close()

    def get_key_from_tg_id(self, tg_id: int) -> Type[Key]:
        session: Session = self.Session()
        key = session.query(Key).filter(Key.owner == tg_id).first()
        session.close()
        return key

    def update_key_end(self, tg_id: int, end: datetime) -> None:
        session: Session = self.Session()
        key = session.query(Key).filter(Key.owner == tg_id).first()
        if key is None:
            session.close()
            return
        key.end = end
        session.commit()
        session.close()

    def update_key_url(self, tg_id: int, new_url: str) -> None:
        session: Session = self.Session()
        key = session.query(Key).filter(Key.owner == tg_id).first()
        if key is None:
            session.close()
            return
        key.url = new_url
        session.commit()
        session.close()

    def add_log(self, text: str) -> None:
        session: Session = self.Session()
        log = Log(text=text)
        session.add(log)
        session.commit()
        session.close()

    def get_all_keys(self) -> list:
        session: Session = self.Session()
        keys = session.query(Key).all()
        session.close()
        return keys

    def delete_depleted_keys(self) -> None:
        session: Session = self.Session()
        now = datetime.now(timezone.utc) + timedelta(hours=3)
        session.query(Key).filter(Key.end < now).delete()
        session.commit()
        session.close()

    def add_cryptopay(self, tg_id: int, invoice_id: int) -> None:
        session: Session = self.Session()
        cryptopay_payment = CryptopayPayment(tg_id=tg_id, invoice_id=invoice_id)
        session.add(cryptopay_payment)
        session.commit()
        session.close()

    def delete_cryptopay_by_invoice(self, invoice_id: int) -> None:
        session: Session = self.Session()
        session.query(CryptopayPayment).filter(CryptopayPayment.invoice_id == invoice_id).delete()
        session.commit()
        session.close()

    def get_all_cryptopay_invoice_ids(self) -> list[int]:
        session: Session = self.Session()
        invoice_ids = session.query(CryptopayPayment.invoice_id).all()
        session.close()
        return [invoice_id for (invoice_id,) in invoice_ids]

    # def get_tg_id_from_invoice_cryptopay(self, invoice_id: int) -> Type[Key]:
    #     session: Session = self.Session()
    #     result = session.query(CryptopayPayment).filter(CryptopayPayment.invoice_id == invoice_id).first()
    #     session.close()
    #     return result