import datetime
from sqlalchemy import Column, DateTime, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(80), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=True)
    password_hash = Column(String(512), nullable=False)
    created_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # NEW: security question / answer for password reset
    security_question = Column(String(255), nullable=True)
    security_answer_hash = Column(String(512), nullable=True)

    # relationships
    owned_cards = db.relationship(
        "OwnedCard",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    wanted_cards = db.relationship(
        "WantedCard",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    price_snapshots = db.relationship(
        "PriceSnapshot",
        back_populates="source_user",
        cascade="all, delete-orphan",
    )

    # helper functions
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # NEW: helpers for the security answer
    def set_security_answer(self, answer: str | None) -> None:
        """
        Store a normalized, hashed version of the security answer.
        Normalization = strip whitespace + lowercasing.
        """
        if answer:
            normalized = answer.strip().lower()
            self.security_answer_hash = generate_password_hash(normalized)
        else:
            self.security_answer_hash = None

    def check_security_answer(self, candidate: str) -> bool:
        """
        Check a candidate security answer against the stored hash.
        Uses the same normalization as set_security_answer.
        """
        if not self.security_answer_hash or not candidate:
            return False
        normalized = candidate.strip().lower()
        return check_password_hash(self.security_answer_hash, normalized)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
