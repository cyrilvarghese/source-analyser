#!/usr/bin/env python3
"""
FastAPI backend for TOC Visualization and PDF Cropping
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
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
import re

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

def mount_extraction_folders():
    """Dynamically mount all extraction folders as static file directories."""
    current_dir = Path(".")
    
    # Look for folders ending with '_extracted' or similar patterns
    extraction_patterns = ["*_extracted", "*_docling_extracted", "*_images"]
    
    for pattern in extraction_patterns:
        for folder in current_dir.glob(pattern):
            if folder.is_dir():
                try:
                    # Mount each extraction folder individually
                    mount_path = f"/extracts/{folder.name}"
                    app.mount(mount_path, StaticFiles(directory=str(folder)), name=f"extract_{folder.name}")
                    print(f"Mounted extraction folder: {mount_path} -> {folder}")
                except Exception as e:
                    print(f"Warning: Could not mount {folder}: {e}")

# Mount extraction folders at startup
mount_extraction_folders()

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

@app.get("/serve-docling-html/{extract_folder}/{html_filename}")
async def serve_docling_html(extract_folder: str, html_filename: str):
    """Serve Docling-generated HTML files for display in browser."""
    try:
        # Construct the path to the HTML file
        html_path = Path(extract_folder) / html_filename
        
        # Security check: ensure the path is safe
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        
        # Ensure it's an HTML file
        if not html_filename.lower().endswith('.html'):
            raise HTTPException(status_code=400, detail="Only HTML files are supported")
        
        # Read the HTML content and serve it directly
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Update image paths in HTML to use the new mounted paths
        # Replace relative image paths with absolute paths to mounted folder
        
        # Pattern to match image src attributes
        img_pattern = r'src="([^"]*\.png)"'
        
        def replace_img_src(match):
            original_src = match.group(1)
            # Convert to absolute path using the mounted folder
            new_src = f"/extracts/{extract_folder}/{original_src}"
            return f'src="{new_src}"'
        
        # Replace all image sources
        html_content = re.sub(img_pattern, replace_img_src, html_content)
        
        # Return HTML content with proper headers for browser display
        return HTMLResponse(
            content=html_content,
            status_code=200,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving HTML file: {str(e)}")

@app.get("/view/{extract_folder}/{html_filename}")
async def view_extraction(extract_folder: str, html_filename: str):
    """Alternative route to view extracted content - redirects to mounted static files."""
    try:
        # Check if the folder is mounted
        mount_path = f"/extracts/{extract_folder}/{html_filename}"
        
        # Verify the file exists
        file_path = Path(extract_folder) / html_filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # For HTML files, use the HTML serving route
        if html_filename.lower().endswith('.html'):
            return await serve_docling_html(extract_folder, html_filename)
        
        # For other files, redirect to the mounted static path
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=mount_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing file: {str(e)}")

@app.post("/remount-extractions")
async def remount_extractions():
    """Re-scan and mount new extraction folders."""
    try:
        mount_extraction_folders()
        return JSONResponse(content={"message": "Extraction folders remounted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error remounting: {str(e)}")

@app.get("/list-docling-extracts")
async def list_docling_extracts():
    """List all available Docling extraction folders and their HTML files with mounted paths."""
    try:
        current_dir = Path(".")
        extract_folders = []
        
        # Look for folders ending with '_docling_extracted' or '_extracted'
        for folder in current_dir.glob("*_extracted"):
            if folder.is_dir():
                html_files = list(folder.glob("*.html"))
                if html_files:
                    html_file_info = []
                    for html_file in html_files:
                        html_file_info.append({
                            "filename": html_file.name,
                            "view_url": f"/view/{folder.name}/{html_file.name}",
                            "serve_url": f"/serve-docling-html/{folder.name}/{html_file.name}",
                            "static_url": f"/extracts/{folder.name}/{html_file.name}"
                        })
                    
                    folder_info = {
                        "folder_name": folder.name,
                        "mount_path": f"/extracts/{folder.name}",
                        "html_files": html_file_info,
                        "image_count": len(list(folder.glob("*.png"))),
                        "markdown_files": [f.name for f in folder.glob("*.md")],
                        "all_assets": [f.name for f in folder.iterdir() if f.is_file()]
                    }
                    extract_folders.append(folder_info)
        
        return JSONResponse(content={
            "extract_folders": extract_folders,
            "total_folders": len(extract_folders),
            "instructions": {
                "view_html": "Use view_url to see HTML with proper image loading",
                "serve_html": "Use serve_url for direct HTML serving",
                "static_access": "Use static_url for direct file access",
                "remount": "POST to /remount-extractions to detect new folders"
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing extracts: {str(e)}")

@app.get("/docling-extract-info/{folder_name}")
async def get_docling_extract_info(folder_name: str):
    """Get detailed information about a specific Docling extraction folder."""
    try:
        folder_path = Path(folder_name)
        
        if not folder_path.exists() or not folder_path.is_dir():
            raise HTTPException(status_code=404, detail="Extract folder not found")
        
        # Get all files in the folder
        files_info = []
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                if file_size > 1024 * 1024:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{file_size / 1024:.1f} KB"
                
                files_info.append({
                    "filename": file_path.name,
                    "size": size_str,
                    "type": file_path.suffix.lower(),
                    "is_html": file_path.suffix.lower() == '.html',
                    "is_image": file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif'],
                    "is_markdown": file_path.suffix.lower() == '.md'
                })
        
        return JSONResponse(content={
            "folder_name": folder_name,
            "files": files_info,
            "total_files": len(files_info),
            "html_files": [f for f in files_info if f["is_html"]],
            "image_files": [f for f in files_info if f["is_image"]],
            "markdown_files": [f for f in files_info if f["is_markdown"]]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting extract info: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 