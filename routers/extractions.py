"""
Extractions router for static file serving and extraction management
"""

import re
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from utils import CROPPED_PDFS_DIR, chapter_extractions

router = APIRouter(prefix="/api/extractions", tags=["extractions"])

@router.get("/serve-html/{extract_folder}/{html_filename}")
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

@router.get("/view/{extract_folder}/{html_filename}")
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
        return RedirectResponse(url=mount_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error viewing file: {str(e)}")

@router.get("/list-docling/")
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
                                "serve_url": f"/api/extractions/serve-html/{folder.name}/{html_file.name}",
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
                                    "download_url": f"/api/chapters/download/{chapter_id}",
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
                            "serve_url": f"/api/extractions/serve-html/{folder.name}/{html_file.name}",
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
                                "download_url": f"/api/chapters/download/{chapter_id}",
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
                "remount": "POST to /api/extractions/remount to detect new folders"
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing extracts: {str(e)}")

@router.get("/list-files/{folder_name}")
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

@router.get("/info/{folder_name}")
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

@router.get("/test-image/{extraction_dir}/{filename}")
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

@router.get("/serve-pdf/{filename}")
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