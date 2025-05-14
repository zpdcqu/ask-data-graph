from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.api.v1.schemas import user_schemas, token_schemas
from app.crud import crud_user
from app.core import security
from app.db.session import get_db
from app.core.config import settings
from app.core.deps import get_current_active_user
from app.db.models import user_models # For type hinting

router = APIRouter()

@router.post("/login", response_model=token_schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: user_schemas.UserCreate,
    db: Session = Depends(get_db)
):
    db_user_by_username = crud_user.get_user_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    db_user_by_email = crud_user.get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    created_user = crud_user.create_user(db=db, user=user_in)
    return created_user

@router.get("/users/me", response_model=user_schemas.User)
async def read_users_me(
    current_user: user_models.User = Depends(get_current_active_user)
):
    """Fetch the current logged in user."""
    return current_user 