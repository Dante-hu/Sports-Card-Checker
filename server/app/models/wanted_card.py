from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..extensions import db
import datetime


class WantedCard(db.Model):
    __tablename__ = "wanted_cards"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)

    priority = Column(Integer, nullable=True)  # 1 = highest
    max_price_willing_to_pay = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    date_added = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    #relationships 
    user = relationship("User", back_populates="wanted_cards")
    card = relationship("Card", back_populates="wanted_entries")

    def __repr__(self):
        return f"<WantedCard {self.card} by {self.user.email}>"