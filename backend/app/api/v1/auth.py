from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, Token, UserCreate, UserOut
from app.services import auth_service
from app.services.auth_service import EmailTakenError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User) -> dict:
    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
        "user": _user_out(user),
    }


def _user_out(user: User) -> dict:
    return {"id": str(user.id), "email": user.email, "preferences": user.preferences}


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db: Session = Depends(get_db)) -> dict:
    try:
        user = auth_service.signup(db, body.email, body.password)
    except EmailTakenError:
        raise HTTPException(status_code=409, detail="Email already registered") from None
    return _token_response(user)


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    try:
        user = auth_service.authenticate(db, body.email, body.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password") from None
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> dict:
    return _user_out(user)
