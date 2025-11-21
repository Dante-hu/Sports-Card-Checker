from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Numeric,
    Boolean,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from ..extensions import db


class OwnedCard(db.Model):
    __tablename__ = "owned_cards"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)

    quantity = Column(Integer, default=1, nullable=False)
    condition = Column(String(30), nullable=False)  # "Mint"
    grade = Column(Numeric(3, 1), nullable=True)  # PSA 9.5
    acquired_price = Column(Numeric(10, 2), nullable=True)
    acquired_date = Column(Date, nullable=True)
    is_for_trade = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=db.func.now(), nullable=False)

    # relationships
    owner = relationship("User", back_populates="owned_cards")
    card = relationship("Card", back_populates="owned_instances")

    def __repr__(self):
        return f"<OwnedCard {self.card} x{self.quantity} by {self.owner.email}>"
