# Frontend Structure Documentation

## Overview

The frontend code has been refactored from monolithic JavaScript files into a modular, component-based architecture. This structure improves maintainability, reusability, and organization while preserving all existing functionality.

## Directory Structure

```
assets/
├── js/
│   ├── config.js              # Application configuration and settings
│   ├── utils.js               # Shared utility functions
│   ├── app-main.js            # Main application coordinator
│   └── components/            # Reusable UI components
│       ├── file-upload.js     # File upload with drag & drop
│       ├── table-processor.js # Table extraction and processing
│       └── chapter-manager.js # PDF cropping and chapter management
├── css/
│   └── main.css              # Shared styles and component base styles
└── components/               # Future component templates (if needed)

templates/                    # Refactored HTML templates
├── index.html               # Main dashboard with chapter manager
├── case-creator.html         # File upload and table extraction
├── table-processor.html     # Dedicated table processing page
└── extractions-viewer.html  # Browse extracted data (uses existing code)
```

## Core Modules

### 1. Configuration (`assets/js/config.js`)

Centralized configuration for the entire frontend application.

**Key Features:**
- API endpoint configuration (new and legacy endpoints)
- UI settings (timeouts, file limits, animations)
- Feature flags for enabling/disabling functionality
- Error and success message templates
- Global event bus for component communication

**Usage:**
```javascript
import { CONFIG, ENV, EventBus } from './config.js';

// Access API endpoints
const uploadUrl = CONFIG.API.ENDPOINTS.UPLOAD_DOCUMENT;

// Use UI settings
const maxFileSize = CONFIG.UI.MAX_FILE_SIZE;

// Emit events
EventBus.emit('upload:complete', data);
```

### 2. Utilities (`assets/js/utils.js`)

Shared utility functions used across all components.

**Modules:**
- **API**: HTTP request helpers (GET, POST, DELETE)
- **DOM**: Element manipulation and creation
- **FileUtils**: File validation and formatting
- **UI**: Toast notifications, loading states, debouncing
- **Storage**: localStorage management with error handling
- **Validator**: Form validation helpers
- **DateTime**: Date formatting and relative time
- **Clipboard**: Copy to clipboard functionality
- **Logger**: Development and production logging

**Usage:**
```javascript
import { API, UI, FileUtils } from './utils.js';

// Make API requests
const data = await API.post('/api/upload/', formData);

// Show notifications
UI.showToast('Upload successful!', 'success');

// Validate files
if (FileUtils.isValidFileType(file)) { ... }
```

### 3. Main Application (`assets/js/app-main.js`)

Application coordinator that initializes and manages all components.

**Features:**
- Page detection and component initialization
- Global error handling
- Inter-component communication setup
- Theme management
- Navigation handling

**Page Detection:**
- Automatically detects current page and initializes appropriate components
- Supports case-creator, table-processor, extractions-viewer, and index pages

## Components

### 1. File Upload Component (`assets/js/components/file-upload.js`)

Reusable file upload component with drag & drop support.

**Features:**
- Drag and drop file upload
- File type and size validation
- Progress tracking
- Multi-file support (configurable)
- Real-time file list display
- Auto-upload or manual trigger options

**Container Requirements:**
```html
<div id="file-upload-container"></div>
```

**Initialization:**
```javascript
const fileUpload = new FileUploadComponent('file-upload-container', {
    onUploadComplete: (results) => {
        console.log('Upload completed:', results);
    },
    allowMultiple: false,
    maxFileSize: 100 * 1024 * 1024 // 100MB
});
```

### 2. Table Processor Component (`assets/js/components/table-processor.js`)

Handles table extraction and processing functionality.

**Features:**
- File selection from uploaded files
- Processing options (full rows, preserve format)
- Multiple view modes (Preview, JSON, Raw)
- Copy to clipboard and download JSON
- Processing history with reload capability
- Tab-based result display

**Container Requirements:**
```html
<div id="table-processor-container"></div>
```

**API Integration:**
- Uses `/api/tables/extract-json/` for extraction
- Uses `/api/tables/process/` for additional processing
- Maintains compatibility with full row object format

### 3. Chapter Manager Component (`assets/js/components/chapter-manager.js`)

PDF cropping and chapter management functionality.

**Features:**
- Chapter creation from PDF page ranges
- Chapter listing with search and filtering
- Bulk operations (download, delete)
- Chapter preview modal
- Source file selection
- Grid-based chapter display

**Container Requirements:**
```html
<div id="chapter-manager-container"></div>
```

**API Integration:**
- Uses `/api/chapters/crop-section/` for creating chapters
- Uses `/api/chapters/list/` for listing chapters
- Uses `/api/chapters/download/` and `/api/chapters/delete/` for management

## HTML Templates

### Refactored Templates

All HTML files have been refactored to use the new modular structure:

1. **templates/index.html**
   - Main dashboard with quick actions
   - Chapter manager integration
   - General file upload area
   - Feature overview cards

2. **templates/case-creator.html**
   - File upload component
   - Table extraction component
   - Simplified structure using components

3. **templates/table-processor.html**
   - Dedicated table processing interface
   - Full table processor component
   - Navigation between pages

### Template Features

- **Consistent Styling**: All templates use the shared CSS framework
- **Component Integration**: Components are initialized automatically based on container presence
- **Responsive Design**: Mobile-friendly layouts
- **Navigation**: Standardized navigation between pages
- **Modular Loading**: Only required components are loaded per page

## CSS Framework (`assets/css/main.css`)

Comprehensive CSS framework with:

- **CSS Variables**: Centralized theming and dark mode support
- **Component Styles**: Reusable card, button, form, and modal styles
- **Utility Classes**: Common layout and spacing utilities
- **Responsive Design**: Mobile-first responsive breakpoints
- **Theme Support**: Light and dark theme variables
- **Animation**: Smooth transitions and loading states

## Migration from Legacy Code

### Key Changes

1. **Modular Architecture**: Split monolithic files into focused components
2. **Component Reusability**: Components can be used across multiple pages
3. **Consistent API**: Standardized API endpoints and error handling
4. **Improved UX**: Better loading states, notifications, and responsive design
5. **Maintainability**: Clear separation of concerns and documentation

### Backward Compatibility

- All existing API endpoints remain functional
- Original HTML files are preserved as reference
- Legacy JavaScript files (app.js, table-processor.js, extractions-viewer.js) remain untouched
- New structure provides enhanced features while maintaining core functionality

### Benefits

1. **Maintainability**: Easier to modify and extend individual components
2. **Testing**: Components can be tested in isolation
3. **Performance**: Modular loading reduces initial page load
4. **Consistency**: Shared utilities ensure consistent behavior
5. **Documentation**: Well-documented structure and APIs

## Usage Guide

### For Developers

1. **Adding New Components**:
   - Create component file in `assets/js/components/`
   - Follow the existing component pattern
   - Add initialization logic to `app-main.js`

2. **Modifying Existing Components**:
   - Components are self-contained
   - Modify component files directly
   - Update configuration in `config.js` if needed

3. **Adding New Pages**:
   - Create HTML template in `templates/`
   - Add page detection logic to `app-main.js`
   - Include necessary component containers

### For Users

The refactored frontend maintains all existing functionality:

- **Upload files**: Use case-creator.html or index.html
- **Process tables**: Use table-processor.html
- **Manage chapters**: Available on index.html
- **View extractions**: Use extractions-viewer.html (unchanged)

## Future Enhancements

The modular structure enables easy future enhancements:

1. **Additional Components**: File browser, settings panel, user management
2. **Advanced Features**: Real-time collaboration, advanced search, bulk operations
3. **Testing Framework**: Unit tests for individual components
4. **Build Process**: Bundling and minification for production
5. **TypeScript**: Type safety for larger projects

## API Integration

The frontend integrates seamlessly with the refactored backend API structure:

- **New Endpoints**: Uses `/api/` prefixed endpoints
- **Legacy Support**: Maintains compatibility with original endpoints
- **Error Handling**: Standardized error responses and user feedback
- **File Management**: Improved file upload and processing workflows

This refactored structure provides a solid foundation for continued development while maintaining all existing functionality and improving the overall user experience. 