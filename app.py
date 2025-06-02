#!/usr/bin/env python3
"""
FastAPI backend for TOC Visualization and PDF Cropping
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pymupdf
import tempfile
import os
import json
import shutil
import glob
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from typing import List, Dict, Optional
import uuid

app = FastAPI(title="TOC Visualizer & PDF Cropper", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store uploaded files temporarily
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory storage for file info (in production, use a database)
file_store = {}

def clear_upload_folder():
    """Clear all files in the temp_uploads folder."""
    try:
        if os.path.exists(UPLOAD_DIR):
            # Remove all files in the directory
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
        
        # Clear the in-memory file store as well
        file_store.clear()
        print(f"Cleared upload folder: {UPLOAD_DIR}")
        
    except Exception as e:
        print(f"Error clearing upload folder: {e}")

def extract_toc_from_document(file_path: str) -> List[Dict[str, any]]:
    """Extract TOC from document using PyMuPDF."""
    try:
        doc = pymupdf.open(file_path)
        toc_raw = doc.get_toc()
        
        toc_entries = []
        for entry in toc_raw:
            level = entry[0]
            title = entry[1]
            page_number = entry[2]
            
            toc_entries.append({
                'title': title.strip(),
                'level': level,
                'page_number': page_number,
                'id': str(uuid.uuid4())  # Unique ID for frontend
            })
        
        doc.close()
        return toc_entries
    except Exception as e:
        raise Exception(f"Error extracting TOC: {str(e)}")

def get_document_info(file_path: str) -> Dict[str, any]:
    """Get document metadata and info."""
    try:
        doc = pymupdf.open(file_path)
        
        info = {
            'page_count': doc.page_count,
            'is_pdf': doc.is_pdf,
            'is_encrypted': doc.is_encrypted,
            'metadata': doc.metadata or {},
            'toc': extract_toc_from_document(file_path)
        }
        
        doc.close()
        return info
    except Exception as e:
        raise Exception(f"Error getting document info: {str(e)}")

def crop_pdf_pages(input_path: str, start_page: int, end_page: int, output_path: str):
    """Crop PDF pages using PyPDF2."""
    try:
        pdf_reader = PdfReader(input_path)
        total_pages = len(pdf_reader.pages)
        
        if start_page < 1:
            start_page = 1
        if end_page > total_pages:
            end_page = total_pages
            
        pdf_writer = PdfWriter()
        for page_num in range(start_page - 1, end_page):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        with open(output_path, "wb") as output_file:
            pdf_writer.write(output_file)
            
        return True
    except Exception as e:
        raise Exception(f"Error cropping PDF: {str(e)}")

@app.post("/upload-document/")
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

@app.post("/crop-section/")
async def crop_section(
    file_id: str = Form(...),
    start_page: int = Form(...),
    end_page: int = Form(...),
    section_title: str = Form(...)
):
    """Crop a section of the PDF based on page range."""
    if file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_info = file_store[file_id]
        input_path = file_info['file_path']
        
        # Generate output filename
        safe_title = "".join(c for c in section_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        output_filename = f"{safe_title}_pages_{start_page}-{end_page}.pdf"
        output_path = os.path.join(UPLOAD_DIR, f"cropped_{uuid.uuid4()}.pdf")
        
        # Crop PDF
        crop_pdf_pages(input_path, start_page, end_page, output_path)
        
        # Return file for download
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type='application/pdf'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cropping PDF: {str(e)}")

@app.get("/file-info/{file_id}")
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

@app.get("/")
async def root():
    return {"message": "TOC Visualizer & PDF Cropper API", "docs": "/docs"}

@app.post("/clear-uploads/")
async def clear_uploads_endpoint():
    """Manually clear all uploaded files."""
    try:
        clear_upload_folder()
        return JSONResponse(content={"message": "Upload folder cleared successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing uploads: {str(e)}")

@app.get("/upload-stats/")
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

# Cleanup endpoint (optional)
@app.delete("/cleanup/{file_id}")
async def cleanup_file(file_id: str):
    """Clean up uploaded file."""
    if file_id in file_store:
        file_path = file_store[file_id]['file_path']
        if os.path.exists(file_path):
            os.unlink(file_path)
        del file_store[file_id]
        return {"message": "File cleaned up"}
    return {"message": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 