# PDF TOC Visualizer & Cropper with Image Extraction

A comprehensive web application for extracting table of contents (TOC) from PDF documents, visualizing them hierarchically, cropping sections, and extracting images using advanced document processing.

## 🚀 Features

### 📖 TOC Management
- **Document Upload**: Drag-drop or browse PDF files
- **TOC Extraction**: Extract table of contents using PyMuPDF
- **Hierarchical Display**: Interactive tree view with expand/collapse functionality
- **Search & Navigation**: Real-time search with highlighting and click-to-navigate

### ✂️ PDF Section Cropping
- **Smart Page Range Calculation**: Automatic calculation based on TOC hierarchy
- **Section-based Cropping**: Click TOC items to crop specific sections
- **Custom Page Ranges**: Manual page range selection with validation
- **Instant Download**: Generated PDF sections download automatically

### 🖼️ **NEW: Image Extraction (Powered by Docling)**
- **Advanced Image Detection**: Extract images and figures using [Docling](https://docling-project.github.io/docling/)
- **Dual Extraction Methods**: 
  - Docling's advanced figure recognition for high-quality extraction
  - PyMuPDF fallback for comprehensive image capture
- **Image Gallery**: Visual grid display with thumbnails and metadata
- **Modal Viewer**: Full-size image preview with zoom capabilities
- **Batch Download**: Download individual images or all images as ZIP
- **Image Metadata**: Display dimensions, file size, and captions

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PyMuPDF**: PDF processing and TOC extraction
- **PyPDF2**: PDF section cropping
- **Docling**: Advanced document analysis and image extraction
- **Pillow**: Image processing and conversion

### Frontend
- **Vanilla JavaScript**: Clean, framework-free implementation
- **Tailwind CSS**: Modern, responsive styling
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Prerequisites

- Python 3.8+
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd file-cropper
```

2. **Create and activate virtual environment**:
```bash
python -m venv crop-file
# Windows
crop-file\Scripts\activate
# Linux/Mac
source crop-file/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Start the Server
```bash
python app.py
```
Server will start at `http://localhost:8000`

### Open the Web Interface
Navigate to `http://localhost:8000` and open `index.html` in your browser.

### Extract Images from PDF Sections

1. **Upload PDF**: Drag-drop or browse to upload your PDF file
2. **Navigate TOC**: Explore the hierarchical table of contents
3. **Select Section**: Click on any TOC item to select a section
4. **Extract Images**: Click the "Extract Images" button in the crop panel
5. **View Results**: Browse extracted images in the gallery view
6. **Download**: Download individual images or get all images as a ZIP file

### Image Extraction Features

- **Smart Detection**: Docling identifies figures, charts, diagrams, and embedded images
- **Quality Preservation**: High-resolution image extraction with original quality
- **Format Support**: Images are saved as PNG for universal compatibility
- **Metadata Rich**: Each image includes dimensions, file size, and contextual captions
- **Batch Operations**: Extract all images from a section in one operation

## 🔧 API Endpoints

### Image Extraction Endpoints
- `POST /extract-images/` - Extract images from a PDF section
- `GET /download-image/{section_id}/{image_filename}` - Download specific image
- `POST /download-all-images/{section_id}` - Download all images as ZIP

### Existing Endpoints
- `POST /upload-document/` - Upload and process PDF
- `POST /crop-section/` - Crop PDF section
- `GET /file-info/{file_id}` - Get document information
- `POST /clear-uploads/` - Clear uploaded files
- `GET /upload-stats/` - Get upload statistics

## 📁 File Structure

```
file-cropper/
├── app.py                 # FastAPI backend with image extraction
├── index.html            # Web interface with image gallery
├── app.js                # Frontend JavaScript with image handling
├── requirements.txt      # Python dependencies including Docling
├── toc_extractor.py      # Command-line TOC extractor
├── pdf_cropper.py        # Command-line PDF cropper
├── temp_uploads/         # Temporary file storage
├── extracted_images/     # Extracted images storage
└── README.md            # This file
```

## 🎨 Image Extraction Workflow

1. **Section Selection**: Choose a PDF section via TOC navigation
2. **Dual Processing**: 
   - Docling analyzes document structure and extracts figures
   - PyMuPDF provides comprehensive image scanning as backup
3. **Image Processing**: Convert and optimize images for web display
4. **Gallery Display**: Show images in responsive grid with thumbnails
5. **Interactive Features**: Modal viewer, download options, metadata display

## 🔍 Docling Integration

This application leverages [Docling](https://docling-project.github.io/docling/) for advanced document processing:

- **Figure Export**: Extract high-quality figures and diagrams
- **Multimodal Processing**: Handle various document elements
- **Smart Recognition**: AI-powered image and figure detection
- **Format Support**: Works with PDF and other document formats

## 🌟 Key Features

### Image Gallery
- **Grid Layout**: Responsive image thumbnails
- **Hover Effects**: Smooth transitions and zoom effects
- **Quick Actions**: Download and view buttons for each image
- **Empty State**: Friendly message when no images are found

### Modal Viewer
- **Full-Size Display**: High-quality image viewing
- **Click-to-Close**: Intuitive navigation
- **Download Integration**: Direct download from modal
- **Metadata Display**: Image dimensions and file size

### Batch Operations
- **ZIP Download**: All section images in one file
- **Progress Indicators**: Loading states for long operations
- **Error Handling**: Graceful failure management
- **Auto Cleanup**: Temporary files automatically cleaned

## 🚨 Error Handling

- **File Validation**: Comprehensive upload validation
- **Graceful Degradation**: Fallback extraction methods
- **User Feedback**: Clear error messages and success notifications
- **Automatic Cleanup**: Failed operations don't leave artifacts

## 🔄 Auto-Cleanup

- **Upload Management**: Automatic cleanup on new uploads
- **Temporary Files**: Extracted images cleaned after download
- **Memory Management**: Efficient file handling to prevent bloat

## 🎯 Use Cases

- **Academic Research**: Extract figures and charts from research papers
- **Document Processing**: Batch extract images from technical documents
- **Content Migration**: Extract images for content management systems
- **Report Analysis**: Extract charts and diagrams from business reports
- **Educational Materials**: Extract images from textbooks and teaching materials

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **[Docling Project](https://docling-project.github.io/docling/)** for advanced document processing capabilities
- **PyMuPDF** for PDF processing and TOC extraction
- **FastAPI** for the modern web framework
- **Tailwind CSS** for responsive styling 