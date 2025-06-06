#!/usr/bin/env python3
"""
FastAPI backend for TOC Visualization and PDF Cropping
Refactored with separate routers for better organization
"""

import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import upload, tables, chapters, extractions, admin, debug, assessment, master_cases

# Import utilities and configurations
from utils import (
    UPLOAD_DIR, 
    CROPPED_PDFS_DIR, 
    chapter_extractions
)

app = FastAPI(title="TOC Visualizer & PDF Cropper", version="2.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def mount_extraction_folders():
    """Dynamically mount all extraction folders as static file directories."""
    # First mount the main extracted-data directory
    extracted_data_dir = Path("extracted-data")
    if extracted_data_dir.exists():
        try:
            app.mount("/extracted-data", StaticFiles(directory="extracted-data"), name="extracted_data")
            print(f"Mounted main extracted-data directory: /extracted-data -> extracted-data")
        except Exception as e:
            print(f"Warning: Could not mount extracted-data directory: {e}")
    
    # Mount cropped PDFs directory
    cropped_pdfs_dir = Path(CROPPED_PDFS_DIR)
    if cropped_pdfs_dir.exists():
        try:
            app.mount("/cropped-pdfs", StaticFiles(directory=CROPPED_PDFS_DIR), name="cropped_pdfs")
            print(f"Mounted cropped PDFs directory: /cropped-pdfs -> {CROPPED_PDFS_DIR}")
        except Exception as e:
            print(f"Warning: Could not mount cropped PDFs directory: {e}")
    
    # Mount individual extraction folders within extracted-data
    if extracted_data_dir.exists():
        for folder in extracted_data_dir.iterdir():
            if folder.is_dir() and folder.name.endswith('_extracted'):
                try:
                    mount_path = f"/extracts/{folder.name}"
                    app.mount(mount_path, StaticFiles(directory=str(folder)), name=f"extract_{folder.name}")
                    print(f"Mounted extraction folder: {mount_path} -> {folder}")
                except Exception as e:
                    print(f"Warning: Could not mount {folder}: {e}")
    
    # Also check current directory for legacy extractions
    current_dir = Path(".")
    extraction_patterns = ["*_extracted", "*_docling_extracted", "*_images"]
    
    for pattern in extraction_patterns:
        for folder in current_dir.glob(pattern):
            if folder.is_dir() and not str(folder).startswith("extracted-data"):
                try:
                    mount_path = f"/extracts/{folder.name}"
                    app.mount(mount_path, StaticFiles(directory=str(folder)), name=f"extract_{folder.name}")
                    print(f"Mounted legacy extraction folder: {mount_path} -> {folder}")
                except Exception as e:
                    print(f"Warning: Could not mount {folder}: {e}")

def recover_chapters_from_extractions():
    """Attempt to recover chapter information from existing extraction directories."""
    print("🔄 Attempting to recover chapters from existing extractions...")
    
    recovered_count = 0
    extracted_data_dir = Path("extracted-data")
    
    if not extracted_data_dir.exists():
        print("📁 No extracted-data directory found")
        return recovered_count
    
    for extraction_dir in extracted_data_dir.glob("*_docling_extracted"):
        if extraction_dir.is_dir():
            # Try to find corresponding cropped PDF in the cropped-pdfs directory
            potential_pdfs = []
            cropped_pdfs_dir = Path(CROPPED_PDFS_DIR)
            
            if cropped_pdfs_dir.exists():
                # Look for PDFs that might match this extraction
                extraction_base_name = extraction_dir.name.replace('_docling_extracted', '')
                for pdf_file in cropped_pdfs_dir.glob("*.pdf"):
                    if extraction_base_name.lower() in pdf_file.name.lower():
                        potential_pdfs.append(str(pdf_file))
                
                # Also check all PDF files as fallback
                if not potential_pdfs:
                    potential_pdfs = [str(f) for f in cropped_pdfs_dir.glob("*.pdf")]
            
            # Also check the old upload directory for backwards compatibility
            if not potential_pdfs and Path(UPLOAD_DIR).exists():
                for file in Path(UPLOAD_DIR).iterdir():
                    if file.suffix == '.pdf' and 'cropped_' in file.name:
                        potential_pdfs.append(str(file))
            
            # Create a basic chapter entry (without full metadata)
            chapter_id = str(uuid.uuid4())
            section_title = extraction_dir.name.replace('_docling_extracted', '').replace('_', ' ')
            
            # Use the first available PDF or create a placeholder
            cropped_pdf_path = potential_pdfs[0] if potential_pdfs else ""
            cropped_pdf_filename = Path(cropped_pdf_path).name if cropped_pdf_path else f"{section_title}.pdf"
            
            # Find HTML files for this extraction
            html_files = list(extraction_dir.glob("*.html"))
            html_url = None
            html_full_url = None
            
            if html_files:
                html_file = html_files[0]
                html_url = f"/extracted-data/{extraction_dir.name}/{html_file.name}"
                html_full_url = f"http://localhost:8001{html_url}"
            
            chapter_extractions[chapter_id] = {
                "chapter_id": chapter_id,
                "section_title": section_title,
                "start_page": 1,  # Placeholder
                "end_page": 1,    # Placeholder
                "cropped_pdf_path": cropped_pdf_path,
                "cropped_pdf_filename": cropped_pdf_filename,
                "extraction_result": {
                    "success": True,
                    "extraction_dir": extraction_dir.name,
                    "extraction_path": str(extraction_dir),
                    "images": [],
                    "html_path": str(html_files[0]) if html_files else None,
                    "html_url": html_url,
                    "html_full_url": html_full_url,
                    "total_images": len(list(extraction_dir.glob("*.png"))),
                    "html_available": len(html_files) > 0
                },
                "created_at": str(uuid.uuid4())  # Placeholder
            }
            
            recovered_count += 1
            print(f"📦 Recovered chapter: {section_title} (ID: {chapter_id})")
            if cropped_pdf_path:
                print(f"    📄 PDF: {cropped_pdf_filename}")
            if html_url:
                print(f"    🌐 HTML: {html_url}")
    
    print(f"✅ Recovered {recovered_count} chapters from existing extractions")
    return recovered_count

# Include all routers
app.include_router(upload.router)
app.include_router(tables.router)
app.include_router(chapters.router)
app.include_router(extractions.router)
app.include_router(admin.router)
app.include_router(debug.router)
app.include_router(assessment.router)
app.include_router(master_cases.router)

# Legacy endpoints for backward compatibility
@app.post("/upload-document/")
async def legacy_upload_document(*args, **kwargs):
    """Legacy endpoint - redirects to new upload router."""
    return await upload.upload_document(*args, **kwargs)

@app.post("/crop-section/")
async def legacy_crop_section(*args, **kwargs):
    """Legacy endpoint - redirects to new chapters router."""
    return await chapters.crop_section(*args, **kwargs)

@app.post("/extract-table-json/")
async def legacy_extract_table_json(*args, **kwargs):
    """Legacy endpoint - redirects to new tables router."""
    return await tables.extract_table_json(*args, **kwargs)

@app.get("/download-cropped/{chapter_id}")
async def legacy_download_cropped_pdf(chapter_id: str):
    """Legacy endpoint - redirects to new chapters router."""
    return await chapters.download_cropped_pdf(chapter_id)

@app.get("/list-chapters")
async def legacy_list_chapters():
    """Legacy endpoint - redirects to new chapters router."""
    return await chapters.list_chapters()

# Root endpoints
@app.get("/")
async def root():
    """Serve the main application homepage."""
    try:
        return FileResponse("index.html", media_type="text/html")
    except Exception as e:
        return JSONResponse(
            status_code=404,
            content={"detail": "index.html not found"}
        )

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "TOC Visualizer & PDF Cropper API", 
        "version": "2.0.0",
        "docs": "/docs",
        "routers": {
            "upload": "/api/upload",
            "tables": "/api/tables", 
            "chapters": "/api/chapters",
            "extractions": "/api/extractions",
            "admin": "/api/admin",
            "debug": "/api/debug"
        }
    }

# Startup operations
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🚀 Starting File Cropper API v2.0.0")
    print("📂 Setting up directories and mounting static files...")
    
    # Mount extraction folders at startup
    mount_extraction_folders()
    
    # Attempt to recover chapters from existing extractions
    recover_chapters_from_extractions()
    
    print("✅ Application startup complete")

# Mount static files for frontend (HTML, JS, CSS) - this must be last to avoid route conflicts
try:
    app.mount("/", StaticFiles(directory=".", html=True), name="frontend")
    print("Mounted frontend static files: / -> current directory")
except Exception as e:
    print(f"Warning: Could not mount frontend static files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 