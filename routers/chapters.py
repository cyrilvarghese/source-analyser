"""
Chapters router for PDF cropping and chapter management
"""

import os
import json
import uuid
import shutil
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from utils import (
    UPLOAD_DIR, 
    CROPPED_PDFS_DIR, 
    file_store, 
    chapter_extractions, 
    crop_pdf_pages, 
    extract_images_from_cropped_pdf
)

router = APIRouter(prefix="/api/chapters", tags=["chapters"])

@router.post("/crop-section/")
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
                "download_url": f"/api/chapters/download/{chapter_id}",
                "download_full_url": f"http://localhost:8001/api/chapters/download/{chapter_id}",
                "file_path": cropped_pdf_path,  # Include full path for debugging
                "file_exists": os.path.exists(cropped_pdf_path)  # Verify file exists
            },
            "extraction": extraction_result,
            "extraction_skipped": skip_extraction,
            "browse_url": f"/api/chapters/browse/{chapter_id}" if not skip_extraction and extraction_result["success"] else None
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

@router.get("/download/{chapter_id}")
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

@router.get("/browse/{chapter_id}")
async def browse_chapter(chapter_id: str):
    """Get detailed information about a chapter's extracted content."""
    if chapter_id not in chapter_extractions:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    chapter_info = chapter_extractions[chapter_id]
    return JSONResponse(content=chapter_info)

@router.get("/list/")
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
            "browse_url": f"/api/chapters/browse/{chapter_id}",
            "download_url": f"/api/chapters/download/{chapter_id}",
            "download_full_url": f"http://localhost:8001/api/chapters/download/{chapter_id}",
            "html_url": extraction_result.get("html_url"),
            "html_full_url": extraction_result.get("html_full_url"),
            "extraction_dir": extraction_result.get("extraction_dir"),
            "extraction_result": extraction_result  # Include full extraction result for frontend access
        })
    
    return JSONResponse(content={
        "chapters": chapters_list,
        "total_chapters": len(chapters_list)
    })

@router.delete("/delete/{chapter_id}")
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
            from pathlib import Path
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

@router.get("/debug/")
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