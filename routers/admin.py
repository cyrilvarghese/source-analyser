"""
Admin router for cleanup and administrative functions
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from utils import (
    UPLOAD_DIR, 
    file_store, 
    chapter_extractions, 
    clear_upload_folder
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/clear-uploads/")
async def clear_uploads_endpoint():
    """Manually clear all uploaded files."""
    try:
        clear_upload_folder()
        return JSONResponse(content={"message": "Upload folder cleared successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing uploads: {str(e)}")

@router.delete("/cleanup/{file_id}")
async def cleanup_file(file_id: str):
    """Clean up uploaded file."""
    if file_id in file_store:
        file_path = file_store[file_id]['file_path']
        if os.path.exists(file_path):
            os.unlink(file_path)
        del file_store[file_id]
        return {"message": "File cleaned up"}
    return {"message": "File not found"}

@router.get("/stats/")
async def get_system_stats():
    """Get comprehensive system statistics."""
    try:
        # Upload directory stats
        file_count = len([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]) if os.path.exists(UPLOAD_DIR) else 0
        total_size = sum(os.path.getsize(os.path.join(UPLOAD_DIR, f)) for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))) if os.path.exists(UPLOAD_DIR) else 0
        
        return JSONResponse(content={
            "uploads": {
                "files_count": file_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "active_sessions": len(file_store)
            },
            "chapters": {
                "total_chapters": len(chapter_extractions),
                "active_chapters": len(chapter_extractions)
            },
            "directories": {
                "upload_dir_exists": os.path.exists(UPLOAD_DIR),
                "upload_dir": UPLOAD_DIR
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@router.get("/health/")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "healthy",
        "service": "File Cropper API",
        "version": "1.0.0"
    }) 