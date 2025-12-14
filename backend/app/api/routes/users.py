"""Admin routes for user and permission management."""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.database import get_db
from app.config import get_settings
from app.models.db_models import UserDB, UserPermissionDB, DEPARTMENTS
from app.api.routes.auth import decode_access_token, get_user_permissions, serialize_user

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ==================== PYDANTIC MODELS ====================

class PermissionUpdate(BaseModel):
    """Permission update payload."""
    can_view_scolarite: Optional[bool] = None
    can_edit_scolarite: Optional[bool] = None
    can_view_recrutement: Optional[bool] = None
    can_edit_recrutement: Optional[bool] = None
    can_view_budget: Optional[bool] = None
    can_edit_budget: Optional[bool] = None
    can_view_edt: Optional[bool] = None
    can_edit_edt: Optional[bool] = None
    can_import: Optional[bool] = None
    can_export: Optional[bool] = None
    is_dept_admin: Optional[bool] = None


class UserUpdate(BaseModel):
    """User update payload."""
    email: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    is_active: Optional[bool] = None
    is_superadmin: Optional[bool] = None


class BulkPermissionGrant(BaseModel):
    """Grant permissions to multiple departments."""
    departments: List[str]
    permissions: PermissionUpdate


# ==================== AUTH HELPERS ====================

async def get_admin_user(token: str, db: Session) -> UserDB:
    """Validate token and ensure user is admin."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not validated")
    
    if not user.is_superadmin:
        # Check if dept admin for any department
        dept_admin = db.query(UserPermissionDB).filter(
            UserPermissionDB.user_id == user.id,
            UserPermissionDB.is_dept_admin == True
        ).first()
        
        if not dept_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


async def check_can_manage_user(admin: UserDB, target_user: UserDB, db: Session, department: Optional[str] = None):
    """Check if admin can manage target user."""
    if admin.is_superadmin:
        return True
    
    # Dept admin can only manage users in their departments
    admin_depts = db.query(UserPermissionDB).filter(
        UserPermissionDB.user_id == admin.id,
        UserPermissionDB.is_dept_admin == True
    ).all()
    
    admin_dept_list = [p.department for p in admin_depts]
    
    if department and department not in admin_dept_list:
        raise HTTPException(status_code=403, detail=f"No admin access to department {department}")
    
    # Cannot modify superadmins
    if target_user.is_superadmin and not admin.is_superadmin:
        raise HTTPException(status_code=403, detail="Cannot modify superadmin")
    
    return True


# ==================== USER MANAGEMENT ROUTES ====================

@router.get("/users")
async def list_users(
    token: str = Query(...),
    status: Optional[str] = Query(None, description="Filter: active, pending, all"),
    department: Optional[str] = Query(None, description="Filter by department permission"),
    db: Session = Depends(get_db),
):
    """
    List all users. Admin only.
    """
    admin = await get_admin_user(token, db)
    
    query = db.query(UserDB)
    
    # Filter by status
    if status == "active":
        query = query.filter(UserDB.is_active == True)
    elif status == "pending":
        query = query.filter(UserDB.is_active == False)
    
    users = query.order_by(UserDB.date_creation.desc()).all()
    
    # If not superadmin, filter to only users in admin's departments
    if not admin.is_superadmin:
        admin_depts = db.query(UserPermissionDB).filter(
            UserPermissionDB.user_id == admin.id,
            UserPermissionDB.is_dept_admin == True
        ).all()
        admin_dept_list = [p.department for p in admin_depts]
        
        # Filter users who have permissions in admin's departments
        filtered_users = []
        for user in users:
            user_perms = db.query(UserPermissionDB).filter(
                UserPermissionDB.user_id == user.id,
                UserPermissionDB.department.in_(admin_dept_list)
            ).first()
            # Include pending users too (they don't have perms yet)
            if user_perms or not user.is_active:
                filtered_users.append(user)
        users = filtered_users
    
    # Filter by department if specified
    if department:
        user_ids_in_dept = db.query(UserPermissionDB.user_id).filter(
            UserPermissionDB.department == department
        ).distinct()
        users = [u for u in users if u.id in [uid[0] for uid in user_ids_in_dept] or not u.is_active]
    
    result = []
    for user in users:
        perms = get_user_permissions(db, user)
        result.append(serialize_user(user, perms))
    
    return {"users": result, "total": len(result)}


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get specific user details."""
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await check_can_manage_user(admin, user, db)
    
    perms = get_user_permissions(db, user)
    return serialize_user(user, perms)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Update user details."""
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await check_can_manage_user(admin, user, db)
    
    # Only superadmin can grant superadmin
    if data.is_superadmin is not None and not admin.is_superadmin:
        raise HTTPException(status_code=403, detail="Only superadmin can grant superadmin status")
    
    # Update fields
    if data.email is not None:
        user.email = data.email
    if data.nom is not None:
        user.nom = data.nom
    if data.prenom is not None:
        user.prenom = data.prenom
    if data.is_active is not None:
        user.is_active = data.is_active
        if data.is_active and not user.date_validation:
            user.date_validation = datetime.utcnow()
            user.validated_by = admin.id
    if data.is_superadmin is not None:
        user.is_superadmin = data.is_superadmin
    
    db.commit()
    db.refresh(user)
    
    perms = get_user_permissions(db, user)
    return serialize_user(user, perms)


@router.post("/users/{user_id}/validate")
async def validate_user(
    user_id: int,
    token: str = Query(...),
    departments: Optional[List[str]] = Query(None, description="Departments to grant basic view access"),
    db: Session = Depends(get_db),
):
    """
    Validate/activate a pending user account.
    Optionally grant basic view permissions to specified departments.
    """
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_active:
        raise HTTPException(status_code=400, detail="User already validated")
    
    # Validate user
    user.is_active = True
    user.date_validation = datetime.utcnow()
    user.validated_by = admin.id
    
    # Grant basic view permissions if departments specified
    if departments:
        for dept in departments:
            if dept not in DEPARTMENTS:
                continue
            
            # Check admin has access to this dept
            if not admin.is_superadmin:
                admin_perm = db.query(UserPermissionDB).filter(
                    UserPermissionDB.user_id == admin.id,
                    UserPermissionDB.department == dept,
                    UserPermissionDB.is_dept_admin == True
                ).first()
                if not admin_perm:
                    continue
            
            # Create permission
            perm = UserPermissionDB(
                user_id=user.id,
                department=dept,
                can_view_scolarite=True,
                can_view_recrutement=True,
                can_view_edt=True,
                can_export=True,
                granted_by=admin.id,
            )
            db.add(perm)
    
    db.commit()
    db.refresh(user)
    
    perms = get_user_permissions(db, user)
    return serialize_user(user, perms)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Delete a user account."""
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await check_can_manage_user(admin, user, db)
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted", "user_id": user_id}


# ==================== PERMISSION MANAGEMENT ROUTES ====================

@router.get("/users/{user_id}/permissions")
async def get_user_permissions_route(
    user_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get all permissions for a user."""
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await check_can_manage_user(admin, user, db)
    
    perms = db.query(UserPermissionDB).filter(UserPermissionDB.user_id == user_id).all()
    
    result = []
    for perm in perms:
        result.append({
            'id': perm.id,
            'department': perm.department,
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
            'date_creation': perm.date_creation.isoformat() if perm.date_creation else None,
        })
    
    return {"user_id": user_id, "permissions": result}


@router.put("/users/{user_id}/permissions/{department}")
async def update_user_permission(
    user_id: int,
    department: str,
    data: PermissionUpdate,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Update permissions for a user in a specific department."""
    admin = await get_admin_user(token, db)
    
    if department not in DEPARTMENTS:
        raise HTTPException(status_code=400, detail=f"Invalid department: {department}")
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await check_can_manage_user(admin, user, db, department)
    
    # Get or create permission
    perm = db.query(UserPermissionDB).filter(
        UserPermissionDB.user_id == user_id,
        UserPermissionDB.department == department
    ).first()
    
    if not perm:
        perm = UserPermissionDB(
            user_id=user_id,
            department=department,
            granted_by=admin.id,
        )
        db.add(perm)
    
    # Update fields
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            # Only superadmin can grant dept_admin
            if field == 'is_dept_admin' and not admin.is_superadmin:
                admin_perm = db.query(UserPermissionDB).filter(
                    UserPermissionDB.user_id == admin.id,
                    UserPermissionDB.department == department,
                    UserPermissionDB.is_dept_admin == True
                ).first()
                if not admin_perm:
                    continue
            setattr(perm, field, value)
    
    db.commit()
    db.refresh(perm)
    
    return {
        'id': perm.id,
        'user_id': user_id,
        'department': department,
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


@router.delete("/users/{user_id}/permissions/{department}")
async def delete_user_permission(
    user_id: int,
    department: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Remove all permissions for a user in a department."""
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await check_can_manage_user(admin, user, db, department)
    
    perm = db.query(UserPermissionDB).filter(
        UserPermissionDB.user_id == user_id,
        UserPermissionDB.department == department
    ).first()
    
    if perm:
        db.delete(perm)
        db.commit()
    
    return {"message": "Permission removed", "user_id": user_id, "department": department}


@router.post("/users/{user_id}/permissions/bulk")
async def bulk_grant_permissions(
    user_id: int,
    data: BulkPermissionGrant,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Grant same permissions to multiple departments at once."""
    admin = await get_admin_user(token, db)
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await check_can_manage_user(admin, user, db)
    
    updated = []
    for dept in data.departments:
        if dept not in DEPARTMENTS:
            continue
        
        # Check admin access
        try:
            await check_can_manage_user(admin, user, db, dept)
        except HTTPException:
            continue
        
        # Get or create permission
        perm = db.query(UserPermissionDB).filter(
            UserPermissionDB.user_id == user_id,
            UserPermissionDB.department == dept
        ).first()
        
        if not perm:
            perm = UserPermissionDB(
                user_id=user_id,
                department=dept,
                granted_by=admin.id,
            )
            db.add(perm)
        
        # Update fields
        for field, value in data.permissions.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(perm, field, value)
        
        updated.append(dept)
    
    db.commit()
    
    return {"message": "Permissions updated", "departments": updated}


# ==================== DEPARTMENT OVERVIEW ====================

@router.get("/departments")
async def list_departments(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get list of departments with user counts."""
    admin = await get_admin_user(token, db)
    
    result = []
    for dept in DEPARTMENTS:
        # Count users with any permission in this dept
        user_count = db.query(UserPermissionDB).filter(
            UserPermissionDB.department == dept
        ).distinct(UserPermissionDB.user_id).count()
        
        # Count admins
        admin_count = db.query(UserPermissionDB).filter(
            UserPermissionDB.department == dept,
            UserPermissionDB.is_dept_admin == True
        ).count()
        
        result.append({
            'department': dept,
            'user_count': user_count,
            'admin_count': admin_count,
        })
    
    # Pending users count
    pending = db.query(UserDB).filter(UserDB.is_active == False).count()
    
    return {
        "departments": result,
        "pending_users": pending,
        "available_departments": DEPARTMENTS,
    }
