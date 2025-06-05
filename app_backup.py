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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import docling extraction function
try:
    from docling_figure_extractor import extract_figures_with_docling
except ImportError:
    print("Warning: docling_figure_extractor not found. PDF extraction features will be limited.")
    extract_figures_with_docling = None

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
CROPPED_PDFS_DIR = "cropped-pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CROPPED_PDFS_DIR, exist_ok=True)

# In-memory storage for file info (in production, use a database)
file_store = {}

# Chapter mapping for extracted content
chapter_extractions = {}

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
            if not potential_pdfs and os.path.exists(UPLOAD_DIR):
                for file in os.listdir(UPLOAD_DIR):
                    if file.endswith('.pdf') and 'cropped_' in file:
                        potential_pdfs.append(os.path.join(UPLOAD_DIR, file))
            
            # Create a basic chapter entry (without full metadata)
            chapter_id = str(uuid.uuid4())
            section_title = extraction_dir.name.replace('_docling_extracted', '').replace('_', ' ')
            
            # Use the first available PDF or create a placeholder
            cropped_pdf_path = potential_pdfs[0] if potential_pdfs else ""
            cropped_pdf_filename = os.path.basename(cropped_pdf_path) if cropped_pdf_path else f"{section_title}.pdf"
            
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

# Mount extraction folders at startup
mount_extraction_folders()

# Attempt to recover chapters from existing extractions
recover_chapters_from_extractions()

# Mount the current directory for serving static frontend files
# This should be done AFTER all API routes are defined to avoid conflicts
# We'll add this at the end of the file before starting the server

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

def extract_images_from_cropped_pdf(pdf_path: str, section_title: str) -> Dict[str, any]:
    """Extract images from cropped PDF using docling and return metadata."""
    print(f"\n🔄 Starting image extraction for: {section_title}")
    print(f"📁 PDF path: {pdf_path}")
    
    if extract_figures_with_docling is None:
        print("❌ Docling extractor not available")
        return {
            "success": False,
            "error": "Docling extractor not available",
            "images": [],
            "html_path": None,
            "extraction_dir": None
        }
    
    try:
        # Create a safe filename for the section
        safe_title = "".join(c for c in section_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]
        
        # Create extraction directory name within extracted-data
        extraction_dir_name = f"{safe_title}_docling_extracted"
        extraction_dir = Path("extracted-data") / extraction_dir_name
        
        print(f"📂 Extraction directory: {extraction_dir}")
        
        # Extract using docling (pass the full path)
        print("🚀 Running docling extraction...")
        success = extract_figures_with_docling(pdf_path, str(extraction_dir))
        
        if not success:
            print("❌ Docling extraction failed")
            return {
                "success": False,
                "error": "Docling extraction failed",
                "images": [],
                "html_path": None,
                "extraction_dir": None
            }
        
        # Scan extraction directory for results
        if not extraction_dir.exists():
            print(f"❌ Extraction directory not found: {extraction_dir}")
            return {
                "success": False,
                "error": "Extraction directory not found",
                "images": [],
                "html_path": None,
                "extraction_dir": None
            }
        
        print(f"✅ Extraction directory created: {extraction_dir}")
        
        # Find images
        image_files = []
        for img_file in extraction_dir.glob("*.png"):
            image_files.append({
                "filename": img_file.name,
                "path": str(img_file),
                "url": f"/extracted-data/{extraction_dir_name}/{img_file.name}",
                "size": img_file.stat().st_size
            })
        
        print(f"🖼️  Found {len(image_files)} images")
        if image_files:
            print(f"📷 Sample image URL: {image_files[0]['url']}")
        
        # Find HTML files
        html_files = list(extraction_dir.glob("*.html"))
        html_path = None
        html_url = None
        
        if html_files:
            # Prefer -with-image-refs.html if available
            html_with_refs = [f for f in html_files if 'with-image-refs' in f.name]
            if html_with_refs:
                html_file = html_with_refs[0]
                html_path = str(html_file)
                html_url = f"/extracted-data/{extraction_dir_name}/{html_file.name}"
                print(f"📄 Found HTML with refs: {html_file.name}")
                print(f"🔗 HTML URL: {html_url}")
            else:
                html_file = html_files[0]
                html_path = str(html_file)
                html_url = f"/extracted-data/{extraction_dir_name}/{html_file.name}"
                print(f"📄 Found HTML: {html_file.name}")
                print(f"🔗 HTML URL: {html_url}")
        else:
            print("❌ No HTML files found")
        
        # Find markdown files
        markdown_files = []
        for md_file in extraction_dir.glob("*.md"):
            markdown_files.append({
                "filename": md_file.name,
                "path": str(md_file),
                "url": f"/extracted-data/{extraction_dir_name}/{md_file.name}"
            })
        
        print(f"📝 Found {len(markdown_files)} markdown files")
        
        # Mount the new extraction directory - try both mount points
        try:
            # Mount individual folder for legacy /extracts/ URLs
            mount_path_extracts = f"/extracts/{extraction_dir_name}"
            app.mount(mount_path_extracts, StaticFiles(directory=str(extraction_dir)), name=f"extract_{extraction_dir_name}")
            print(f"🔗 Mounted extraction folder (extracts): {mount_path_extracts} -> {extraction_dir}")
        except Exception as e:
            print(f"⚠️  Warning: Could not mount extraction folder (extracts): {e}")
        
        result = {
            "success": True,
            "extraction_dir": extraction_dir_name,
            "extraction_path": str(extraction_dir),
            "images": image_files,
            "html_path": html_path,
            "html_url": html_url,
            "html_full_url": f"http://localhost:8001{html_url}" if html_url else None,
            "html_available": html_url is not None,
            "markdown_files": markdown_files,
            "total_images": len(image_files),
            "total_files": len(list(extraction_dir.iterdir()))
        }
        
        print("=" * 60)
        print("🎉 EXTRACTION RESULT:")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        return {
            "success": False,
            "error": f"Error during extraction: {str(e)}",
            "images": [],
            "html_path": None,
            "extraction_dir": None
        }

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
    section_title: str = Form(...),
    skip_extraction: bool = Form(False)
):
    """Crop a section of the PDF, optionally extract images using docling, and return metadata."""
    if file_id not in file_store:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_info = file_store[file_id]
        input_path = file_info['file_path']
        
        # Generate output filename for cropped PDF with timestamp for uniqueness
        safe_title = "".join(c for c in section_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        
        # Create unique chapter ID first
        chapter_id = str(uuid.uuid4())
        
        # Create cropped PDF filename with chapter ID for uniqueness
        cropped_pdf_filename = f"{safe_title}_pages_{start_page}-{end_page}_{chapter_id[:8]}.pdf"
        cropped_pdf_path = os.path.join(CROPPED_PDFS_DIR, cropped_pdf_filename)
        
        print(f"📄 Creating cropped PDF: {cropped_pdf_path}")
        
        # Crop PDF and store in dedicated directory
        crop_pdf_pages(input_path, start_page, end_page, cropped_pdf_path)
        
        print(f"✅ Cropped PDF created successfully: {cropped_pdf_filename}")
        
        # Initialize extraction result
        extraction_result = {
            "success": False,
            "skipped": True,
            "message": "Extraction skipped by user request"
        }
        
        # Extract images using docling only if not skipped
        if not skip_extraction:
            print(f"🚀 Starting docling extraction for: {section_title}")
            extraction_result = extract_images_from_cropped_pdf(cropped_pdf_path, section_title)
        else:
            print(f"⏭️ Skipping docling extraction for: {section_title}")
        
        # Create chapter mapping entry with proper paths
        chapter_extractions[chapter_id] = {
            "chapter_id": chapter_id,
            "section_title": section_title,
            "start_page": start_page,
            "end_page": end_page,
            "cropped_pdf_path": cropped_pdf_path,  # Full path to the stored PDF
            "cropped_pdf_filename": cropped_pdf_filename,  # Just the filename
            "extraction_result": extraction_result,
            "created_at": str(uuid.uuid4()),  # In production, use actual timestamp
            "extraction_skipped": skip_extraction
        }
        
        # Create response object with proper download URLs
        response_data = {
            "success": True,
            "chapter_id": chapter_id,
            "section_title": section_title,
            "page_range": f"{start_page}-{end_page}",
            "cropped_pdf": {
                "filename": cropped_pdf_filename,
                "download_url": f"/download-cropped/{chapter_id}",
                "download_full_url": f"http://localhost:8001/download-cropped/{chapter_id}",
                "file_path": cropped_pdf_path,  # Include full path for debugging
                "file_exists": os.path.exists(cropped_pdf_path)  # Verify file exists
            },
            "extraction": extraction_result,
            "extraction_skipped": skip_extraction,
            "browse_url": f"/browse-chapter/{chapter_id}" if not skip_extraction and extraction_result["success"] else None
        }
        
        # Log the response object
        print("=" * 80)
        print("CROP SECTION RESPONSE OBJECT:")
        print("=" * 80)
        print(json.dumps(response_data, indent=2, default=str))
        print("=" * 80)
        
        # Return comprehensive response
        return JSONResponse(content=response_data)
        
    except Exception as e:
        # Clean up cropped file if it was created but extraction failed
        if 'cropped_pdf_path' in locals() and os.path.exists(cropped_pdf_path):
            try:
                os.unlink(cropped_pdf_path)
                print(f"🗑️ Cleaned up failed cropped PDF: {cropped_pdf_path}")
            except:
                pass
        
        error_response = {
            "success": False,
            "error": f"Error processing section: {str(e)}",
            "chapter_id": None,
            "section_title": section_title,
            "page_range": f"{start_page}-{end_page}",
            "extraction": {
                "success": False,
                "error": str(e)
            },
            "extraction_skipped": skip_extraction if 'skip_extraction' in locals() else False
        }
        
        # Log the error response
        print("=" * 80)
        print("CROP SECTION ERROR RESPONSE:")
        print("=" * 80)
        print(json.dumps(error_response, indent=2, default=str))
        print("=" * 80)
        
        raise HTTPException(status_code=500, detail=f"Error processing section: {str(e)}")

@app.get("/download-cropped/{chapter_id}")
async def download_cropped_pdf(chapter_id: str):
    """Download the cropped PDF for a specific chapter."""
    print(f"🔍 Download request for chapter_id: {chapter_id}")
    print(f"📊 Available chapters: {list(chapter_extractions.keys())}")
    print(f"📁 Total chapters in memory: {len(chapter_extractions)}")
    
    if chapter_id not in chapter_extractions:
        print(f"❌ Chapter {chapter_id} not found in memory")
        raise HTTPException(status_code=404, detail=f"Chapter not found. Available chapters: {len(chapter_extractions)}")
    
    chapter_info = chapter_extractions[chapter_id]
    cropped_pdf_path = chapter_info["cropped_pdf_path"]
    
    print(f"📄 Looking for PDF at: {cropped_pdf_path}")
    
    if not os.path.exists(cropped_pdf_path):
        print(f"❌ File not found at path: {cropped_pdf_path}")
        # List files in the directory to help debug
        upload_dir_files = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []
        print(f"📁 Files in upload directory: {upload_dir_files}")
        raise HTTPException(status_code=404, detail=f"Cropped PDF file not found at: {cropped_pdf_path}")
    
    print(f"✅ Found PDF file, serving: {chapter_info['cropped_pdf_filename']}")
    
    return FileResponse(
        path=cropped_pdf_path,
        filename=chapter_info["cropped_pdf_filename"],
        media_type='application/pdf'
    )

@app.get("/cropped-pdf/{filename}")
async def serve_cropped_pdf_direct(filename: str):
    """Direct endpoint to serve cropped PDF files from the cropped-pdfs directory."""
    try:
        pdf_path = Path(CROPPED_PDFS_DIR) / filename
        
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {filename}")
        
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        return FileResponse(
            path=str(pdf_path),
            filename=filename,
            media_type='application/pdf'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PDF: {str(e)}")

@app.get("/debug/chapters")
async def debug_chapters():
    """Debug endpoint to check current chapter extractions state."""
    upload_dir_files = []
    if os.path.exists(UPLOAD_DIR):
        upload_dir_files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
    
    chapter_details = {}
    for chapter_id, chapter_info in chapter_extractions.items():
        pdf_path = chapter_info.get("cropped_pdf_path", "")
        chapter_details[chapter_id] = {
            "section_title": chapter_info.get("section_title", ""),
            "cropped_pdf_path": pdf_path,
            "file_exists": os.path.exists(pdf_path) if pdf_path else False,
            "cropped_pdf_filename": chapter_info.get("cropped_pdf_filename", "")
        }
    
    return JSONResponse(content={
        "total_chapters": len(chapter_extractions),
        "chapter_ids": list(chapter_extractions.keys()),
        "chapter_details": chapter_details,
        "upload_dir": UPLOAD_DIR,
        "upload_dir_exists": os.path.exists(UPLOAD_DIR),
        "upload_dir_files": upload_dir_files
    })

@app.get("/browse-chapter/{chapter_id}")
async def browse_chapter(chapter_id: str):
    """Get detailed information about a chapter's extracted content."""
    if chapter_id not in chapter_extractions:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    chapter_info = chapter_extractions[chapter_id]
    return JSONResponse(content=chapter_info)

@app.get("/list-chapters")
async def list_chapters():
    """List all cropped chapters and their extraction status."""
    chapters_list = []
    
    for chapter_id, chapter_info in chapter_extractions.items():
        extraction_result = chapter_info["extraction_result"]
        
        chapters_list.append({
            "chapter_id": chapter_id,
            "section_title": chapter_info["section_title"],
            "page_range": f"{chapter_info['start_page']}-{chapter_info['end_page']}",
            "extraction_success": extraction_result.get("success", False),
            "total_images": extraction_result.get("total_images", 0),
            "html_available": extraction_result.get("html_available", False) or extraction_result.get("html_url") is not None,
            "browse_url": f"/browse-chapter/{chapter_id}",
            "download_url": f"/download-cropped/{chapter_id}",
            "download_full_url": f"http://localhost:8001/download-cropped/{chapter_id}",
            "html_url": extraction_result.get("html_url"),
            "html_full_url": extraction_result.get("html_full_url"),
            "extraction_dir": extraction_result.get("extraction_dir"),
            "extraction_result": extraction_result  # Include full extraction result for frontend access
        })
    
    return JSONResponse(content={
        "chapters": chapters_list,
        "total_chapters": len(chapters_list)
    })

@app.delete("/delete-chapter/{chapter_id}")
async def delete_chapter(chapter_id: str):
    """Delete a chapter and its associated files."""
    if chapter_id not in chapter_extractions:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    chapter_info = chapter_extractions[chapter_id]
    
    try:
        # Delete cropped PDF
        if os.path.exists(chapter_info["cropped_pdf_path"]):
            os.unlink(chapter_info["cropped_pdf_path"])
            print(f"🗑️ Deleted cropped PDF: {chapter_info['cropped_pdf_path']}")
        
        # Delete extraction directory if it exists
        extraction_result = chapter_info["extraction_result"]
        if extraction_result.get("success") and extraction_result.get("extraction_path"):
            extraction_path = extraction_result["extraction_path"]
            if os.path.exists(extraction_path):
                shutil.rmtree(extraction_path)
                print(f"🗑️ Deleted extraction directory: {extraction_path}")
        elif extraction_result.get("extraction_dir"):
            # Try both possible locations
            extraction_dir_name = extraction_result["extraction_dir"]
            
            # Check in extracted-data first
            extracted_data_path = Path("extracted-data") / extraction_dir_name
            if extracted_data_path.exists():
                shutil.rmtree(extracted_data_path)
                print(f"🗑️ Deleted extraction directory: {extracted_data_path}")
            
            # Check in root directory (legacy)
            root_path = Path(extraction_dir_name)
            if root_path.exists():
                shutil.rmtree(root_path)
                print(f"🗑️ Deleted legacy extraction directory: {root_path}")
        
        # Remove from memory
        del chapter_extractions[chapter_id]
        print(f"🗑️ Removed chapter {chapter_id} from memory")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Chapter {chapter_id} deleted successfully"
        })
        
    except Exception as e:
        print(f"❌ Error deleting chapter {chapter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting chapter: {str(e)}")

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
    """Serve the main application homepage."""
    try:
        return FileResponse("index.html", media_type="text/html")
    except Exception as e:
        raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/api")
async def api_info():
    """API information endpoint."""
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
            "active_sessions": len(file_store),
            "active_chapters": len(chapter_extractions)
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
        extract_folders = []
        
        # Check extracted-data directory first
        extracted_data_dir = Path("extracted-data")
        if extracted_data_dir.exists():
            for folder in extracted_data_dir.glob("*_extracted"):
                if folder.is_dir():
                    html_files = list(folder.glob("*.html"))
                    if html_files:
                        html_file_info = []
                        for html_file in html_files:
                            html_file_info.append({
                                "filename": html_file.name,
                                "view_url": f"/extracted-data/{folder.name}/{html_file.name}",
                                "serve_url": f"/serve-docling-html/{folder.name}/{html_file.name}",
                                "static_url": f"/extracted-data/{folder.name}/{html_file.name}"
                            })
                        
                        # Find corresponding chapter for cropped PDF info
                        chapter_info = None
                        cropped_pdf_info = None
                        
                        for chapter_id, chapter_data in chapter_extractions.items():
                            extraction_result = chapter_data.get("extraction_result", {})
                            if extraction_result.get("extraction_dir") == folder.name:
                                chapter_info = chapter_data
                                cropped_pdf_info = {
                                    "chapter_id": chapter_id,
                                    "filename": chapter_data.get("cropped_pdf_filename"),
                                    "download_url": f"/download-cropped/{chapter_id}",
                                    "section_title": chapter_data.get("section_title", ""),
                                    "page_range": f"{chapter_data.get('start_page', '')}-{chapter_data.get('end_page', '')}"
                                }
                                break
                        
                        folder_info = {
                            "folder_name": folder.name,
                            "folder_path": str(folder),
                            "mount_path": f"/extracts/{folder.name}",
                            "html_files": html_file_info,
                            "image_count": len(list(folder.glob("*.png"))),
                            "markdown_files": [f.name for f in folder.glob("*.md")],
                            "all_assets": [f.name for f in folder.iterdir() if f.is_file()],
                            "location": "extracted-data",
                            "cropped_pdf": cropped_pdf_info
                        }
                        extract_folders.append(folder_info)
        
        # Also check current directory for legacy extractions
        current_dir = Path(".")
        for folder in current_dir.glob("*_extracted"):
            if folder.is_dir() and not str(folder).startswith("extracted-data"):
                html_files = list(folder.glob("*.html"))
                if html_files:
                    html_file_info = []
                    for html_file in html_files:
                        html_file_info.append({
                            "filename": html_file.name,
                            "view_url": f"/extracts/{folder.name}/{html_file.name}",
                            "serve_url": f"/serve-docling-html/{folder.name}/{html_file.name}",
                            "static_url": f"/extracts/{folder.name}/{html_file.name}"
                        })
                    
                    # Find corresponding chapter for cropped PDF info
                    chapter_info = None
                    cropped_pdf_info = None
                    
                    for chapter_id, chapter_data in chapter_extractions.items():
                        extraction_result = chapter_data.get("extraction_result", {})
                        if extraction_result.get("extraction_dir") == folder.name:
                            chapter_info = chapter_data
                            cropped_pdf_info = {
                                "chapter_id": chapter_id,
                                "filename": chapter_data.get("cropped_pdf_filename"),
                                "download_url": f"/download-cropped/{chapter_id}",
                                "section_title": chapter_data.get("section_title", ""),
                                "page_range": f"{chapter_data.get('start_page', '')}-{chapter_data.get('end_page', '')}"
                            }
                            break
                    
                    folder_info = {
                        "folder_name": folder.name,
                        "folder_path": str(folder),
                        "mount_path": f"/extracts/{folder.name}",
                        "html_files": html_file_info,
                        "image_count": len(list(folder.glob("*.png"))),
                        "markdown_files": [f.name for f in folder.glob("*.md")],
                        "all_assets": [f.name for f in folder.iterdir() if f.is_file()],
                        "location": "root",
                        "cropped_pdf": cropped_pdf_info
                    }
                    extract_folders.append(folder_info)
        
        return JSONResponse(content={
            "extract_folders": extract_folders,
            "total_folders": len(extract_folders),
            "extracted_data_dir": str(extracted_data_dir) if extracted_data_dir.exists() else None,
            "instructions": {
                "view_html": "Use view_url to see HTML with proper image loading",
                "serve_html": "Use serve_url for direct HTML serving",
                "static_access": "Use static_url for direct file access",
                "download_pdf": "Use cropped_pdf.download_url to download the original cropped PDF",
                "remount": "POST to /remount-extractions to detect new folders"
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing extracts: {str(e)}")

@app.get("/list-extraction-files/{folder_name}")
async def list_extraction_files(folder_name: str):
    """List all files in a specific extraction folder."""
    try:
        # Try both possible locations
        folder_paths = [
            Path("extracted-data") / folder_name,
            Path(folder_name)
        ]
        
        folder_path = None
        for path in folder_paths:
            if path.exists() and path.is_dir():
                folder_path = path
                break
        
        if not folder_path:
            raise HTTPException(status_code=404, detail=f"Extraction folder '{folder_name}' not found")
        
        files_info = {
            "folder_name": folder_name,
            "folder_path": str(folder_path),
            "location": "extracted-data" if "extracted-data" in str(folder_path) else "root",
            "images": [],
            "html_files": [],
            "markdown_files": [],
            "other_files": []
        }
        
        # Scan all files in the directory
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                file_info = {
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix.lower()
                }
                
                # Generate URL based on location
                if files_info["location"] == "extracted-data":
                    file_url = f"/extracted-data/{folder_name}/{file_path.name}"
                else:
                    file_url = f"/extracts/{folder_name}/{file_path.name}"
                
                file_info["url"] = file_url
                file_info["full_url"] = f"http://localhost:8001{file_url}"
                
                # Categorize files
                if file_info["extension"] in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
                    files_info["images"].append(file_info)
                elif file_info["extension"] == '.html':
                    files_info["html_files"].append(file_info)
                elif file_info["extension"] == '.md':
                    files_info["markdown_files"].append(file_info)
                else:
                    files_info["other_files"].append(file_info)
        
        # Sort images by filename for consistent ordering
        files_info["images"].sort(key=lambda x: x["filename"])
        
        return JSONResponse(content=files_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing extraction files: {str(e)}")

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

@app.get("/debug/mounts")
async def debug_mounts():
    """Debug endpoint to check mounted paths and static file serving."""
    try:
        mount_info = []
        
        # Get FastAPI app routes to see what's mounted
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'name'):
                if 'static' in str(route.name).lower() or 'extract' in str(route.name).lower():
                    mount_info.append({
                        "path": route.path,
                        "name": route.name,
                        "type": str(type(route))
                    })
        
        # Check if extracted-data directory exists and list contents
        extracted_data_dir = Path("extracted-data")
        extracted_data_info = {
            "exists": extracted_data_dir.exists(),
            "path": str(extracted_data_dir.absolute()),
            "contents": []
        }
        
        if extracted_data_dir.exists():
            for item in extracted_data_dir.iterdir():
                if item.is_dir():
                    image_count = len(list(item.glob("*.png")))
                    html_count = len(list(item.glob("*.html")))
                    extracted_data_info["contents"].append({
                        "name": item.name,
                        "type": "directory",
                        "images": image_count,
                        "html_files": html_count,
                        "path": str(item)
                    })
        
        return JSONResponse(content={
            "mounted_paths": mount_info,
            "extracted_data": extracted_data_info,
            "active_chapters": len(chapter_extractions),
            "total_mounts": len(mount_info)
        })
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.get("/test-image/{extraction_dir}/{filename}")
async def test_image_serving(extraction_dir: str, filename: str):
    """Test endpoint to verify image serving works."""
    try:
        # Try different possible paths
        paths_to_try = [
            Path("extracted-data") / extraction_dir / filename,
            Path(extraction_dir) / filename,
            Path(".") / extraction_dir / filename
        ]
        
        for path in paths_to_try:
            if path.exists():
                return FileResponse(
                    path=str(path),
                    media_type="image/png",
                    filename=filename
                )
        
        raise HTTPException(status_code=404, detail=f"Image not found: {filename} in {extraction_dir}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")

@app.post("/extract-table-json/")
async def extract_table_json(
    file: UploadFile = File(...)
):
    """
    Extract tables from uploaded file and convert to JSON using Gemini API.
    Returns clean JSON data structure.
    """
    try:
        import time
        import pandas as pd
        from docling.document_converter import DocumentConverter
        from google import genai
        
        start_time = time.time()
        
        # Create directories for processing
        temp_output_dir = Path("temp_processing")
        temp_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file temporarily
        temp_file_path = temp_output_dir / f"temp_{int(time.time())}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Processing file with Docling: {file.filename}")
        
        # Initialize Docling document converter
        doc_converter = DocumentConverter()
        
        # Convert the document
        conv_res = doc_converter.convert(temp_file_path)
        
        # Extract tables to markdown
        tables_markdown = []
        for table_ix, table in enumerate(conv_res.document.tables):
            table_df: pd.DataFrame = table.export_to_dataframe()
            table_markdown = table_df.to_markdown(index=False)
            tables_markdown.append({
                "table_number": table_ix + 1,
                "markdown": table_markdown,
                "rows": len(table_df),
                "columns": len(table_df.columns) if not table_df.empty else 0
            })
        
        if not tables_markdown:
            # Clean up
            temp_file_path.unlink()
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "No tables found in the uploaded file"
                }
            )
        
        # Get API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "GEMINI_API_KEY not found in environment variables. Please add it to your .env file."
                }
            )
        
        # Initialize Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        # Prepare prompt for Gemini
        combined_markdown = "\n\n".join([t["markdown"] for t in tables_markdown])
        
        prompt = f"""Convert the following markdown table(s) to this specific JSON format:
{{
  "topics": [
    {{
      "topic": "T1", 
      "competencies": [
        {{"code": "GM6.22", "description": "Demonstrate a non-judgmental attitude...", "column3": "A", "column4": "SH", "column5": "Y", "column6": "Bedside clinic..."}},
        {{"code": "GM6.23", "description": "Another competency...", "column3": "B", "column4": "SH", "column5": "N", "column6": "Lab session..."}}
      ]
    }}
  ]
}}

Instructions:
- Group rows by topic (first column or most appropriate grouping)
- Each competency should be an object containing ALL columns from that row
- Use column headers as keys, or if no headers use: "code", "description", "column3", "column4", etc.
- Preserve all data from each row - nothing should be lost
- Use the actual text content from the table
- Return only the JSON, no explanations or markdown formatting

Markdown tables:
{combined_markdown}

Return only the JSON in the specified format with full row objects."""

        print("Sending to Gemini API for JSON conversion...")
        
        # Send to Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        # Parse the response
        json_response = response.text.strip()
        
        # Try to clean up any potential markdown formatting
        if json_response.startswith("```json"):
            json_response = json_response.replace("```json", "").replace("```", "").strip()
        elif json_response.startswith("```"):
            json_response = json_response.replace("```", "").strip()
        
        # Validate it's valid JSON
        import json
        try:
            parsed_json = json.loads(json_response)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {json_response}")
            # Fallback: return structured data in the requested format with full row objects
            topics = []
            for t, (_, table) in zip(tables_markdown, enumerate(conv_res.document.tables)):
                table_df = table.export_to_dataframe()
                if not table_df.empty:
                    # Group all rows under a single topic or create multiple topics
                    competencies = []
                    
                    # Get column names or create default ones
                    column_names = list(table_df.columns) if table_df.columns.tolist() != list(range(len(table_df.columns))) else [f"column{i+1}" for i in range(len(table_df.columns))]
                    
                    # Convert each row to a competency object
                    for index, row in table_df.iterrows():
                        row_obj = {}
                        for col_idx, col_name in enumerate(column_names):
                            if col_idx < len(row):
                                value = row.iloc[col_idx]
                                row_obj[col_name] = str(value) if not pd.isna(value) else ""
                            else:
                                row_obj[col_name] = ""
                        
                        # Only add non-empty rows
                        if any(v.strip() for v in row_obj.values() if v):
                            competencies.append(row_obj)
                    
                    # Create a topic entry
                    if competencies:
                        # Use first row's first column as topic if available, otherwise generic name
                        topic_name = competencies[0].get(column_names[0], f"Table_{t+1}") if competencies else f"Table_{t+1}"
                        topics.append({
                            "topic": topic_name,
                            "competencies": competencies
                        })
            
            parsed_json = {"topics": topics}
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        processing_time = time.time() - start_time
        
        print(f"Processing completed in {processing_time:.2f}s")
        print(f"Found {len(tables_markdown)} table(s)")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "tables_found": len(tables_markdown),
            "processing_time": f"{processing_time:.2f}s",
            "json_data": parsed_json
        })
        
    except ImportError as e:
        print(f"Import error: {e}")
        if "google" in str(e):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Google GenAI SDK not installed. Please install with: pip install google-genai"
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Required dependencies not installed. Please install with: pip install docling docling-core pandas google-genai"
                }
            )
    except Exception as e:
        print(f"Error processing table: {e}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error processing table: {str(e)}"
            }
        )

@app.post("/process-table/")
async def process_table(
    file: UploadFile = File(...),
    generate_csv: bool = Form(True),
    generate_html: bool = Form(True),
    generate_markdown: bool = Form(True)
):
    """
    Process a table image using Docling to extract tables and generate various formats.
    Based on the docling table export example.
    """
    try:
        import time
        import pandas as pd
        from docling.document_converter import DocumentConverter
        
        start_time = time.time()
        
        # Create directories for table processing
        table_output_dir = Path("extracted-data") / "table-extractions"
        table_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file temporarily
        temp_file_path = table_output_dir / f"temp_{int(time.time())}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Processing table image: {file.filename}")
        print(f"Temporary file saved to: {temp_file_path}")
        
        # Initialize Docling document converter
        doc_converter = DocumentConverter()
        
        # Convert the document
        conv_res = doc_converter.convert(temp_file_path)
        
        # Create unique output directory for this processing
        doc_filename = temp_file_path.stem
        output_dir = table_output_dir / f"{doc_filename}_{int(time.time())}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "success": True,
            "filename": file.filename,
            "tables_found": len(conv_res.document.tables),
            "processing_time": f"{time.time() - start_time:.2f}s",
            "output_dir": str(output_dir),
            "files": [],
            "tables": [],
            "markdown_content": ""
        }
        
        # Process each table found in the document
        all_markdown_tables = []
        
        for table_ix, table in enumerate(conv_res.document.tables):
            table_num = table_ix + 1
            print(f"Processing table {table_num}")
            
            # Export table to dataframe
            table_df: pd.DataFrame = table.export_to_dataframe()
            
            # Generate markdown for this table
            table_markdown = table_df.to_markdown(index=False)
            all_markdown_tables.append(f"## Table {table_num}\n\n{table_markdown}\n")
            
            table_info = {
                "table_number": table_num,
                "rows": len(table_df),
                "columns": len(table_df.columns) if not table_df.empty else 0,
                "markdown": table_markdown
            }
            
            # Generate CSV if requested
            if generate_csv:
                csv_filename = f"{doc_filename}-table-{table_num}.csv"
                csv_path = output_dir / csv_filename
                table_df.to_csv(csv_path, index=False)
                
                # Add to results
                results["files"].append({
                    "filename": csv_filename,
                    "type": "csv",
                    "url": f"/extracted-data/table-extractions/{output_dir.name}/{csv_filename}",
                    "size": csv_path.stat().st_size
                })
                table_info["csv"] = table_df.to_csv(index=False)
            
            # Generate HTML if requested
            if generate_html:
                html_filename = f"{doc_filename}-table-{table_num}.html"
                html_path = output_dir / html_filename
                
                # Generate HTML table
                html_content = table.export_to_html(doc=conv_res.document)
                
                # Create a complete HTML document
                full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Table {table_num} - {file.filename}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-800 mb-4">Table {table_num}</h1>
        <p class="text-gray-600 mb-6">Extracted from: {file.filename}</p>
        <div class="bg-white rounded-lg shadow-md p-6 overflow-x-auto">
            {html_content}
        </div>
    </div>
</body>
</html>"""
                
                with html_path.open("w", encoding="utf-8") as fp:
                    fp.write(full_html)
                
                results["files"].append({
                    "filename": html_filename,
                    "type": "html",
                    "url": f"/extracted-data/table-extractions/{output_dir.name}/{html_filename}",
                    "size": html_path.stat().st_size
                })
                table_info["html"] = html_content
            
            results["tables"].append(table_info)
        
        # Generate combined markdown file if requested
        if generate_markdown and all_markdown_tables:
            markdown_filename = f"{doc_filename}-tables.md"
            markdown_path = output_dir / markdown_filename
            
            combined_markdown = f"""# Tables Extracted from {file.filename}

*Generated using Docling on {time.strftime('%Y-%m-%d %H:%M:%S')}*

---

{chr(10).join(all_markdown_tables)}

---

**Processing Summary:**
- Tables found: {len(conv_res.document.tables)}
- Processing time: {results["processing_time"]}
- Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with markdown_path.open("w", encoding="utf-8") as fp:
                fp.write(combined_markdown)
            
            results["files"].append({
                "filename": markdown_filename,
                "type": "markdown",
                "url": f"/extracted-data/table-extractions/{output_dir.name}/{markdown_filename}",
                "size": markdown_path.stat().st_size
            })
            
            results["markdown_content"] = combined_markdown
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        print(f"Table processing completed in {results['processing_time']}")
        print(f"Found {results['tables_found']} tables")
        print(f"Generated {len(results['files'])} files")
        
        return JSONResponse(content=results)
        
    except ImportError as e:
        print(f"Import error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Docling or required dependencies not installed. Please install with: pip install docling docling-core pandas"
            }
        )
    except Exception as e:
        print(f"Error processing table: {e}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error processing table: {str(e)}"
            }
        )

# Mount static files for frontend (HTML, JS, CSS) - this must be last to avoid route conflicts
try:
    app.mount("/", StaticFiles(directory=".", html=True), name="frontend")
    print("Mounted frontend static files: / -> current directory")
except Exception as e:
    print(f"Warning: Could not mount frontend static files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 