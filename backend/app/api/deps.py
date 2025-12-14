"""Common dependencies for API routes."""

from typing import Annotated, Optional
from functools import lru_cache
from enum import Enum
import logging

from fastapi import Depends, Path, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.adapters.scodoc import ScoDocAdapter
from app.adapters.excel import ExcelAdapter
from app.adapters.parcoursup import ParcoursupAdapter
from app.database import get_db

logger = logging.getLogger(__name__)


class Department(str, Enum):
    """Valid departments."""
    RT = "RT"
    GEII = "GEII"
    GCCD = "GCCD"
    GMP = "GMP"
    QLIO = "QLIO"
    CHIMIE = "CHIMIE"


VALID_DEPARTMENTS = [d.value for d in Department]


def validate_department(department: str) -> str:
    """Validate department code."""
    dept_upper = department.upper()
    if dept_upper not in VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Département invalide: {department}. Valeurs autorisées: {', '.join(VALID_DEPARTMENTS)}"
        )
    return dept_upper


# Department path parameter dependency
DepartmentDep = Annotated[str, Path(
    ..., 
    description="Code du département (RT, GEII, GCCD, GMP, QLIO, CHIMIE)",
    pattern="^(RT|GEII|GCCD|GMP|QLIO|CHIMIE)$",
    examples=["RT", "GEII"]
)]


# Settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ==================== AUTHENTICATION DEPENDENCIES ====================

def get_token_from_header(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None, description="JWT token (alternative to header)"),
) -> Optional[str]:
    """Extract JWT token from Authorization header or query param."""
    if authorization:
        # Bearer token
        if authorization.startswith("Bearer "):
            return authorization[7:]
        return authorization
    return token


def get_current_user(
    token: Optional[str] = Depends(get_token_from_header),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user from JWT token.
    Returns None if no token or invalid token (for optional auth).
    """
    if not token:
        return None
    
    # Import here to avoid circular imports
    from app.api.routes.auth import decode_access_token
    from app.models.db_models import UserDB
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user or not user.is_active:
        return None
    
    return user


def require_auth(
    token: Optional[str] = Depends(get_token_from_header),
    db: Session = Depends(get_db),
):
    """
    Require authenticated user. Raises 401 if not authenticated.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    from app.api.routes.auth import decode_access_token
    from app.models.db_models import UserDB
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not validated")
    
    return user


# Type alias for authenticated user dependency
from app.models.db_models import UserDB
AuthUserDep = Annotated[UserDB, Depends(require_auth)]
OptionalUserDep = Annotated[Optional[UserDB], Depends(get_current_user)]


# ==================== PERMISSION CHECKING ====================

def get_user_permission_for_department(user: UserDB, department: str, db: Session):
    """Get user's permission object for a specific department."""
    from app.models.db_models import UserPermissionDB
    
    return db.query(UserPermissionDB).filter(
        UserPermissionDB.user_id == user.id,
        UserPermissionDB.department == department.upper()
    ).first()


def check_permission(
    user: UserDB,
    department: str,
    domain: str,  # scolarite, recrutement, budget, edt
    action: str,  # view, edit
    db: Session,
) -> bool:
    """
    Check if user has permission for a specific action on a domain in a department.
    Superadmins have all permissions.
    """
    logger.info(f"Checking permission: user={user.cas_login}, dept={department}, domain={domain}, action={action}")
    
    if user.is_superadmin:
        logger.info(f"User {user.cas_login} is superadmin - access granted")
        return True
    
    perm = get_user_permission_for_department(user, department, db)
    if not perm:
        logger.info(f"No permission found for user {user.cas_login} in dept {department} - access denied")
        return False
    
    # Dept admins have all permissions for their department
    if perm.is_dept_admin:
        logger.info(f"User {user.cas_login} is dept_admin for {department} - access granted")
        return True
    
    # Check specific permission
    perm_field = f"can_{action}_{domain}"
    has_perm = getattr(perm, perm_field, False)
    logger.info(f"User {user.cas_login} permission {perm_field}={has_perm}")
    return has_perm


def check_import_permission(user: UserDB, department: str, db: Session) -> bool:
    """Check if user can import data for a department."""
    if user.is_superadmin:
        return True
    
    perm = get_user_permission_for_department(user, department, db)
    if not perm:
        return False
    
    return perm.is_dept_admin or perm.can_import


def check_export_permission(user: UserDB, department: str, db: Session) -> bool:
    """Check if user can export data for a department."""
    if user.is_superadmin:
        return True
    
    perm = get_user_permission_for_department(user, department, db)
    if not perm:
        return False
    
    return perm.is_dept_admin or perm.can_export


# ==================== PERMISSION DEPENDENCY FACTORIES ====================

class PermissionChecker:
    """
    Dependency factory for checking domain permissions.
    Usage: Depends(PermissionChecker("scolarite", "view"))
    """
    def __init__(self, domain: str, action: str):
        self.domain = domain
        self.action = action
    
    def __call__(
        self,
        department: DepartmentDep,
        user: UserDB = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> UserDB:
        if not check_permission(user, department, self.domain, self.action, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: cannot {self.action} {self.domain} for department {department}"
            )
        return user


class ImportPermissionChecker:
    """Dependency factory for checking import permission."""
    def __call__(
        self,
        department: DepartmentDep,
        user: UserDB = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> UserDB:
        if not check_import_permission(user, department, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: cannot import data for department {department}"
            )
        return user


class ExportPermissionChecker:
    """Dependency factory for checking export permission."""
    def __call__(
        self,
        department: DepartmentDep,
        user: UserDB = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> UserDB:
        if not check_export_permission(user, department, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: cannot export data for department {department}"
            )
        return user


# Pre-built permission checkers for common use cases
require_view_scolarite = PermissionChecker("scolarite", "view")
require_edit_scolarite = PermissionChecker("scolarite", "edit")
require_view_recrutement = PermissionChecker("recrutement", "view")
require_edit_recrutement = PermissionChecker("recrutement", "edit")
require_view_budget = PermissionChecker("budget", "view")
require_edit_budget = PermissionChecker("budget", "edit")
require_view_edt = PermissionChecker("edt", "view")
require_edit_edt = PermissionChecker("edt", "edit")
require_import = ImportPermissionChecker()
require_export = ExportPermissionChecker()


def get_scodoc_adapter_for_department(department: str) -> ScoDocAdapter:
    """Get ScoDoc adapter instance for a specific department."""
    settings = get_settings()
    return ScoDocAdapter(
        base_url=settings.scodoc_base_url,
        username=settings.scodoc_username,
        password=settings.scodoc_password,
        department=department,  # Use the department from path
    )


@lru_cache
def get_scodoc_adapter() -> ScoDocAdapter:
    """Get ScoDoc adapter instance (deprecated - use get_scodoc_adapter_for_department)."""
    settings = get_settings()
    return ScoDocAdapter(
        base_url=settings.scodoc_base_url,
        username=settings.scodoc_username,
        password=settings.scodoc_password,
        department=settings.scodoc_department,
    )


@lru_cache
def get_excel_adapter() -> ExcelAdapter:
    """Get Excel adapter instance."""
    return ExcelAdapter()


@lru_cache
def get_parcoursup_adapter() -> ParcoursupAdapter:
    """Get Parcoursup adapter instance."""
    return ParcoursupAdapter()


# Adapter dependencies
ScoDocDep = Annotated[ScoDocAdapter, Depends(get_scodoc_adapter)]
ExcelDep = Annotated[ExcelAdapter, Depends(get_excel_adapter)]
ParcoursupDep = Annotated[ParcoursupAdapter, Depends(get_parcoursup_adapter)]
