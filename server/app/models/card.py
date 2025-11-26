# app/models/card.py
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from ..extensions import db


class Card(db.Model):
    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint(
            "sport",
            "year",
            "brand",
            "set_name",
            "card_number",
            name="uq_card_catalog",
        ),
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

    def __repr__(self) -> str:
        return (
            f"<Card {self.year} {self.brand} "
            f"#{self.card_number} {self.player_name}>"
        )

    # 🔹 Minimal dict used inside Owned/Wanted/etc.
    def to_dict_basic(self) -> dict:
        return {
            "id": self.id,
            "sport": self.sport,
            "year": self.year,
            "brand": self.brand,
            "set_name": self.set_name,
            "card_number": self.card_number,
            "player_name": self.player_name,
            "team": self.team,
            "image_url": self.image_url,  # 👈 IMPORTANT
        }

    # 🔹 Full dict if you ever need more later
    def to_dict(self) -> dict:
        return self.to_dict_basic()
