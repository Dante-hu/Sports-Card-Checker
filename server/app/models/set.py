from sqlalchemy import Column, Integer, String, UniqueConstraint
from ..extensions import db


class Set(db.Model):
    __tablename__ = "sets"
    __table_args__ = (
        UniqueConstraint("sport", "year", "brand", "set_name", name="uq_set_catalog"),
    )

    id = Column(Integer, primary_key=True)
    sport = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    brand = Column(String(50), nullable=False)
    set_name = Column(String(120), nullable=False)

    def __repr__(self):
        return f"<Set {self.year} {self.brand} {self.set_name}>"
