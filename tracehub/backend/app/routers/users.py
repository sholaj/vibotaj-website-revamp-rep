"""Users router - user management CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import math

from ..database import get_db
from ..models.user import User as UserModel, UserRole
from ..schemas.user import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserListResponse,
    CurrentUser
)
from ..routers.auth import get_current_active_user, get_password_hash, verify_password
from ..services.permissions import (
    Permission,
    has_permission,
    can_manage_role,
    get_permission_matrix
)

router = APIRouter()


def check_permission(user: CurrentUser, permission: Permission) -> None:
    """Check if user has the required permission, raise 403 if not."""
    if not has_permission(user.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: {permission.value}"
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Create a new user. Admin only."""
    # Check permission
    check_permission(current_user, Permission.USERS_CREATE)

    # Check if current user can create a user with the specified role
    if not can_manage_role(current_user.role, user_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You cannot create users with role '{user_data.role.value}'"
        )

    # Check if email already exists
    existing = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    # Create user - inherit organization from current user
    user = UserModel(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
        created_at=datetime.utcnow(),
        organization_id=current_user.organization_id  # Multi-tenancy: inherit org from creator
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """List all users with filtering and pagination. Admin only."""
    # Check permission
    check_permission(current_user, Permission.USERS_LIST)

    # Build query - filter by organization (multi-tenancy)
    query = db.query(UserModel).filter(
        UserModel.organization_id == current_user.organization_id
    )

    # Apply filters
    if role:
        query = query.filter(UserModel.role == role)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (UserModel.email.ilike(search_term)) |
            (UserModel.full_name.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Calculate pagination
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total > 0 else 1

    # Get users
    users = (
        query
        .order_by(UserModel.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return UserListResponse(
        items=users,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get current user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=datetime.utcnow(),  # Would need to fetch from DB for real value
        updated_at=None,
        last_login=None
    )


@router.get("/roles")
async def get_available_roles(
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get list of available user roles."""
    check_permission(current_user, Permission.USERS_READ)

    roles = [
        {
            "value": role.value,
            "name": role.value.replace("_", " ").title(),
            "description": _get_role_description(role),
            "can_assign": can_manage_role(current_user.role, role)
        }
        for role in UserRole
    ]

    return {"roles": roles}


@router.get("/permissions-matrix")
async def get_permissions_matrix(
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get the complete permission matrix. Admin only."""
    check_permission(current_user, Permission.SYSTEM_ADMIN)
    return get_permission_matrix()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get a specific user by ID."""
    # Users can view their own profile, admins can view all
    if user_id != current_user.id:
        check_permission(current_user, Permission.USERS_READ)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Update a user. Users can update their own profile, admins can update all."""
    # Check if updating own profile or has admin permission
    is_own_profile = user_id == current_user.id
    if not is_own_profile:
        check_permission(current_user, Permission.USERS_UPDATE)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Users can only update their own name and email (not role or is_active)
    if is_own_profile and not has_permission(current_user.role, Permission.USERS_UPDATE):
        if user_update.role is not None or user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your name and email"
            )

    # Check if trying to change role and if allowed
    if user_update.role is not None:
        if not can_manage_role(current_user.role, user_update.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot assign role '{user_update.role.value}'"
            )
        # Cannot change own role
        if is_own_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot change your own role"
            )

    # Check if email already exists (if changing email)
    if user_update.email and user_update.email != user.email:
        existing = db.query(UserModel).filter(UserModel.email == user_update.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )

    # Apply updates
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/password")
async def update_user_password(
    user_id: UUID,
    password_update: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Update user password. Users can update their own password."""
    # Users can only update their own password
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(password_update.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    user.hashed_password = get_password_hash(password_update.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: UUID,
    new_password: str = Query(..., min_length=8, description="New password"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Reset user password (admin only)."""
    check_permission(current_user, Permission.USERS_UPDATE)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Cannot reset own password this way
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the password update endpoint to change your own password"
        )

    # Check if current user can manage this user's role
    if not can_manage_role(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot reset password for this user"
        )

    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password reset successfully"}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Deactivate a user (soft delete). Admin only."""
    check_permission(current_user, Permission.USERS_DELETE)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Cannot deactivate yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    # Check if current user can manage this user's role
    if not can_manage_role(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot deactivate this user"
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Reactivate a deactivated user. Admin only."""
    check_permission(current_user, Permission.USERS_UPDATE)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )

    # Check if current user can manage this user's role
    if not can_manage_role(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot activate this user"
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "User activated successfully"}


def _get_role_description(role: UserRole) -> str:
    """Get description for a role."""
    descriptions = {
        UserRole.ADMIN: "Full access to all features including user management",
        UserRole.COMPLIANCE: "Can validate and approve documents, view all shipments",
        UserRole.LOGISTICS_AGENT: "Schedule containers, upload all documents, manage shipments",
        UserRole.BUYER: "Read-only access to their assigned shipments and documents",
        UserRole.SUPPLIER: "Upload origin certificates, provide geolocation data",
        UserRole.VIEWER: "Read-only access to all shipment and document data"
    }
    return descriptions.get(role, "")
