/**
 * File Upload Component
 * Handles file upload functionality with drag & drop support
 */

import { CONFIG } from '../config.js';
import { API, DOM, FileUtils, UI, Logger } from '../utils.js';

export class FileUploadComponent {
    constructor(containerId, options = {}) {
        this.container = DOM.getElementById(containerId);
        this.options = {
            allowMultiple: false,
            acceptedTypes: CONFIG.UI.ALLOWED_FILE_TYPES,
            maxFileSize: CONFIG.UI.MAX_FILE_SIZE,
            uploadEndpoint: CONFIG.API.ENDPOINTS.UPLOAD_DOCUMENT,
            onUploadStart: null,
            onUploadProgress: null,
            onUploadComplete: null,
            onUploadError: null,
            ...options
        };

        this.currentFiles = [];
        this.init();
    }

    init() {
        if (!this.container) {
            Logger.error('File upload container not found');
            return;
        }

        this.createUploadUI();
        this.setupEventListeners();
        Logger.log('File upload component initialized');
    }

    createUploadUI() {
        this.container.innerHTML = `
            <div class="file-upload-wrapper">
                <div class="drop-zone border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                    <div class="upload-icon mb-4">
                        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <div class="upload-text">
                        <p class="text-lg font-medium text-gray-700 mb-2">Drop files here or click to upload</p>
                        <p class="text-sm text-gray-500">Supports: ${this.options.acceptedTypes.join(', ')}</p>
                        <p class="text-sm text-gray-500">Max size: ${FileUtils.formatFileSize(this.options.maxFileSize)}</p>
                    </div>
                    <input type="file" class="file-input hidden" ${this.options.allowMultiple ? 'multiple' : ''} accept="${this.options.acceptedTypes.join(',')}">
                </div>
                
                <div class="file-list mt-4 hidden"></div>
                
                <div class="upload-progress mt-4 hidden">
                    <div class="progress-bar bg-gray-200 rounded-full h-2">
                        <div class="progress-fill bg-blue-500 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                    <p class="progress-text text-sm text-gray-600 mt-2">Uploading...</p>
                </div>
            </div>
        `;

        // Get references to elements
        this.dropZone = this.container.querySelector('.drop-zone');
        this.fileInput = this.container.querySelector('.file-input');
        this.fileList = this.container.querySelector('.file-list');
        this.progressContainer = this.container.querySelector('.upload-progress');
        this.progressBar = this.container.querySelector('.progress-fill');
        this.progressText = this.container.querySelector('.progress-text');
    }

    setupEventListeners() {
        // Click to upload
        this.dropZone.addEventListener('click', () => {
            this.fileInput.click();
        });

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });

        // Drag and drop events
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('border-blue-500', 'bg-blue-50');
        });

        this.dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('border-blue-500', 'bg-blue-50');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('border-blue-500', 'bg-blue-50');
            this.handleFileSelect(e.dataTransfer.files);
        });
    }

    handleFileSelect(files) {
        const validFiles = Array.from(files).filter(file => {
            if (!FileUtils.isValidFileType(file)) {
                UI.showToast(`Invalid file type: ${file.name}`, 'error');
                return false;
            }

            if (!FileUtils.isValidFileSize(file)) {
                UI.showToast(`File too large: ${file.name}`, 'error');
                return false;
            }

            return true;
        });

        if (validFiles.length === 0) return;

        this.currentFiles = this.options.allowMultiple ? [...this.currentFiles, ...validFiles] : validFiles;
        this.displayFileList();

        if (this.options.autoUpload !== false) {
            this.uploadFiles();
        }
    }

    displayFileList() {
        if (this.currentFiles.length === 0) {
            DOM.hide(this.fileList);
            return;
        }

        DOM.show(this.fileList);
        this.fileList.innerHTML = `
            <h4 class="font-medium text-gray-700 mb-2">Selected Files:</h4>
            <div class="file-items space-y-2">
                ${this.currentFiles.map((file, index) => `
                    <div class="file-item flex items-center justify-between p-3 bg-gray-50 rounded">
                        <div>
                            <span class="font-medium">${file.name}</span>
                            <span class="text-sm text-gray-500 ml-2">(${FileUtils.formatFileSize(file.size)})</span>
                        </div>
                        <button class="remove-file text-red-500 hover:text-red-700" data-index="${index}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;

        // Add remove file listeners
        this.fileList.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                this.removeFile(index);
            });
        });
    }

    removeFile(index) {
        this.currentFiles.splice(index, 1);
        this.displayFileList();
    }

    async uploadFiles() {
        if (this.currentFiles.length === 0) {
            UI.showToast('No files selected', 'warning');
            return;
        }

        try {
            DOM.show(this.progressContainer);
            this.updateProgress(0, 'Preparing upload...');

            if (this.options.onUploadStart) {
                this.options.onUploadStart(this.currentFiles);
            }

            const results = [];

            for (let i = 0; i < this.currentFiles.length; i++) {
                const file = this.currentFiles[i];
                const progress = ((i + 1) / this.currentFiles.length) * 100;

                this.updateProgress(progress, `Uploading ${file.name}...`);

                const result = await this.uploadSingleFile(file);
                results.push(result);
            }

            this.updateProgress(100, 'Upload complete!');

            if (this.options.onUploadComplete) {
                this.options.onUploadComplete(results);
            }

            UI.showToast('Files uploaded successfully!', 'success');
            this.reset();

        } catch (error) {
            Logger.error('Upload failed:', error);

            if (this.options.onUploadError) {
                this.options.onUploadError(error);
            }

            UI.showToast('Upload failed: ' + error.message, 'error');
            DOM.hide(this.progressContainer);
        }
    }

    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        return await API.post(this.options.uploadEndpoint, formData);
    }

    updateProgress(percentage, text) {
        this.progressBar.style.width = `${percentage}%`;
        this.progressText.textContent = text;
    }

    reset() {
        this.currentFiles = [];
        this.fileInput.value = '';
        DOM.hide(this.fileList);

        setTimeout(() => {
            DOM.hide(this.progressContainer);
            this.updateProgress(0, 'Uploading...');
        }, 2000);
    }

    // Public API methods
    getFiles() {
        return this.currentFiles;
    }

    clearFiles() {
        this.reset();
    }

    setOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
    }
} 