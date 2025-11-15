from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Simple SQLite database just for this auth test
DATABASE_URL = "sqlite:///./auth_test.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


class User(Base):
    """
    Very simple User table for login / signup testing.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


app = FastAPI()


def get_password_hash(password: str) -> str:
    """
    Fake password hashing for testing.
    Don't use this in a real project.
    """
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    return get_password_hash(password) == hashed_password


# Create the users table if it does not exist
Base.metadata.create_all(bind=engine)


@app.post("/signup")
def signup(payload: SignUpRequest):
    """
    Create a new user if the email is not already taken.
    """
    session = SessionLocal()
    try:
        existing_user = (
            session.query(User)
            .filter(User.email == payload.email)
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "email": user.email}
    finally:
        session.close()


@app.post("/login")
def login(payload: LoginRequest):
    """
    Check whether the email + password are valid.
    """
    session = SessionLocal()
    try:
        user = (
            session.query(User)
            .filter(User.email == payload.email)
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid email or password",
            )

        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=400,
                detail="Invalid email or password",
            )

        return {"message": "Login successful"}
    finally:
        session.close()
