from datetime import datetime
import datetime
from sqlalchemy import Column, DateTime, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions  import db


class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(80), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    #relationships
    owned_cards = db.relationship("OwnedCard", back_populates="owner", cascade="all, delete-orphan")
    wanted_cards = db.relationship("WantedCard", back_populates="user", cascade="all, delete-orphan")
    price_snapshots = db.relationship("PriceSnapshot", back_populates="source_user", cascade="all, delete-orphan")

    #helper functions
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"