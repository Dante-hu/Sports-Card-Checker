from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from ..extensions import db


class Card(db.Model):
    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint(
            "sport", "year", "brand", "set_name", "card_number", name="uq_card_catalog"
        ),  # ensure no duplicate cards in catalog
    )

    id = Column(Integer, primary_key=True)
    sport = Column(String(50), nullable=False, index=True)
    year = Column(String(20), nullable=False, index=True)
    brand = Column(String(50), nullable=False)
    set_name = Column(String(120), nullable=False)
    card_number = Column(String(20), nullable=False)
    player_name = Column(String(120), nullable=False, index=True)
    team = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)

    # relationships
    owned_instances = db.relationship(
        "OwnedCard",
        back_populates="card",
        cascade="all, delete-orphan",
    )
    wanted_entries = db.relationship(
        "WantedCard",
        back_populates="card",
        cascade="all, delete-orphan",
    )
    price_history = db.relationship(
        "PriceSnapshot",
        back_populates="card",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Card {self.year} {self.brand} #{self.card_number} {self.player_name}>"
