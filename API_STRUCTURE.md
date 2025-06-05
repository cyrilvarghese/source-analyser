# File Cropper API v2.0.0 - Refactored Structure

## Overview

The File Cropper application has been refactored into a modular structure using FastAPI routers for better organization and maintainability.

## Project Structure

```
file-cropper/
├── app.py                    # Main FastAPI application (refactored)
├── app_backup.py            # Backup of original monolithic app.py
├── utils.py                 # Shared utilities and configurations
├── routers/                 # Modular API routers
│   ├── __init__.py         # Router package initialization
│   ├── upload.py           # File upload and document processing
│   ├── tables.py           # Table extraction and Gemini API processing
│   ├── chapters.py         # PDF cropping and chapter management
│   ├── extractions.py      # Static file serving and extraction management
│   ├── admin.py            # Administrative and cleanup functions
│   └── debug.py            # Debugging and monitoring endpoints
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create manually)
└── frontend files...        # HTML, JS, CSS files
```

## API Endpoints

### Upload Router (`/api/upload`)
- `POST /api/upload/document/` - Upload PDF and extract TOC
- `GET /api/upload/file-info/{file_id}` - Get file information
- `GET /api/upload/stats/` - Upload statistics

### Tables Router (`/api/tables`)
- `POST /api/tables/extract-json/` - Extract tables to JSON using Gemini API
- `POST /api/tables/process/` - Process tables to multiple formats (CSV, HTML, Markdown)

### Chapters Router (`/api/chapters`)
- `POST /api/chapters/crop-section/` - Crop PDF sections
- `GET /api/chapters/download/{chapter_id}` - Download cropped PDF
- `GET /api/chapters/browse/{chapter_id}` - Browse chapter details
- `GET /api/chapters/list/` - List all chapters
- `DELETE /api/chapters/delete/{chapter_id}` - Delete chapter
- `GET /api/chapters/debug/` - Debug chapter information

### Extractions Router (`/api/extractions`)
- `GET /api/extractions/serve-html/{extract_folder}/{html_filename}` - Serve HTML files
- `GET /api/extractions/view/{extract_folder}/{html_filename}` - View extractions
- `GET /api/extractions/list-docling/` - List docling extractions
- `GET /api/extractions/list-files/{folder_name}` - List extraction files
- `GET /api/extractions/info/{folder_name}` - Get extraction info
- `GET /api/extractions/test-image/{extraction_dir}/{filename}` - Test image serving
- `GET /api/extractions/serve-pdf/{filename}` - Serve PDF files

### Admin Router (`/api/admin`)
- `POST /api/admin/clear-uploads/` - Clear upload folder
- `DELETE /api/admin/cleanup/{file_id}` - Cleanup specific file
- `GET /api/admin/stats/` - System statistics
- `GET /api/admin/health/` - Health check

### Debug Router (`/api/debug`)
- `GET /api/debug/mounts/` - Debug mounted paths
- `GET /api/debug/system-info/` - System information

## Legacy Compatibility

The following legacy endpoints are maintained for backward compatibility:
- `POST /upload-document/` → `POST /api/upload/document/`
- `POST /crop-section/` → `POST /api/chapters/crop-section/`
- `POST /extract-table-json/` → `POST /api/tables/extract-json/`
- `GET /download-cropped/{chapter_id}` → `GET /api/chapters/download/{chapter_id}`
- `GET /list-chapters` → `GET /api/chapters/list/`

## Shared Utilities (`utils.py`)

Contains shared functions and configurations:
- Global constants (UPLOAD_DIR, CROPPED_PDFS_DIR)
- In-memory storage (file_store, chapter_extractions)
- Common functions (clear_upload_folder, extract_toc_from_document, etc.)
- PDF processing utilities (crop_pdf_pages, extract_images_from_cropped_pdf)

## Environment Configuration

Create a `.env` file in the root directory:
```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# You can get your free API key from: https://aistudio.google.com/app/apikey
```

## Benefits of Refactoring

1. **Modularity**: Each router handles a specific domain of functionality
2. **Maintainability**: Easier to modify and extend individual components
3. **Testability**: Each router can be tested independently
4. **Scalability**: Easy to add new routers or modify existing ones
5. **Code Organization**: Clear separation of concerns
6. **Documentation**: Better API documentation with grouped endpoints

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run the application
python app.py
```

The application will start on `http://localhost:8001` with automatic API documentation available at `/docs`.

## Migration Notes

- All existing functionality is preserved
- Legacy endpoints continue to work for backward compatibility
- New modular structure makes future development easier
- Shared utilities are centralized in `utils.py`
- Environment variables are now properly managed 