from sqlalchemy import Column, DateTime, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from ..extensions import db
import datetime


class PriceSnapshot(db.Model):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)
    source_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # who requested the check

    source = Column(String(30), nullable=False, default="ebay")  # ebay, tcgplayer, etc.
    median_price = Column(Numeric(10, 2), nullable=False)
    high_price = Column(Numeric(10, 2), nullable=True)
    low_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    recorded_at = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    # ----- relationships -----
    card = relationship("Card", back_populates="price_history")
    source_user = relationship("User", back_populates="price_snapshots")

    def __repr__(self):
        return f"<PriceSnapshot {self.card}  ${self.median_price} {self.currency} @ {self.recorded_at}>"
