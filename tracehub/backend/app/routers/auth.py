"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt

from ..config import get_settings

router = APIRouter()
settings = get_settings()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Simple in-memory user for POC (replace with database in production)
# Password: tracehub2026
POC_USER = {
    "username": "demo",
    "email": "demo@vibotaj.com",
    "password": "tracehub2026",  # Simple plaintext for POC
    "full_name": "Demo User"
}


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str


class User(BaseModel):
    """User information."""
    username: str
    email: str
    full_name: str


def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify password - simple comparison for POC."""
    return plain_password == stored_password


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # For POC, just check if username matches
    if username != POC_USER["username"]:
        raise credentials_exception

    return User(
        username=POC_USER["username"],
        email=POC_USER["email"],
        full_name=POC_USER["full_name"]
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token."""
    # For POC, simple check against hardcoded user
    if form_data.username != POC_USER["username"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, POC_USER["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": form_data.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user
