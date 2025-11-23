from sqlalchemy import Column, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..extensions import db
import datetime


class WantedCard(db.Model):
    __tablename__ = "wanted_cards"

    id = Column(Integer, primary_key=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)

    # Optional notes
    notes = Column(Text, nullable=True)

    # Timestamp
    date_added = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="wanted_cards")
    card = relationship("Card", back_populates="wanted_entries")

    def __repr__(self):
        user_email = getattr(self.user, "email", "unknown user")
        return f"<WantedCard card_id={self.card_id} user={user_email}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "card_id": self.card_id,
            "player_name": self.card.player_name if self.card else None,
            "notes": self.notes,
            "date_added": self.date_added.isoformat() if self.date_added else None,
        }
