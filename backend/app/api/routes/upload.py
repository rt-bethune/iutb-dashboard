"""File upload routes."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import os
from datetime import datetime

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/file")
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    type: str = Form(..., description="Type of data: budget, edt, parcoursup, etudiants, notes, other"),
    description: Optional[str] = Form(None, description="File description"),
):
    """
    Upload a data file.
    
    Supported types:
    - budget: Excel file with budget data
    - edt: Excel file with schedule data
    - parcoursup: CSV file with Parcoursup export
    - etudiants: CSV/Excel file with student list
    - notes: CSV/Excel file with grades
    - other: Any other file
    """
    # Validate file type
    allowed_extensions = {
        "budget": [".xlsx", ".xls", ".csv"],
        "edt": [".xlsx", ".xls", ".csv"],
        "parcoursup": [".csv"],
        "etudiants": [".csv", ".xlsx", ".xls"],
        "notes": [".csv", ".xlsx", ".xls"],
        "other": [".xlsx", ".xls", ".csv", ".pdf"],
    }
    
    if type not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Type inconnu: {type}. Types acceptés: {list(allowed_extensions.keys())}"
        )
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions[type]:
        raise HTTPException(
            status_code=400,
            detail=f"Extension {ext} non acceptée pour le type {type}. Extensions acceptées: {allowed_extensions[type]}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille max: {settings.max_upload_size / 1024 / 1024}MB"
        )
    
    # Create upload directory if needed
    upload_dir = os.path.join(settings.upload_dir, type)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, safe_filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(content)
    
    return {
        "success": True,
        "filename": safe_filename,
        "type": type,
        "size": len(content),
        "path": filepath,
    }


@router.get("/files")
async def list_uploaded_files(
    type: Optional[str] = None,
):
    """
    List uploaded files.
    """
    files = []
    base_dir = settings.upload_dir
    
    if not os.path.exists(base_dir):
        return {"files": []}
    
    types_to_scan = [type] if type else os.listdir(base_dir)
    
    for data_type in types_to_scan:
        type_dir = os.path.join(base_dir, data_type)
        if os.path.isdir(type_dir):
            for filename in os.listdir(type_dir):
                filepath = os.path.join(type_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "type": data_type,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
    
    return {"files": sorted(files, key=lambda x: x["modified"], reverse=True)}


@router.delete("/file/{type}/{filename}")
async def delete_file(type: str, filename: str):
    """
    Delete an uploaded file.
    """
    filepath = os.path.join(settings.upload_dir, type, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    try:
        os.remove(filepath)
        return {"success": True, "message": f"Fichier {filename} supprimé"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@router.get("/download/{type}/{filename}")
async def download_file(type: str, filename: str):
    """
    Download an uploaded file.
    """
    from fastapi.responses import FileResponse
    
    filepath = os.path.join(settings.upload_dir, type, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type='application/octet-stream'
    )
