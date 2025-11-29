from sqlalchemy import Column, Integer, String, UniqueConstraint
from ..extensions import db


class Set(db.Model):
    __tablename__ = "sets"
    __table_args__ = (
        UniqueConstraint("sport", "year", "brand", "set_name", name="uq_set_catalog"),
    )

    id = Column(Integer, primary_key=True)
    sport = Column(String(50), nullable=False, index=True)
    year = Column(String(20), nullable=False, index=True)
    brand = Column(String(50), nullable=False)
    set_name = Column(String(120), nullable=False)

    def __repr__(self):
        return f"<Set {self.year} {self.brand} {self.set_name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "sport": self.sport,
            "year": self.year,
            "brand": self.brand,
            "set_name": self.set_name,
        }

    @classmethod
    def get_or_create(cls, sport: str, year: int, brand: str, set_name: str):
        """
        Find an existing set with this sport/year/brand/set_name,
        or create it (without committing yet).
        """
        instance = cls.query.filter_by(
            sport=sport,
            year=year,
            brand=brand,
            set_name=set_name,
        ).first()

        if instance is None:
            instance = cls(
                sport=sport,
                year=year,
                brand=brand,
                set_name=set_name,
            )
            db.session.add(instance)

        return instance
