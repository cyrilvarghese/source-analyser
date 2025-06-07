"""
Master Cases router for case library management
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import aiohttp
import aiofiles
router = APIRouter(prefix="/api/master-cases", tags=["master-cases"])

# Pydantic models
class MasterCaseInfo(BaseModel):
    id: str
    title: str
    topic: str
    file_path: str
    file_size: int
    created_at: str
    status: str  # 'generated', 'failed', 'pending'
    disease_name: Optional[str] = None

class MasterCaseStats(BaseModel):
    total_topics: int
    total_cases: int
    generated_cases: int
    failed_cases: int
    pending_cases: int

class MasterCaseListResponse(BaseModel):
    success: bool
    stats: MasterCaseStats
    cases: List[MasterCaseInfo]  # Flat array of all cases
    topics: Dict[str, List[MasterCaseInfo]]  # Grouped by topic (for reference)
    message: Optional[str] = None

def sanitize_topic_name(topic_name: str) -> str:
    """Sanitize topic name for safe folder/file operations"""
    if not topic_name:
        return ""
    
    # Replace spaces and special characters with underscores
    sanitized = topic_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    # Remove any remaining special characters except underscores and hyphens
    import re
    sanitized = re.sub(r'[^\w\-_]', '', sanitized)
    return sanitized.lower()

def get_case_info_from_file(file_path: Path, topic: str) -> MasterCaseInfo:
    """Extract case information from a markdown file"""
    try:
        # Get file stats
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
        file_size = stat.st_size
        
        # Extract title from filename (remove .md extension)
        title = file_path.stem.replace("_", " ")
        
        # Try to extract disease name from the file content
        disease_name = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for the first header that might contain the disease name
                lines = content.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if line.startswith('## **Master Clinical Case:') or line.startswith('# Master Clinical Case:'):
                        disease_name = line.split(':')[-1].strip().replace('**', '').replace('#', '').strip()
                        break
                if not disease_name and lines:
                    # Fallback to first non-empty line
                    for line in lines[:5]:
                        if line.strip() and not line.startswith('#'):
                            disease_name = line.strip()[:50] + "..." if len(line.strip()) > 50 else line.strip()
                            break
        except Exception as e:
            print(f"Warning: Could not read file content for {file_path}: {e}")
        
        return MasterCaseInfo(
            id=file_path.stem,  # Just use filename without topic prefix
            title=title,
            topic=topic,
            file_path=str(file_path),
            file_size=file_size,
            created_at=created_at,
            status="generated",  # If file exists, it's generated
            disease_name=disease_name or title
        )
    except Exception as e:
        # If there's an error reading the file, mark as failed
        return MasterCaseInfo(
            id=file_path.stem,  # Just use filename without topic prefix
            title=file_path.stem.replace("_", " "),
            topic=topic,
            file_path=str(file_path),
            file_size=0,
            created_at=datetime.now().isoformat(),
            status="failed",
            disease_name=file_path.stem.replace("_", " ")
        )

@router.get("/list/", response_model=MasterCaseListResponse)
async def list_master_cases():
    """
    Get a list of all master cases organized by topic
    """
    try:
        case_docs_dir = Path("cache/case_docs")
        
        if not case_docs_dir.exists():
            return MasterCaseListResponse(
                success=True,
                stats=MasterCaseStats(
                    total_topics=0,
                    total_cases=0,
                    generated_cases=0,
                    failed_cases=0,
                    pending_cases=0
                ),
                topics={},
                message="No master cases directory found"
            )
        
        topics_dict = {}
        all_cases = []  # Flat array for all cases
        total_cases = 0
        generated_cases = 0
        failed_cases = 0
        
        # Scan the case_docs directory
        for item in case_docs_dir.iterdir():
            if item.is_dir():
                # This is a topic folder
                topic_name = item.name
                cases_in_topic = []
                
                # Scan for markdown files in this topic folder
                for case_file in item.glob("*.md"):
                    case_info = get_case_info_from_file(case_file, topic_name)
                    cases_in_topic.append(case_info)
                    total_cases += 1
                    
                    if case_info.status == "generated":
                        generated_cases += 1
                    elif case_info.status == "failed":
                        failed_cases += 1
                
                if cases_in_topic:  # Only add topics that have cases
                    topics_dict[topic_name] = cases_in_topic
            
            elif item.is_file() and item.suffix == ".md":
                # This is a case file in the root (legacy cases without topic folders)
                topic_name = "General"
                if topic_name not in topics_dict:
                    topics_dict[topic_name] = []
                
                case_info = get_case_info_from_file(item, topic_name)
                topics_dict[topic_name].append(case_info)
                total_cases += 1
                
                if case_info.status == "generated":
                    generated_cases += 1
                elif case_info.status == "failed":
                    failed_cases += 1
        
        # Sort cases within each topic by creation date (newest first)
        for topic in topics_dict:
            topics_dict[topic].sort(key=lambda x: x.created_at, reverse=True)
        
        # Create flat array of all cases
        all_cases = []
        for topic_cases in topics_dict.values():
            all_cases.extend(topic_cases)
        
        stats = MasterCaseStats(
            total_topics=len(topics_dict),
            total_cases=total_cases,
            generated_cases=generated_cases,
            failed_cases=failed_cases,
            pending_cases=0  # We don't track pending cases yet
        )
        
        return MasterCaseListResponse(
            success=True,
            stats=stats,
            cases=all_cases,  # Add the required cases field
            topics=topics_dict,
            message=f"Found {total_cases} master cases across {len(topics_dict)} topics"
        )
        
    except Exception as e:
        print(f"Error listing master cases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing master cases: {str(e)}"
        )

@router.get("/{case_id}/content/")
async def get_case_content(case_id: str):
    """
    Get the content of a specific master case for preview
    """
    try:
        # Search for the file across all topic folders since case_id no longer includes topic
        case_docs_dir = Path("cache/case_docs")
        case_file_path = None
        
        # First try legacy path (files in root)
        legacy_path = case_docs_dir / f"{case_id}.md"
        if legacy_path.exists():
            case_file_path = legacy_path
        else:
            # Search in topic folders
            for item in case_docs_dir.iterdir():
                if item.is_dir():
                    potential_path = item / f"{case_id}.md"
                    if potential_path.exists():
                        case_file_path = potential_path
                        break
        
        if not case_file_path or not case_file_path.exists():
            raise HTTPException(status_code=404, detail="Case file not found")
        
        # Read file content
        with open(case_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return JSONResponse(content={
            "success": True,
            "case_id": case_id,
            "content": content,
            "file_path": str(case_file_path)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting case content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting case content: {str(e)}"
        )

@router.get("/{case_id}/download/")
async def download_case(case_id: str):
    """
    Download a specific master case file
    """
    try:
        # Search for the file across all topic folders since case_id no longer includes topic
        case_docs_dir = Path("cache/case_docs")
        case_file_path = None
        
        # First try legacy path (files in root)
        legacy_path = case_docs_dir / f"{case_id}.md"
        if legacy_path.exists():
            case_file_path = legacy_path
        else:
            # Search in topic folders
            for item in case_docs_dir.iterdir():
                if item.is_dir():
                    potential_path = item / f"{case_id}.md"
                    if potential_path.exists():
                        case_file_path = potential_path
                        break
        
        if not case_file_path or not case_file_path.exists():
            raise HTTPException(status_code=404, detail="Case file not found")
        
        return FileResponse(
            path=case_file_path,
            filename=f"{case_id}.md",
            media_type="text/markdown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading case: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading case: {str(e)}"
        )

@router.post("/{case_id}/regenerate/")
async def regenerate_case(case_id: str):
    """
    Regenerate a failed or existing master case
    """
    try:
        # This would integrate with the master case generation system
        # For now, return a placeholder response
        return JSONResponse(content={
            "success": True,
            "message": f"Case regeneration initiated for {case_id}",
            "case_id": case_id
        })
        
    except Exception as e:
        print(f"Error regenerating case: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating case: {str(e)}"
        )

@router.post("/upload/")
async def upload_master_cases():
    """
    Upload master cases - logs the case IDs for now
    """
    try:
        from fastapi import Request
        
        # Get the request body
        async def get_request_body(request: Request):
            body = await request.body()
            if body:
                import json
                return json.loads(body.decode())
            return {}
        
        # This is a placeholder - we'll get the actual request in the endpoint
        return JSONResponse(content={
            "success": True,
            "message": "Upload endpoint created"
        })
        
    except Exception as e:
        print(f"Error in upload endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading master cases: {str(e)}"
        )

@router.post("/upload-cases/")
async def upload_master_cases_with_ids(request_data: dict):
    """
    Upload master cases - reads files and uploads them to external API
    """
  
    
    try:
        case_ids = request_data.get('case_ids', [])
        topic_id = request_data.get('topic_id', '')
        
        print(f"🚀 Upload Master Cases API called:")
        print(f"   Topic ID: {topic_id}")
        print(f"   Case IDs: {case_ids}")
        print(f"   Total cases: {len(case_ids)}")
        
        # Log each case ID
        for i, case_id in enumerate(case_ids, 1):
            print(f"   {i}. {case_id}")
        
        uploaded_files = []
        failed_uploads = []
        
        # Process each case file
        for case_id in case_ids:
            try:
                print(f"\n📁 Processing case: {case_id}")
                
                # Search for the file across all topic folders since case_id no longer includes topic
                case_docs_dir = Path("cache/case_docs")
                case_file_path = None
                filename = case_id  # case_id is now just the filename
                
                # First try in the specified topic folder
                if topic_id:
                    topic_path = case_docs_dir / topic_id / f"{filename}.md"
                    if topic_path.exists():
                        case_file_path = topic_path
                
                # If not found in topic folder, try legacy path (files in root)
                if not case_file_path:
                    legacy_path = case_docs_dir / f"{filename}.md"
                    if legacy_path.exists():
                        case_file_path = legacy_path
                
                # If still not found, search in all topic folders
                if not case_file_path:
                    for item in case_docs_dir.iterdir():
                        if item.is_dir():
                            potential_path = item / f"{filename}.md"
                            if potential_path.exists():
                                case_file_path = potential_path
                                break
                
                if not case_file_path or not case_file_path.exists():
                    print(f"   ❌ File not found for case ID: {case_id}")
                    failed_uploads.append({"case_id": case_id, "error": "File not found"})
                    continue
                
                print(f"   📄 Found file: {case_file_path}")
                print(f"   🔄 Uploading to external API...")
                
                # Read file content
                async with aiofiles.open(case_file_path, 'rb') as f:
                    file_content = await f.read()
                
                # Prepare data for external API
                file_title = f"{filename}.md"
                
                # Create form data for the external API matching the expected structure
                data = aiohttp.FormData()
                data.add_field('files', file_content, filename=file_title, content_type='text/markdown')
                data.add_field('titles', file_title)  # Should be a list but FormData handles it
                data.add_field('descriptions', f"Master clinical case: {filename.replace('_', ' ')}")  # Add description
                data.add_field('department_name', 'dermatology')
                data.add_field('department_id', '2')
                
                # Upload to external API
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'http://localhost:8000/documents/upload-unauthenticated',
                        data=data
                    ) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            print(f"   ✅ Successfully uploaded: {file_title}")
                            
                            # Move file to "ready" folder after successful upload
                            try:
                                ready_dir = case_docs_dir / "ready"
                                ready_dir.mkdir(exist_ok=True)
                                
                                new_file_path = ready_dir / case_file_path.name
                                case_file_path.rename(new_file_path)
                                print(f"   📁 Moved to ready folder: {new_file_path}")
                                
                                uploaded_files.append({
                                    "case_id": case_id,
                                    "filename": file_title,
                                    "moved_to": str(new_file_path),
                                    "external_response": response_data
                                })
                            except Exception as move_error:
                                print(f"   ⚠️ Upload successful but failed to move file: {move_error}")
                                uploaded_files.append({
                                    "case_id": case_id,
                                    "filename": file_title,
                                    "move_error": str(move_error),
                                    "external_response": response_data
                                })
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Upload failed (HTTP {response.status}): {error_text}")
                            failed_uploads.append({
                                "case_id": case_id,
                                "error": f"HTTP {response.status}: {error_text}"
                            })
            
            except Exception as e:
                print(f"   ❌ Error processing {case_id}: {str(e)}")
                failed_uploads.append({"case_id": case_id, "error": str(e)})
        
        # Summary
        total_processed = len(uploaded_files) + len(failed_uploads)
        print(f"\n📊 Upload Summary:")
        print(f"   ✅ Successfully uploaded: {len(uploaded_files)}")
        print(f"   ❌ Failed uploads: {len(failed_uploads)}")
        print(f"   📁 Total processed: {total_processed}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Processed {total_processed} cases: {len(uploaded_files)} uploaded, {len(failed_uploads)} failed",
            "total_cases": len(case_ids),
            "uploaded_count": len(uploaded_files),
            "failed_count": len(failed_uploads),
            "uploaded_files": uploaded_files,
            "failed_uploads": failed_uploads,
            "topic_id": topic_id
        })
        
    except Exception as e:
        print(f"❌ Error in upload process: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading master cases: {str(e)}"
        )

@router.get("/stats/")
async def get_master_case_stats():
    """
    Get statistics about master cases
    """
    try:
        # Get the full list to calculate stats
        full_response = await list_master_cases()
        
        if not full_response.success:
            raise HTTPException(status_code=500, detail="Failed to get case statistics")
        
        return JSONResponse(content={
            "success": True,
            "stats": full_response.stats.dict()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting case statistics: {str(e)}"
        ) 