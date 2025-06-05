"""
Debug router for debugging and monitoring functions
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from utils import chapter_extractions

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/mounts/")
async def debug_mounts():
    """Debug endpoint to check mounted paths and static file serving."""
    try:
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
            "extracted_data": extracted_data_info,
            "active_chapters": len(chapter_extractions),
            "debug_info": {
                "service": "File Cropper API",
                "routers": ["upload", "tables", "chapters", "extractions", "admin", "debug"]
            }
        })
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@router.get("/system-info/")
async def get_system_info():
    """Get system information for debugging."""
    import sys
    import platform
    
    return JSONResponse(content={
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "working_directory": str(Path.cwd()),
        "chapters_loaded": len(chapter_extractions)
    }) 