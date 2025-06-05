/**
 * Application Configuration
 * Centralized configuration for the File Cropper frontend
 */

export const CONFIG = {
    // API Configuration
    API: {
        BASE_URL: '',  // Empty for relative URLs
        ENDPOINTS: {
            // Upload endpoints
            UPLOAD_DOCUMENT: '/api/upload/document/',
            UPLOAD_STATS: '/api/upload/stats/',
            FILE_INFO: '/api/upload/file-info/',

            // Table endpoints
            EXTRACT_TABLE_JSON: '/api/tables/extract-json/',
            PROCESS_TABLE: '/api/tables/process/',

            // Chapter endpoints
            CROP_SECTION: '/api/chapters/crop-section/',
            DOWNLOAD_CHAPTER: '/api/chapters/download/',
            LIST_CHAPTERS: '/api/chapters/list/',
            DELETE_CHAPTER: '/api/chapters/delete/',
            BROWSE_CHAPTER: '/api/chapters/browse/',

            // Extraction endpoints
            LIST_EXTRACTIONS: '/api/extractions/list-docling/',
            LIST_FILES: '/api/extractions/list-files/',
            SERVE_HTML: '/api/extractions/serve-html/',

            // Admin endpoints
            CLEAR_UPLOADS: '/api/admin/clear-uploads/',
            SYSTEM_STATS: '/api/admin/stats/',
            HEALTH_CHECK: '/api/admin/health/',

            // Legacy endpoints (for backward compatibility)
            LEGACY_UPLOAD: '/upload-document/',
            LEGACY_CROP: '/crop-section/',
            LEGACY_EXTRACT_JSON: '/extract-table-json/',
            LEGACY_DOWNLOAD: '/download-cropped/',
            LEGACY_LIST: '/list-chapters'
        }
    },

    // UI Configuration
    UI: {
        ANIMATION_DURATION: 300,
        DEBOUNCE_DELAY: 500,
        MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
        ALLOWED_FILE_TYPES: ['.pdf', '.png', '.jpg', '.jpeg'],
        POLLING_INTERVAL: 2000,
        TOAST_DURATION: 5000
    },

    // Feature Flags
    FEATURES: {
        USE_NEW_API: true,
        ENABLE_DEBUG: false,
        ENABLE_ANALYTICS: false,
        ENABLE_OFFLINE_MODE: false
    },

    // Error Messages
    ERRORS: {
        NETWORK_ERROR: 'Network error occurred. Please try again.',
        FILE_TOO_LARGE: 'File size exceeds the maximum limit.',
        INVALID_FILE_TYPE: 'Invalid file type. Please select a valid file.',
        UPLOAD_FAILED: 'Upload failed. Please try again.',
        PROCESSING_ERROR: 'Processing error occurred.',
        NO_FILE_SELECTED: 'Please select a file first.',
        API_KEY_MISSING: 'API key is required but not configured.'
    },

    // Success Messages
    MESSAGES: {
        UPLOAD_SUCCESS: 'File uploaded successfully!',
        PROCESSING_COMPLETE: 'Processing completed successfully!',
        DOWNLOAD_READY: 'Download is ready!',
        COPY_SUCCESS: 'Copied to clipboard!',
        DELETE_SUCCESS: 'Item deleted successfully!'
    }
};

// Environment detection
export const ENV = {
    isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    isProduction: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
    version: '2.0.0'
};

// Global event bus for component communication
export const EventBus = {
    events: {},

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    },

    off(event, callback) {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        }
    },

    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    }
}; 