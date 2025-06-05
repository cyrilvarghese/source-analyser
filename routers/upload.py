"""
Upload router for file uploads and document processing
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from utils import (
    UPLOAD_DIR, 
    file_store, 
    clear_upload_folder, 
    get_document_info
)

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post("/document/")
async def upload_document(file: UploadFile = File(...)):
    """Upload document and extract TOC."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Clear previous uploads before processing new file
        clear_upload_folder()
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract document info and TOC
        doc_info = get_document_info(file_path)
        
        # Store file info
        file_store[file_id] = {
            'original_name': file.filename,
            'file_path': file_path,
            'doc_info': doc_info
        }
        
        return JSONResponse(content={
            "file_id": file_id,
            "filename": file.filename,
            "document_info": doc_info
        })
        
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.unlink(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/file-info/{file_id}")
async def get_file_info(file_id: str):
    """Get file information and TOC."""
    if file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = file_store[file_id]
    return JSONResponse(content={
        "file_id": file_id,
        "filename": file_info['original_name'],
        "document_info": file_info['doc_info']
    })

@router.get("/stats/")
async def get_upload_stats():
    """Get statistics about uploaded files."""
    try:
        file_count = len([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]) if os.path.exists(UPLOAD_DIR) else 0
        total_size = sum(os.path.getsize(os.path.join(UPLOAD_DIR, f)) for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))) if os.path.exists(UPLOAD_DIR) else 0
        
        return JSONResponse(content={
            "files_count": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "active_sessions": len(file_store)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}") 