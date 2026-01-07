"""Authentication router with database-backed user management."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from typing import Optional

from ..config import get_settings
from ..database import get_db
from ..models.user import User as UserModel, UserRole
from ..schemas.user import UserResponse, CurrentUser
from ..services.permissions import get_role_permissions

router = APIRouter()
settings = get_settings()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# Legacy User class for backward compatibility
class User(BaseModel):
    """User information (legacy format for backward compatibility)."""
    username: str
    email: str
    full_name: str
    role: Optional[str] = "viewer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """Get user by email address."""
    return db.query(UserModel).filter(UserModel.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[UserModel]:
    """Get user by ID."""
    return db.query(UserModel).filter(UserModel.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[UserModel]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token.

    Returns the legacy User format for backward compatibility.
    Use get_current_active_user for the full user model.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "viewer")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Try to get user from database
    user = None
    try:
        user = get_user_by_id(db, user_id)
    except Exception:
        # user_id might not be a valid UUID (legacy tokens like "demo")
        # Rollback the failed transaction to clean up session state
        db.rollback()

    if user is None:
        # Fall back to demo user for backward compatibility
        if email == settings.demo_email or user_id == settings.demo_username or user_id == "demo":
            return User(
                username=settings.demo_username,
                email=settings.demo_email,
                full_name=settings.demo_full_name,
                role="admin"  # Demo user gets admin role
            )
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(
        username=user.email,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value
    )


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """Get current authenticated user with full details and permissions.

    This is the preferred method for new endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role_str: str = payload.get("role", "viewer")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Try to get user from database
    user = None
    try:
        user = get_user_by_id(db, user_id)
    except Exception:
        # user_id might not be a valid UUID (legacy tokens like "demo")
        # Rollback the failed transaction to clean up session state
        db.rollback()

    if user is None:
        # Fall back to demo user for backward compatibility
        if email == settings.demo_email or user_id == settings.demo_username or user_id == "demo":
            from uuid import UUID
            role = UserRole.ADMIN  # Demo user gets admin role
            permissions = [p.value for p in get_role_permissions(role)]
            # Demo user belongs to VIBOTAJ organization
            vibotaj_org_id = UUID("00000000-0000-0000-0000-000000000001")
            return CurrentUser(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                email=settings.demo_email,
                full_name=settings.demo_full_name,
                role=role,
                is_active=True,
                organization_id=vibotaj_org_id,
                permissions=permissions
            )
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get permissions for user's role
    permissions = [p.value for p in get_role_permissions(user.role)]

    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint - returns JWT token.

    Accepts either email or username for backward compatibility.
    """
    # First try to authenticate against database
    user = authenticate_user(db, form_data.username, form_data.password)

    if user:
        # Update last login time
        user.last_login = datetime.utcnow()
        db.commit()

        # Create token with user info
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            }
        )
        return Token(access_token=access_token, token_type="bearer")

    # Fall back to demo user for backward compatibility
    if form_data.username == settings.demo_username or form_data.username == settings.demo_email:
        if form_data.password == settings.demo_password:
            access_token = create_access_token(
                data={
                    "sub": settings.demo_username,
                    "email": settings.demo_email,
                    "role": "admin"
                }
            )
            return Token(access_token=access_token, token_type="bearer")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information (legacy format)."""
    return current_user


@router.get("/me/full", response_model=CurrentUser)
async def get_me_full(current_user: CurrentUser = Depends(get_current_active_user)):
    """Get current user information with permissions."""
    return current_user


@router.get("/permissions")
async def get_my_permissions(current_user: CurrentUser = Depends(get_current_active_user)):
    """Get current user's permissions."""
    return {
        "user_id": str(current_user.id),
        "role": current_user.role.value,
        "permissions": current_user.permissions
    }


@router.get("/debug/ping")
async def debug_ping():
    """Simple debug endpoint to test if new routes are being loaded."""
    return {"pong": True, "message": "Auth router is loaded"}


@router.get("/debug/user-count")
async def debug_user_count(db: Session = Depends(get_db)):
    """Debug endpoint to count users in database."""
    from ..config import get_settings
    settings = get_settings()
    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")

    from ..models.user import User as UserModel
    try:
        count = db.query(UserModel).count()
        return {"user_count": count, "environment": settings.environment}
    except Exception as e:
        return {"error": str(e), "environment": settings.environment}


@router.get("/debug/user-check/{email}")
async def debug_user_check(email: str, db: Session = Depends(get_db)):
    """Debug endpoint to check if a user exists (non-production only)."""
    from ..config import get_settings
    settings = get_settings()
    # Only allow on non-production environments
    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")

    try:
        user = get_user_by_email(db, email)
        if user:
            return {
                "found": True,
                "email": user.email,
                "hash_prefix": user.hashed_password[:20] if user.hashed_password else None,
                "hash_length": len(user.hashed_password) if user.hashed_password else 0,
                "is_active": user.is_active,
                "role": user.role.value if user.role else None,
                "org_id": str(user.organization_id) if user.organization_id else None,
                "environment": settings.environment
            }
        return {"found": False, "email": email, "environment": settings.environment}
    except Exception as e:
        return {"error": str(e), "environment": settings.environment}
