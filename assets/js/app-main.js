/**
 * Main Application Module
 * Coordinates and initializes all components for the File Cropper application
 */

import { CONFIG, ENV, EventBus } from './config.js';
import { Logger, UI } from './utils.js';
import { FileUploadComponent } from './components/file-upload.js';
import { TableProcessorComponent } from './components/table-processor.js';
import { ChapterManagerComponent } from './components/chapter-manager.js';

class FileCropperApp {
    constructor() {
        this.components = {};
        this.initialized = false;
        this.currentPage = this.detectCurrentPage();

        Logger.log('File Cropper App initializing...', { page: this.currentPage, env: ENV });
    }

    /**
     * Detect current page based on URL or page content
     */
    detectCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();

        if (filename.includes('case-creator')) return 'case-creator';
        if (filename.includes('table-processor')) return 'table-processor';
        if (filename.includes('extractions-viewer')) return 'extractions-viewer';
        if (filename.includes('index')) return 'index';

        // Fallback to detecting by page content
        if (document.querySelector('#case-creator-container')) return 'case-creator';
        if (document.querySelector('#table-processor-container')) return 'table-processor';
        if (document.querySelector('#extractions-container')) return 'extractions-viewer';
        if (document.querySelector('#chapter-manager-container')) return 'chapter-manager';

        return 'unknown';
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            Logger.log('Initializing File Cropper App...');

            // Setup global error handling
            this.setupErrorHandling();

            // Setup global event listeners
            this.setupGlobalEvents();

            // Initialize components based on current page
            await this.initializePageComponents();

            // Setup inter-component communication
            this.setupComponentCommunication();

            this.initialized = true;
            Logger.log('File Cropper App initialized successfully');

            // Emit app ready event
            EventBus.emit('app:ready', { page: this.currentPage });

        } catch (error) {
            Logger.error('Failed to initialize app:', error);
            UI.showToast('Application failed to initialize', 'error');
        }
    }

    /**
     * Initialize components for the current page
     */
    async initializePageComponents() {
        switch (this.currentPage) {
            case 'case-creator':
                await this.initUploadFormPage();
                break;

            case 'table-processor':
                await this.initTableProcessorPage();
                break;

            case 'extractions-viewer':
                await this.initExtractionsViewerPage();
                break;

            case 'index':
                await this.initIndexPage();
                break;

            default:
                Logger.warn('Unknown page type, initializing common components only');
                await this.initCommonComponents();
        }
    }

    /**
     * Initialize upload form page components
     */
    async initUploadFormPage() {
        Logger.log('Initializing upload form page...');

        // Initialize file upload component if container exists
        if (document.getElementById('file-upload-container')) {
            this.components.fileUpload = new FileUploadComponent('file-upload-container', {
                onUploadComplete: (results) => {
                    Logger.log('Upload completed:', results);
                    EventBus.emit('upload:complete', results);
                }
            });
        }

        // Initialize table processor for extraction
        if (document.getElementById('table-extraction-container')) {
            this.components.tableProcessor = new TableProcessorComponent('table-extraction-container', {
                extractEndpoint: CONFIG.API.ENDPOINTS.EXTRACT_TABLE_JSON
            });
        }

        await this.initCommonComponents();
    }

    /**
     * Initialize table processor page components
     */
    async initTableProcessorPage() {
        Logger.log('Initializing table processor page...');

        if (document.getElementById('table-processor-container')) {
            this.components.tableProcessor = new TableProcessorComponent('table-processor-container');

            // Load available files
            await this.components.tableProcessor.loadAvailableFiles();
        }

        await this.initCommonComponents();
    }

    /**
     * Initialize extractions viewer page components
     */
    async initExtractionsViewerPage() {
        Logger.log('Initializing extractions viewer page...');

        // Initialize existing extractions viewer functionality
        if (window.ExtractionsViewer) {
            this.components.extractionsViewer = new window.ExtractionsViewer();
        }

        await this.initCommonComponents();
    }

    /**
     * Initialize index page components
     */
    async initIndexPage() {
        Logger.log('Initializing index page...');

        // Initialize chapter manager if container exists
        if (document.getElementById('chapter-manager-container')) {
            this.components.chapterManager = new ChapterManagerComponent('chapter-manager-container');

            // Load available files for chapter creation
            await this.components.chapterManager.loadAvailableFiles();
        }

        // Initialize file upload for general use
        if (document.getElementById('general-upload-container')) {
            this.components.fileUpload = new FileUploadComponent('general-upload-container');
        }

        await this.initCommonComponents();
    }

    /**
     * Initialize common components available on all pages
     */
    async initCommonComponents() {
        // Initialize any common functionality here
        this.setupNavigationHandlers();
        this.setupThemeHandlers();
    }

    /**
     * Setup global error handling
     */
    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            Logger.error('Global error:', event.error);
            UI.showToast('An unexpected error occurred', 'error');
        });

        window.addEventListener('unhandledrejection', (event) => {
            Logger.error('Unhandled promise rejection:', event.reason);
            UI.showToast('An unexpected error occurred', 'error');
        });
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEvents() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                EventBus.emit('app:hidden');
            } else {
                EventBus.emit('app:visible');
            }
        });

        // Handle online/offline status
        window.addEventListener('online', () => {
            EventBus.emit('app:online');
            UI.showToast('Connection restored', 'success');
        });

        window.addEventListener('offline', () => {
            EventBus.emit('app:offline');
            UI.showToast('Connection lost', 'warning');
        });
    }

    /**
     * Setup communication between components
     */
    setupComponentCommunication() {
        // File upload completion triggers table processor update
        EventBus.on('upload:complete', (data) => {
            if (this.components.tableProcessor) {
                this.components.tableProcessor.loadAvailableFiles();
            }
            if (this.components.chapterManager) {
                this.components.chapterManager.loadAvailableFiles();
            }
        });

        // Chapter creation triggers list refresh
        EventBus.on('chapter:created', () => {
            if (this.components.chapterManager) {
                this.components.chapterManager.refresh();
            }
        });

        // Table extraction completion
        EventBus.on('extraction:complete', (data) => {
            Logger.log('Extraction completed:', data);
        });
    }

    /**
     * Setup navigation handlers
     */
    setupNavigationHandlers() {
        // Handle navigation between pages if needed
        const navLinks = document.querySelectorAll('a[data-page]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const targetPage = e.target.getAttribute('data-page');
                this.navigateToPage(targetPage);
            });
        });
    }

    /**
     * Setup theme handlers
     */
    setupThemeHandlers() {
        // Handle theme switching if implemented
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    /**
     * Navigate to a different page
     */
    navigateToPage(page) {
        const pageUrls = {
            'upload': 'case-creator.html',
            'processor': 'table-processor.html',
            'viewer': 'extractions-viewer.html',
            'index': 'index.html'
        };

        if (pageUrls[page]) {
            window.location.href = pageUrls[page];
        }
    }

    /**
     * Toggle application theme
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        EventBus.emit('theme:changed', newTheme);
    }

    /**
     * Get component instance
     */
    getComponent(name) {
        return this.components[name];
    }

    /**
     * Check if app is initialized
     */
    isInitialized() {
        return this.initialized;
    }

    /**
     * Destroy the application and cleanup
     */
    destroy() {
        // Cleanup components
        Object.values(this.components).forEach(component => {
            if (component && typeof component.destroy === 'function') {
                component.destroy();
            }
        });

        // Clear event listeners
        EventBus.events = {};

        this.initialized = false;
        Logger.log('File Cropper App destroyed');
    }
}

// Create global app instance
let app = null;

/**
 * Initialize the application when DOM is ready
 */
function initializeApp() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            app = new FileCropperApp();
            app.init();
        });
    } else {
        app = new FileCropperApp();
        app.init();
    }
}

/**
 * Get the global app instance
 */
function getApp() {
    return app;
}

// Auto-initialize if not in test environment
if (typeof window !== 'undefined' && !window.__TEST_MODE__) {
    initializeApp();
}

// Export for use in other modules
export { FileCropperApp, getApp, initializeApp }; 