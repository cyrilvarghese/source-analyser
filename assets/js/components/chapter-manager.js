/**
 * Chapter Manager Component
 * Handles PDF cropping and chapter management functionality
 */

import { CONFIG } from '../config.js';
import { API, DOM, UI, Logger, DateTime, FileUtils } from '../utils.js';

export class ChapterManagerComponent {
    constructor(containerId, options = {}) {
        this.container = DOM.getElementById(containerId);
        this.options = {
            cropEndpoint: CONFIG.API.ENDPOINTS.CROP_SECTION,
            listEndpoint: CONFIG.API.ENDPOINTS.LIST_CHAPTERS,
            downloadEndpoint: CONFIG.API.ENDPOINTS.DOWNLOAD_CHAPTER,
            deleteEndpoint: CONFIG.API.ENDPOINTS.DELETE_CHAPTER,
            browseEndpoint: CONFIG.API.ENDPOINTS.BROWSE_CHAPTER,
            enablePreview: true,
            enableBulkOperations: true,
            ...options
        };

        this.chapters = [];
        this.selectedChapters = new Set();
        this.init();
    }

    init() {
        if (!this.container) {
            Logger.error('Chapter manager container not found');
            return;
        }

        this.createManagerUI();
        this.setupEventListeners();
        this.loadChapters();
        Logger.log('Chapter manager component initialized');
    }

    createManagerUI() {
        this.container.innerHTML = `
            <div class="chapter-manager-wrapper">
                <div class="manager-header mb-6">
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">Chapter Management</h3>
                    <p class="text-gray-600">Crop PDF sections and manage extracted chapters</p>
                </div>

                <div class="cropping-section mb-8 bg-white p-6 rounded-lg border">
                    <h4 class="text-lg font-medium text-gray-800 mb-4">Create New Chapter</h4>
                    
                    <div class="crop-form space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Chapter Title</label>
                                <input type="text" class="chapter-title w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Enter chapter title">
                            </div>
                            
                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Source File</label>
                                <select class="source-file w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                                    <option value="">Select source PDF...</option>
                                </select>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Start Page</label>
                                <input type="number" class="start-page w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" min="1" placeholder="1">
                            </div>
                            
                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">End Page</label>
                                <input type="number" class="end-page w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" min="1" placeholder="10">
                            </div>
                        </div>

                        <div class="crop-actions flex gap-3">
                            <button class="btn-crop bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors">
                                Create Chapter
                            </button>
                            <button class="btn-clear-form bg-gray-400 hover:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors">
                                Clear Form
                            </button>
                        </div>
                    </div>
                </div>

                <div class="chapters-section">
                    <div class="section-header flex items-center justify-between mb-4">
                        <h4 class="text-lg font-medium text-gray-800">Existing Chapters</h4>
                        <div class="header-actions flex gap-2">
                            <button class="btn-refresh bg-green-500 hover:bg-green-600 text-white px-3 py-1 text-sm rounded">
                                Refresh
                            </button>
                            <button class="btn-bulk-download bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 text-sm rounded hidden">
                                Download Selected
                            </button>
                            <button class="btn-bulk-delete bg-red-500 hover:bg-red-600 text-white px-3 py-1 text-sm rounded hidden">
                                Delete Selected
                            </button>
                        </div>
                    </div>

                    <div class="chapters-filter mb-4">
                        <div class="flex flex-wrap gap-3 items-center">
                            <input type="text" class="search-chapters flex-1 min-w-64 p-2 border border-gray-300 rounded-lg" placeholder="Search chapters...">
                            <select class="filter-source p-2 border border-gray-300 rounded-lg">
                                <option value="">All sources</option>
                            </select>
                            <button class="btn-select-all bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded text-sm">
                                Select All
                            </button>
                        </div>
                    </div>

                    <div class="chapters-list">
                        <div class="loading-state flex items-center justify-center py-8">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                            <span>Loading chapters...</span>
                        </div>
                    </div>
                </div>

                <div class="chapter-preview-modal hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
                    <div class="modal-content bg-white rounded-lg p-6 max-w-4xl max-h-[90vh] overflow-auto">
                        <div class="modal-header flex items-center justify-between mb-4">
                            <h5 class="text-lg font-medium">Chapter Preview</h5>
                            <button class="btn-close-modal text-gray-500 hover:text-gray-700">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="preview-content"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.setupElementReferences();
    }

    setupElementReferences() {
        // Form elements
        this.chapterTitle = this.container.querySelector('.chapter-title');
        this.sourceFile = this.container.querySelector('.source-file');
        this.startPage = this.container.querySelector('.start-page');
        this.endPage = this.container.querySelector('.end-page');

        // Buttons
        this.btnCrop = this.container.querySelector('.btn-crop');
        this.btnClearForm = this.container.querySelector('.btn-clear-form');
        this.btnRefresh = this.container.querySelector('.btn-refresh');
        this.btnBulkDownload = this.container.querySelector('.btn-bulk-download');
        this.btnBulkDelete = this.container.querySelector('.btn-bulk-delete');
        this.btnSelectAll = this.container.querySelector('.btn-select-all');

        // Search and filter
        this.searchChapters = this.container.querySelector('.search-chapters');
        this.filterSource = this.container.querySelector('.filter-source');

        // Lists and containers
        this.chaptersList = this.container.querySelector('.chapters-list');
        this.loadingState = this.container.querySelector('.loading-state');

        // Modal
        this.previewModal = this.container.querySelector('.chapter-preview-modal');
        this.modalContent = this.container.querySelector('.preview-content');
        this.btnCloseModal = this.container.querySelector('.btn-close-modal');
    }

    setupEventListeners() {
        // Create chapter
        this.btnCrop.addEventListener('click', () => {
            this.createChapter();
        });

        // Clear form
        this.btnClearForm.addEventListener('click', () => {
            this.clearForm();
        });

        // Refresh chapters
        this.btnRefresh.addEventListener('click', () => {
            this.loadChapters();
        });

        // Bulk operations
        this.btnBulkDownload.addEventListener('click', () => {
            this.bulkDownload();
        });

        this.btnBulkDelete.addEventListener('click', () => {
            this.bulkDelete();
        });

        // Select all
        this.btnSelectAll.addEventListener('click', () => {
            this.toggleSelectAll();
        });

        // Search and filter
        this.searchChapters.addEventListener('input', UI.debounce(() => {
            this.filterChapters();
        }));

        this.filterSource.addEventListener('change', () => {
            this.filterChapters();
        });

        // Modal close
        this.btnCloseModal.addEventListener('click', () => {
            this.closePreviewModal();
        });

        this.previewModal.addEventListener('click', (e) => {
            if (e.target === this.previewModal) {
                this.closePreviewModal();
            }
        });
    }

    async loadAvailableFiles() {
        try {
            const response = await API.get(CONFIG.API.ENDPOINTS.UPLOAD_STATS);
            if (response.files && response.files.length > 0) {
                this.populateSourceFileSelector(response.files);
            }
        } catch (error) {
            Logger.error('Failed to load available files:', error);
        }
    }

    populateSourceFileSelector(files) {
        const pdfFiles = files.filter(file => FileUtils.getFileExtension(file.name) === 'pdf');

        this.sourceFile.innerHTML = '<option value="">Select source PDF...</option>';
        this.filterSource.innerHTML = '<option value="">All sources</option>';

        pdfFiles.forEach(file => {
            const option = DOM.createElement('option', {
                value: file.id || file.name
            }, file.name);

            this.sourceFile.appendChild(option.cloneNode(true));
            this.filterSource.appendChild(option);
        });
    }

    async createChapter() {
        const title = this.chapterTitle.value.trim();
        const sourceFileId = this.sourceFile.value;
        const startPage = parseInt(this.startPage.value);
        const endPage = parseInt(this.endPage.value);

        // Validation
        if (!title) {
            UI.showToast('Chapter title is required', 'warning');
            return;
        }

        if (!sourceFileId) {
            UI.showToast('Please select a source file', 'warning');
            return;
        }

        if (!startPage || !endPage || startPage < 1 || endPage < startPage) {
            UI.showToast('Please enter valid page numbers', 'warning');
            return;
        }

        try {
            UI.showLoading(this.btnCrop, 'Creating...');

            const formData = new FormData();
            formData.append('title', title);
            formData.append('file_id', sourceFileId);
            formData.append('start_page', startPage);
            formData.append('end_page', endPage);

            const result = await API.post(this.options.cropEndpoint, formData);

            UI.showToast('Chapter created successfully!', 'success');
            this.clearForm();
            this.loadChapters();

        } catch (error) {
            Logger.error('Chapter creation failed:', error);
            UI.showToast('Failed to create chapter: ' + error.message, 'error');
        } finally {
            UI.hideLoading(this.btnCrop, 'Create Chapter');
        }
    }

    async loadChapters() {
        try {
            DOM.show(this.loadingState);
            this.chaptersList.innerHTML = '';

            const response = await API.get(this.options.listEndpoint);
            this.chapters = Array.isArray(response) ? response : (response.chapters || []);

            this.renderChaptersList();
            this.updateBulkActionButtons();

        } catch (error) {
            Logger.error('Failed to load chapters:', error);
            this.chaptersList.innerHTML = `
                <div class="error-state text-center py-8">
                    <p class="text-red-500">Failed to load chapters</p>
                    <button class="btn-retry bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded mt-2">
                        Retry
                    </button>
                </div>
            `;

            this.chaptersList.querySelector('.btn-retry').addEventListener('click', () => {
                this.loadChapters();
            });
        } finally {
            DOM.hide(this.loadingState);
        }
    }

    renderChaptersList() {
        if (this.chapters.length === 0) {
            this.chaptersList.innerHTML = `
                <div class="empty-state text-center py-8">
                    <p class="text-gray-500 mb-4">No chapters found</p>
                    <p class="text-sm text-gray-400">Create your first chapter using the form above</p>
                </div>
            `;
            return;
        }

        const chaptersHTML = this.chapters.map(chapter => this.renderChapterCard(chapter)).join('');
        this.chaptersList.innerHTML = `<div class="chapters-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">${chaptersHTML}</div>`;

        this.setupChapterListeners();
    }

    renderChapterCard(chapter) {
        const isSelected = this.selectedChapters.has(chapter.id);

        return `
            <div class="chapter-card bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${isSelected ? 'ring-2 ring-blue-500' : ''}" data-chapter-id="${chapter.id}">
                <div class="card-header flex items-start justify-between mb-3">
                    <div class="flex items-start">
                        <input type="checkbox" class="chapter-checkbox mt-1 mr-3" ${isSelected ? 'checked' : ''}>
                        <div>
                            <h5 class="font-medium text-gray-800 text-sm">${chapter.title || chapter.filename}</h5>
                            <p class="text-xs text-gray-500">${chapter.source_file || 'Unknown source'}</p>
                        </div>
                    </div>
                    <div class="card-actions flex gap-1">
                        <button class="btn-preview text-blue-500 hover:text-blue-700 text-xs p-1" title="Preview">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                        </button>
                        <button class="btn-download text-green-500 hover:text-green-700 text-xs p-1" title="Download">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                        </button>
                        <button class="btn-delete text-red-500 hover:text-red-700 text-xs p-1" title="Delete">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <div class="card-info space-y-1 text-xs text-gray-600">
                    <div class="flex justify-between">
                        <span>Pages:</span>
                        <span>${chapter.start_page || 'N/A'} - ${chapter.end_page || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Size:</span>
                        <span>${chapter.file_size ? FileUtils.formatFileSize(chapter.file_size) : 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Created:</span>
                        <span>${chapter.created_at ? DateTime.getRelativeTime(chapter.created_at) : 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    setupChapterListeners() {
        // Checkbox listeners
        this.chaptersList.querySelectorAll('.chapter-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const chapterId = e.target.closest('.chapter-card').dataset.chapterId;
                this.toggleChapterSelection(chapterId, e.target.checked);
            });
        });

        // Action button listeners
        this.chaptersList.querySelectorAll('.btn-preview').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chapterId = e.target.closest('.chapter-card').dataset.chapterId;
                this.previewChapter(chapterId);
            });
        });

        this.chaptersList.querySelectorAll('.btn-download').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chapterId = e.target.closest('.chapter-card').dataset.chapterId;
                this.downloadChapter(chapterId);
            });
        });

        this.chaptersList.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chapterId = e.target.closest('.chapter-card').dataset.chapterId;
                this.deleteChapter(chapterId);
            });
        });
    }

    toggleChapterSelection(chapterId, selected) {
        if (selected) {
            this.selectedChapters.add(chapterId);
        } else {
            this.selectedChapters.delete(chapterId);
        }

        // Update card appearance
        const card = this.chaptersList.querySelector(`[data-chapter-id="${chapterId}"]`);
        if (card) {
            if (selected) {
                card.classList.add('ring-2', 'ring-blue-500');
            } else {
                card.classList.remove('ring-2', 'ring-blue-500');
            }
        }

        this.updateBulkActionButtons();
    }

    toggleSelectAll() {
        const allSelected = this.selectedChapters.size === this.chapters.length;

        if (allSelected) {
            // Deselect all
            this.selectedChapters.clear();
            this.chaptersList.querySelectorAll('.chapter-checkbox').forEach(cb => cb.checked = false);
            this.chaptersList.querySelectorAll('.chapter-card').forEach(card => {
                card.classList.remove('ring-2', 'ring-blue-500');
            });
        } else {
            // Select all
            this.chapters.forEach(chapter => this.selectedChapters.add(chapter.id));
            this.chaptersList.querySelectorAll('.chapter-checkbox').forEach(cb => cb.checked = true);
            this.chaptersList.querySelectorAll('.chapter-card').forEach(card => {
                card.classList.add('ring-2', 'ring-blue-500');
            });
        }

        this.updateBulkActionButtons();
    }

    updateBulkActionButtons() {
        const hasSelection = this.selectedChapters.size > 0;

        if (hasSelection) {
            DOM.show(this.btnBulkDownload);
            DOM.show(this.btnBulkDelete);
        } else {
            DOM.hide(this.btnBulkDownload);
            DOM.hide(this.btnBulkDelete);
        }

        // Update select all button text
        const allSelected = this.selectedChapters.size === this.chapters.length;
        this.btnSelectAll.textContent = allSelected ? 'Deselect All' : 'Select All';
    }

    async previewChapter(chapterId) {
        const chapter = this.chapters.find(c => c.id === chapterId);
        if (!chapter) return;

        try {
            this.modalContent.innerHTML = '<div class="text-center py-8">Loading preview...</div>';
            DOM.show(this.previewModal);

            const response = await API.get(`${this.options.browseEndpoint}/${chapterId}`);

            // Display preview content
            this.modalContent.innerHTML = `
                <div class="chapter-preview">
                    <h5 class="text-lg font-medium mb-4">${chapter.title || chapter.filename}</h5>
                    <div class="preview-info grid grid-cols-2 gap-4 mb-4 text-sm">
                        <div><strong>Source:</strong> ${chapter.source_file || 'N/A'}</div>
                        <div><strong>Pages:</strong> ${chapter.start_page} - ${chapter.end_page}</div>
                        <div><strong>Size:</strong> ${chapter.file_size ? FileUtils.formatFileSize(chapter.file_size) : 'N/A'}</div>
                        <div><strong>Created:</strong> ${DateTime.formatDate(chapter.created_at)}</div>
                    </div>
                    <div class="preview-content bg-gray-100 p-4 rounded">
                        ${response.preview || 'Preview not available'}
                    </div>
                </div>
            `;

        } catch (error) {
            Logger.error('Failed to load chapter preview:', error);
            this.modalContent.innerHTML = '<div class="text-center py-8 text-red-500">Failed to load preview</div>';
        }
    }

    closePreviewModal() {
        DOM.hide(this.previewModal);
    }

    async downloadChapter(chapterId) {
        const chapter = this.chapters.find(c => c.id === chapterId);
        if (!chapter) return;

        try {
            const downloadUrl = `${this.options.downloadEndpoint}/${chapterId}`;
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = chapter.filename || `chapter-${chapterId}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            UI.showToast('Chapter download started', 'success');

        } catch (error) {
            Logger.error('Failed to download chapter:', error);
            UI.showToast('Download failed: ' + error.message, 'error');
        }
    }

    async deleteChapter(chapterId) {
        if (!confirm('Are you sure you want to delete this chapter?')) {
            return;
        }

        try {
            await API.delete(`${this.options.deleteEndpoint}/${chapterId}`);

            this.chapters = this.chapters.filter(c => c.id !== chapterId);
            this.selectedChapters.delete(chapterId);

            this.renderChaptersList();
            this.updateBulkActionButtons();

            UI.showToast('Chapter deleted successfully', 'success');

        } catch (error) {
            Logger.error('Failed to delete chapter:', error);
            UI.showToast('Delete failed: ' + error.message, 'error');
        }
    }

    async bulkDownload() {
        if (this.selectedChapters.size === 0) return;

        const selectedIds = Array.from(this.selectedChapters);

        for (const chapterId of selectedIds) {
            await this.downloadChapter(chapterId);
        }

        UI.showToast(`${selectedIds.length} chapters downloaded`, 'success');
    }

    async bulkDelete() {
        if (this.selectedChapters.size === 0) return;

        if (!confirm(`Are you sure you want to delete ${this.selectedChapters.size} chapters?`)) {
            return;
        }

        const selectedIds = Array.from(this.selectedChapters);
        let successCount = 0;

        for (const chapterId of selectedIds) {
            try {
                await API.delete(`${this.options.deleteEndpoint}/${chapterId}`);
                successCount++;
            } catch (error) {
                Logger.error(`Failed to delete chapter ${chapterId}:`, error);
            }
        }

        this.loadChapters();
        UI.showToast(`${successCount} chapters deleted`, 'success');
    }

    filterChapters() {
        const searchTerm = this.searchChapters.value.toLowerCase();
        const sourceFilter = this.filterSource.value;

        const filtered = this.chapters.filter(chapter => {
            const matchesSearch = !searchTerm ||
                (chapter.title && chapter.title.toLowerCase().includes(searchTerm)) ||
                (chapter.filename && chapter.filename.toLowerCase().includes(searchTerm));

            const matchesSource = !sourceFilter || chapter.source_file === sourceFilter;

            return matchesSearch && matchesSource;
        });

        // Re-render with filtered chapters
        const originalChapters = this.chapters;
        this.chapters = filtered;
        this.renderChaptersList();
        this.chapters = originalChapters;
    }

    clearForm() {
        this.chapterTitle.value = '';
        this.sourceFile.value = '';
        this.startPage.value = '';
        this.endPage.value = '';
    }

    // Public API methods
    getChapters() {
        return this.chapters;
    }

    getSelectedChapters() {
        return Array.from(this.selectedChapters);
    }

    clearSelection() {
        this.selectedChapters.clear();
        this.updateBulkActionButtons();
        this.renderChaptersList();
    }

    refresh() {
        this.loadChapters();
    }
}