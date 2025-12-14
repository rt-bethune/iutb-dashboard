"""Authentication API routes - CAS login/logout and JWT tokens."""

from fastapi import APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging

from app.database import get_db
from app.config import get_settings
from app.adapters.cas import get_cas_adapter
from app.models.db_models import UserDB, UserPermissionDB, DEPARTMENTS

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ==================== JWT UTILITIES ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== USER HELPERS ====================

def get_or_create_user(db: Session, cas_login: str, attributes: dict) -> UserDB:
    """Get existing user or create new one from CAS data."""
    user = db.query(UserDB).filter(UserDB.cas_login == cas_login).first()
    
    if user:
        # Update last login
        user.date_derniere_connexion = datetime.utcnow()
        # Update info from CAS if available
        if attributes.get('email'):
            user.email = attributes['email']
        if attributes.get('displayName'):
            parts = attributes['displayName'].split(' ', 1)
            user.prenom = parts[0] if parts else ''
            user.nom = parts[1] if len(parts) > 1 else ''
        db.commit()
        return user
    
    # Create new user (not active by default - must be validated by admin)
    new_user = UserDB(
        cas_login=cas_login,
        email=attributes.get('email'),
        prenom=attributes.get('displayName', '').split(' ')[0] if attributes.get('displayName') else None,
        nom=' '.join(attributes.get('displayName', '').split(' ')[1:]) if attributes.get('displayName') else None,
        is_active=False,  # Must be validated by admin
        is_superadmin=False,
        date_derniere_connexion=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"Created new user: {cas_login} (pending validation)")
    return new_user


def get_user_permissions(db: Session, user: UserDB) -> dict:
    """Get user's permissions structured by department."""
    perms = db.query(UserPermissionDB).filter(UserPermissionDB.user_id == user.id).all()
    
    permissions = {}
    for perm in perms:
        permissions[perm.department] = {
            'can_view_scolarite': perm.can_view_scolarite,
            'can_edit_scolarite': perm.can_edit_scolarite,
            'can_view_recrutement': perm.can_view_recrutement,
            'can_edit_recrutement': perm.can_edit_recrutement,
            'can_view_budget': perm.can_view_budget,
            'can_edit_budget': perm.can_edit_budget,
            'can_view_edt': perm.can_view_edt,
            'can_edit_edt': perm.can_edit_edt,
            'can_import': perm.can_import,
            'can_export': perm.can_export,
            'is_dept_admin': perm.is_dept_admin,
        }
    
    return permissions


def serialize_user(user: UserDB, permissions: dict) -> dict:
    """Serialize user for API response."""
    return {
        'id': user.id,
        'cas_login': user.cas_login,
        'email': user.email,
        'nom': user.nom,
        'prenom': user.prenom,
        'is_active': user.is_active,
        'is_superadmin': user.is_superadmin,
        'date_creation': user.date_creation.isoformat() if user.date_creation else None,
        'date_derniere_connexion': user.date_derniere_connexion.isoformat() if user.date_derniere_connexion else None,
        'permissions': permissions,
    }


# ==================== AUTH ROUTES ====================

@router.get("/login")
async def login_redirect(return_url: Optional[str] = Query(None)):
    """
    Redirect to CAS login page.
    
    After successful CAS login, user will be redirected back to /auth/cas/callback
    """
    cas = get_cas_adapter(
        cas_url=settings.cas_server_url,
        service_url=settings.cas_service_url,
        use_mock=settings.cas_use_mock,
    )
    
    login_url = cas.get_login_url(return_url)
    return RedirectResponse(url=login_url)


@router.get("/cas/callback")
async def cas_callback(
    ticket: Optional[str] = Query(None),
    return_url: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    CAS callback endpoint - validates ticket and creates session.
    
    CAS redirects here with a ticket parameter after successful login.
    """
    if not ticket:
        raise HTTPException(status_code=400, detail="No ticket provided")
    
    cas = get_cas_adapter(
        cas_url=settings.cas_server_url,
        service_url=settings.cas_service_url,
        use_mock=settings.cas_use_mock,
    )
    
    try:
        # Validate ticket with CAS server
        user_info = await cas.validate_ticket(ticket)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid CAS ticket")
        
        cas_login = user_info['user']
        attributes = user_info.get('attributes', {})
        
        # Get or create user in database
        user = get_or_create_user(db, cas_login, attributes)
        
        # Check if user is validated
        if not user.is_active:
            # Redirect to pending page
            redirect_url = f"{settings.frontend_url}/auth/pending"
            return RedirectResponse(url=redirect_url)
        
        # Create JWT token
        permissions = get_user_permissions(db, user)
        token_data = {
            'sub': str(user.id),
            'cas_login': user.cas_login,
            'is_superadmin': user.is_superadmin,
        }
        token = create_access_token(token_data)
        
        # Redirect to frontend with token
        redirect_url = return_url or settings.frontend_url
        redirect_url = f"{redirect_url}?token={token}"
        
        return RedirectResponse(url=redirect_url)
        
    finally:
        await cas.close()


@router.get("/logout")
async def logout(return_url: Optional[str] = Query(None)):
    """
    Logout - redirect to CAS logout.
    """
    cas = get_cas_adapter(
        cas_url=settings.cas_server_url,
        service_url=settings.cas_service_url,
        use_mock=settings.cas_use_mock,
    )
    
    redirect = return_url or settings.frontend_url
    logout_url = cas.get_logout_url(redirect)
    return RedirectResponse(url=logout_url)


@router.get("/me")
async def get_current_user(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user info.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not validated")
    
    permissions = get_user_permissions(db, user)
    return serialize_user(user, permissions)


@router.post("/validate-token")
async def validate_token(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """
    Validate JWT token and return basic user info.
    """
    payload = decode_access_token(token)
    if not payload:
        return {"valid": False, "error": "Invalid or expired token"}
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        return {"valid": False, "error": "User not found"}
    
    if not user.is_active:
        return {"valid": False, "error": "Account not validated", "pending": True}
    
    return {
        "valid": True,
        "user_id": user.id,
        "cas_login": user.cas_login,
        "is_superadmin": user.is_superadmin,
    }


# ==================== DEV/MOCK ROUTES ====================

@router.post("/dev/login")
async def dev_login(
    username: str = Query(..., description="Username for mock login"),
    db: Session = Depends(get_db),
):
    """
    Development-only: Direct login without CAS.
    Only available when cas_use_mock is True.
    """
    if not settings.cas_use_mock:
        raise HTTPException(status_code=403, detail="Dev login not available in production")
    
    # Create mock CAS attributes
    attributes = {
        'email': f'{username.replace(" ", ".").lower()}@univ.fr',
        'displayName': username.replace('.', ' ').title(),
    }
    
    # Get or create user
    user = get_or_create_user(db, username, attributes)
    
    # For dev, auto-activate and make superadmin if first user
    if not user.is_active:
        user_count = db.query(UserDB).count()
        if user_count == 1:
            # First user becomes superadmin
            user.is_active = True
            user.is_superadmin = True
            user.date_validation = datetime.utcnow()
            db.commit()
            logger.info(f"Auto-activated first user as superadmin: {username}")
        else:
            return {
                "error": "Account pending validation",
                "pending": True,
                "user_id": user.id,
            }
    
    # Create JWT token
    permissions = get_user_permissions(db, user)
    token_data = {
        'sub': str(user.id),
        'cas_login': user.cas_login,
        'is_superadmin': user.is_superadmin,
    }
    token = create_access_token(token_data)
    
    return {
        "token": token,
        "user": serialize_user(user, permissions),
    }
