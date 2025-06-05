#!/usr/bin/env python3
"""
Shared utilities and configurations for the File Cropper application
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Optional
import pymupdf
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global configurations
UPLOAD_DIR = "temp_uploads"
CROPPED_PDFS_DIR = "cropped-pdfs"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CROPPED_PDFS_DIR, exist_ok=True)

# In-memory storage for file info (in production, use a database)
file_store = {}

# Chapter mapping for extracted content
chapter_extractions = {}

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

# Import docling extraction function
try:
    from docling_figure_extractor import extract_figures_with_docling
except ImportError:
    print("Warning: docling_figure_extractor not found. PDF extraction features will be limited.")
    extract_figures_with_docling = None

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