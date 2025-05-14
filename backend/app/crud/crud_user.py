from sqlalchemy.orm import Session
from typing import Optional

from app.db.models import user_models
from app.api.v1.schemas import user_schemas
from app.core.security import get_password_hash

def get_user(db: Session, user_id: int) -> Optional[user_models.User]:
    return db.query(user_models.User).filter(user_models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[user_models.User]:
    return db.query(user_models.User).filter(user_models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[user_models.User]:
    return db.query(user_models.User).filter(user_models.User.email == email).first()

def create_user(db: Session, user: user_schemas.UserCreate, role: str = "user") -> user_models.User:
    hashed_password = get_password_hash(user.password)
    db_user = user_models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# TODO: Add update_user, delete_user, etc. as needed 