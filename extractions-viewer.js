/**
 * Docling Extractions Viewer - Modular JavaScript
 * Handles fetching and displaying extraction data from /list-docling-extracts
 */

class ExtractionsViewer {
    constructor() {
        this.API_BASE = 'http://localhost:8001';
        this.extractionsData = [];
        this.filteredData = [];
        this.initializeElements();
        this.bindEvents();
        this.loadExtractions();
    }

    initializeElements() {
        // Main sections
        this.loadingSection = document.getElementById('loadingSection');
        this.statsSection = document.getElementById('statsSection');
        this.filtersSection = document.getElementById('filtersSection');
        this.extractionsSection = document.getElementById('extractionsSection');
        this.emptyState = document.getElementById('emptyState');
        this.errorState = document.getElementById('errorState');

        // Stats elements
        this.totalExtractions = document.getElementById('totalExtractions');
        this.totalImages = document.getElementById('totalImages');
        this.totalHtmlFiles = document.getElementById('totalHtmlFiles');

        // Filter elements
        this.locationFilter = document.getElementById('locationFilter');
        this.searchInput = document.getElementById('searchInput');
        this.clearFilters = document.getElementById('clearFilters');

        // Grid
        this.extractionsGrid = document.getElementById('extractionsGrid');

        // Buttons
        this.refreshBtn = document.getElementById('refreshBtn');
        this.retryBtn = document.getElementById('retryBtn');

        // Modal
        this.imageBrowserModal = document.getElementById('imageBrowserModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalContent = document.getElementById('modalContent');
        this.closeModal = document.getElementById('closeModal');

        // Toast
        this.toast = document.getElementById('toast');
        this.toastIcon = document.getElementById('toastIcon');
        this.toastMessage = document.getElementById('toastMessage');
        this.toastClose = document.getElementById('toastClose');
    }

    bindEvents() {
        // Button events
        this.refreshBtn.addEventListener('click', () => this.loadExtractions());
        this.retryBtn.addEventListener('click', () => this.loadExtractions());

        // Filter events
        this.locationFilter.addEventListener('change', () => this.applyFilters());
        this.searchInput.addEventListener('input', () => this.applyFilters());
        this.clearFilters.addEventListener('click', () => this.clearAllFilters());

        // Modal events
        this.closeModal.addEventListener('click', () => this.hideModal());
        this.imageBrowserModal.addEventListener('click', (e) => {
            if (e.target === this.imageBrowserModal) {
                this.hideModal();
            }
        });

        // Toast events
        this.toastClose.addEventListener('click', () => this.hideToast());

        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal();
                this.hideToast();
            }
        });
    }

    async loadExtractions() {
        this.showLoading();
        this.hideAllSections();

        try {
            const response = await fetch(`${this.API_BASE}/list-docling-extracts`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.extractionsData = data.extract_folders || [];
            this.filteredData = [...this.extractionsData];

            this.hideLoading();

            if (this.extractionsData.length === 0) {
                this.showEmptyState();
            } else {
                this.updateStats();
                this.renderExtractions();
                this.showMainContent();
                this.showToast('Extractions loaded successfully!', 'success');
            }

        } catch (error) {
            console.error('Error loading extractions:', error);
            this.hideLoading();
            this.showErrorState();
            this.showToast(`Error loading extractions: ${error.message}`, 'error');
        }
    }

    updateStats() {
        const totalImages = this.extractionsData.reduce((sum, folder) => sum + folder.image_count, 0);
        const totalHtmlFiles = this.extractionsData.reduce((sum, folder) => sum + folder.html_files.length, 0);

        this.totalExtractions.textContent = this.extractionsData.length;
        this.totalImages.textContent = totalImages;
        this.totalHtmlFiles.textContent = totalHtmlFiles;
    }

    renderExtractions() {
        this.extractionsGrid.innerHTML = '';

        if (this.filteredData.length === 0) {
            this.extractionsGrid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-search text-4xl text-gray-300 mb-4"></i>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">No Results Found</h3>
                    <p class="text-gray-500">Try adjusting your filters or search terms.</p>
                </div>
            `;
            return;
        }

        this.filteredData.forEach(folder => {
            const card = this.createExtractionCard(folder);
            this.extractionsGrid.appendChild(card);
        });
    }

    createExtractionCard(folder) {
        const card = document.createElement('div');
        card.className = 'extraction-card bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg';

        const locationBadge = folder.location === 'extracted-data' ?
            '<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Extracted Data</span>' :
            '<span class="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">Root</span>';

        card.innerHTML = `
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 truncate">${folder.folder_name}</h3>
                    ${locationBadge}
                </div>
                
                <div class="grid grid-cols-3 gap-4 mb-4 text-center">
                    <div class="bg-blue-50 rounded-lg p-3">
                        <i class="fas fa-images text-blue-600 text-xl mb-1"></i>
                        <p class="text-sm text-gray-600">Images</p>
                        <p class="text-lg font-semibold text-blue-600">${folder.image_count}</p>
                    </div>
                    <div class="bg-purple-50 rounded-lg p-3">
                        <i class="fas fa-file-code text-purple-600 text-xl mb-1"></i>
                        <p class="text-sm text-gray-600">HTML</p>
                        <p class="text-lg font-semibold text-purple-600">${folder.html_files.length}</p>
                    </div>
                    <div class="bg-green-50 rounded-lg p-3">
                        <i class="fas fa-file-text text-green-600 text-xl mb-1"></i>
                        <p class="text-sm text-gray-600">Markdown</p>
                        <p class="text-lg font-semibold text-green-600">${folder.markdown_files.length}</p>
                    </div>
                </div>

                <div class="space-y-2">
                    ${folder.html_files.length > 0 ? `
                        <div class="flex flex-wrap gap-2 mb-3">
                            ${folder.html_files.map(html => `
                                <button onclick="window.open('${this.API_BASE}${html.view_url}', '_blank')" 
                                        class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded-full transition-colors duration-200">
                                    <i class="fas fa-external-link-alt mr-1"></i>
                                    ${html.filename}
                                </button>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="flex flex-wrap gap-2">
                        ${folder.image_count > 0 ? `
                            <button onclick="extractionsViewer.showImageBrowser('${folder.folder_name}', '${folder.folder_path}')" 
                                    class="bg-purple-600 hover:bg-purple-700 text-white text-sm px-3 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-1">
                                <i class="fas fa-images"></i>
                                <span>Browse Images</span>
                            </button>
                        ` : ''}
                        
                        <button onclick="extractionsViewer.showFolderDetails('${folder.folder_name}')" 
                                class="bg-gray-600 hover:bg-gray-700 text-white text-sm px-3 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-1">
                            <i class="fas fa-info-circle"></i>
                            <span>Details</span>
                        </button>
                        
                        ${folder.cropped_pdf ? `
                            <button onclick="extractionsViewer.downloadPDF('${folder.cropped_pdf.download_url}', '${folder.cropped_pdf.filename}')" 
                                    class="bg-red-600 hover:bg-red-700 text-white text-sm px-3 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-1">
                                <i class="fas fa-file-pdf"></i>
                                <span>Download PDF</span>
                            </button>
                        ` : `
                            <button disabled 
                                    class="bg-gray-400 text-white text-sm px-3 py-2 rounded-lg flex items-center space-x-1 cursor-not-allowed">
                                <i class="fas fa-file-pdf"></i>
                                <span>No PDF</span>
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    async showImageBrowser(folderName, folderPath) {
        this.modalTitle.textContent = `${folderName} - Images`;
        this.modalContent.innerHTML = '<div class="flex justify-center py-8"><div class="loading-spinner"></div></div>';
        this.showModal();

        try {
            // Get actual file list from the server
            const response = await fetch(`${this.API_BASE}/list-extraction-files/${encodeURIComponent(folderName)}`);

            if (!response.ok) {
                throw new Error(`Failed to load files: ${response.statusText}`);
            }

            const filesData = await response.json();
            this.renderImageGrid(filesData);

        } catch (error) {
            console.error('Error loading images:', error);
            this.modalContent.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                    <p class="text-gray-600 mb-4">Error loading images: ${error.message}</p>
                    <button onclick="extractionsViewer.showImageBrowser('${folderName}', '${folderPath}')" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
                        Try Again
                    </button>
                </div>
            `;
        }
    }

    renderImageGrid(filesData) {
        const images = filesData.images || [];
        const folder = filesData;

        if (images.length === 0) {
            this.modalContent.innerHTML = `
                <div class="flex items-center justify-center h-full">
                    <div class="text-center">
                        <i class="fas fa-images text-gray-400 text-6xl mb-4"></i>
                        <h3 class="text-xl font-semibold mb-2">${folder.folder_name}</h3>
                        <p class="text-gray-600 mb-4">No images found in this extraction</p>
                        <p class="text-sm text-gray-500">Location: ${folder.folder_path}</p>
                    </div>
                </div>
            `;
            return;
        }

        const imagesGrid = images.map((img, index) => `
            <div class="bg-white rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <div class="relative group">
                    <img src="${img.full_url}" 
                         alt="${img.filename}" 
                         class="w-full h-64 object-contain bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors" 
                         onclick="window.open('${img.full_url}', '_blank')"
                         loading="lazy"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="hidden absolute inset-0 flex items-center justify-center bg-gray-100">
                        <div class="text-center text-gray-500">
                            <i class="fas fa-image text-3xl mb-2"></i>
                            <p class="text-sm">Failed to load</p>
                            <p class="text-xs">${img.filename}</p>
                        </div>
                    </div>
                    <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                        <i class="fas fa-expand text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-2xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <div class="bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                            ${index + 1} of ${images.length}
                        </div>
                    </div>
                </div>
                <div class="p-4">
                    <p class="text-sm font-medium truncate mb-1" title="${img.filename}">${img.filename}</p>
                    <p class="text-xs text-gray-500 mb-3">${this.formatFileSize(img.size)}</p>
                    <div class="flex space-x-2">
                        <button onclick="window.open('${img.full_url}', '_blank')" 
                                class="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded transition-colors">
                            <i class="fas fa-external-link-alt mr-1"></i>Open
                        </button>
                        <button onclick="extractionsViewer.copyImageToClipboard('${img.full_url}', this)" 
                                class="flex-1 text-xs bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded transition-colors">
                            <i class="fas fa-copy mr-1"></i>Copy
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Create small HTML link if available
        const htmlLink = folder.html_files && folder.html_files.length > 0 ?
            `<div class="absolute top-4 left-4 z-10">
                <a href="${folder.html_files[0].full_url}" target="_blank" 
                   class="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-2 rounded-lg shadow-lg transition-colors flex items-center space-x-2">
                    <i class="fas fa-file-code"></i>
                    <span>View with captions</span>
                </a>
            </div>` : '';

        this.modalContent.innerHTML = `
            <div class="h-full flex flex-col relative">
                ${htmlLink}
                
                <div class="flex-1 overflow-y-auto pt-4">
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6">
                        ${imagesGrid}
                    </div>
                </div>
                
                <div class="flex-shrink-0 mt-6 text-center">
                    <div class="bg-gray-50 p-3 rounded-lg inline-block">
                        <p class="text-sm text-gray-500">
                            <i class="fas fa-lightbulb mr-1"></i>
                            <strong>${images.length} images</strong> • Click any image to view full size
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showFolderDetails(folderName) {
        const folder = this.extractionsData.find(f => f.folder_name === folderName);
        if (!folder) return;

        this.modalTitle.textContent = `${folderName} - Details`;
        this.modalContent.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h4 class="font-semibold text-gray-900 mb-2">Folder Information</h4>
                        <dl class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Name:</dt>
                                <dd class="text-gray-900 font-medium">${folder.folder_name}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Location:</dt>
                                <dd class="text-gray-900">${folder.location}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Path:</dt>
                                <dd class="text-gray-900 break-all">${folder.folder_path}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Mount Path:</dt>
                                <dd class="text-gray-900">${folder.mount_path}</dd>
                            </div>
                        </dl>
                    </div>
                    
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h4 class="font-semibold text-gray-900 mb-2">File Counts</h4>
                        <dl class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Images:</dt>
                                <dd class="text-gray-900 font-medium">${folder.image_count}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">HTML Files:</dt>
                                <dd class="text-gray-900 font-medium">${folder.html_files.length}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Markdown Files:</dt>
                                <dd class="text-gray-900 font-medium">${folder.markdown_files.length}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Total Assets:</dt>
                                <dd class="text-gray-900 font-medium">${folder.all_assets.length}</dd>
                            </div>
                        </dl>
                    </div>
                </div>

                ${folder.cropped_pdf ? `
                    <div class="bg-red-50 rounded-lg p-4">
                        <h4 class="font-semibold text-gray-900 mb-3">Cropped PDF Information</h4>
                        <dl class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Section Title:</dt>
                                <dd class="text-gray-900 font-medium">${folder.cropped_pdf.section_title || 'N/A'}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Page Range:</dt>
                                <dd class="text-gray-900 font-medium">${folder.cropped_pdf.page_range || 'N/A'}</dd>
                            </div>
                            <div class="flex justify-between">
                                <dt class="text-gray-600">Filename:</dt>
                                <dd class="text-gray-900 font-medium">${folder.cropped_pdf.filename || 'N/A'}</dd>
                            </div>
                            <div class="mt-3">
                                <button onclick="extractionsViewer.downloadPDF('${folder.cropped_pdf.download_url}', '${folder.cropped_pdf.filename}')" 
                                        class="bg-red-600 hover:bg-red-700 text-white text-sm px-4 py-2 rounded-lg flex items-center space-x-2">
                                    <i class="fas fa-file-pdf"></i>
                                    <span>Download Cropped PDF</span>
                                </button>
                            </div>
                        </dl>
                    </div>
                ` : ''}

                ${folder.html_files.length > 0 ? `
                    <div class="bg-blue-50 rounded-lg p-4">
                        <h4 class="font-semibold text-gray-900 mb-3">HTML Files</h4>
                        <div class="space-y-2">
                            ${folder.html_files.map(html => `
                                <div class="flex justify-between items-center bg-white rounded p-3">
                                    <span class="text-sm font-medium">${html.filename}</span>
                                    <button onclick="window.open('${this.API_BASE}${html.view_url}', '_blank')" 
                                            class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded">
                                        Open
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${folder.markdown_files.length > 0 ? `
                    <div class="bg-green-50 rounded-lg p-4">
                        <h4 class="font-semibold text-gray-900 mb-3">Markdown Files</h4>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            ${folder.markdown_files.map(md => `
                                <div class="bg-white rounded p-2 text-sm">${md}</div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        this.showModal();
    }

    downloadPDF(url, filename) {
        try {
            // Create a temporary link element and trigger download
            const link = document.createElement('a');
            link.href = `${this.API_BASE}${url}`;
            link.download = filename || 'cropped-section.pdf';
            link.style.display = 'none';

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.showToast(`PDF download started: ${filename || 'cropped-section.pdf'}`, 'success');
        } catch (error) {
            console.error('PDF download error:', error);
            this.showToast('PDF download failed', 'error');
        }
    }

    applyFilters() {
        const location = this.locationFilter.value;
        const search = this.searchInput.value.toLowerCase().trim();

        this.filteredData = this.extractionsData.filter(folder => {
            const matchesLocation = location === 'all' || folder.location === location;
            const matchesSearch = search === '' ||
                folder.folder_name.toLowerCase().includes(search) ||
                folder.html_files.some(html => html.filename.toLowerCase().includes(search)) ||
                folder.markdown_files.some(md => md.toLowerCase().includes(search));

            return matchesLocation && matchesSearch;
        });

        this.renderExtractions();
    }

    clearAllFilters() {
        this.locationFilter.value = 'all';
        this.searchInput.value = '';
        this.applyFilters();
    }

    // UI State Management
    showLoading() {
        this.loadingSection.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingSection.classList.add('hidden');
    }

    showMainContent() {
        this.statsSection.classList.remove('hidden');
        this.filtersSection.classList.remove('hidden');
        this.extractionsSection.classList.remove('hidden');
    }

    showEmptyState() {
        this.emptyState.classList.remove('hidden');
    }

    showErrorState() {
        this.errorState.classList.remove('hidden');
    }

    hideAllSections() {
        this.statsSection.classList.add('hidden');
        this.filtersSection.classList.add('hidden');
        this.extractionsSection.classList.add('hidden');
        this.emptyState.classList.add('hidden');
        this.errorState.classList.add('hidden');
    }

    showModal() {
        this.imageBrowserModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    hideModal() {
        this.imageBrowserModal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    showToast(message, type = 'info') {
        this.toastMessage.textContent = message;

        const iconClass = type === 'success' ? 'fas fa-check-circle text-green-500' :
            type === 'error' ? 'fas fa-exclamation-circle text-red-500' :
                type === 'warning' ? 'fas fa-exclamation-triangle text-yellow-500' :
                    'fas fa-info-circle text-blue-500';

        this.toastIcon.innerHTML = `<i class="${iconClass}"></i>`;
        this.toast.classList.remove('hidden');

        // Auto hide after 4 seconds
        setTimeout(() => {
            this.hideToast();
        }, 4000);
    }

    hideToast() {
        this.toast.classList.add('hidden');
    }

    async copyImageToClipboard(imageUrl, button) {
        // Store original button content
        const originalContent = button.innerHTML;

        try {
            // Update button to show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Copying...';
            button.disabled = true;

            // Fetch the image
            const response = await fetch(imageUrl);
            if (!response.ok) {
                throw new Error('Failed to fetch image');
            }

            const blob = await response.blob();

            // Check if the browser supports clipboard API for images
            if (!navigator.clipboard || !navigator.clipboard.write) {
                throw new Error('Clipboard API not supported');
            }

            // Create clipboard item with the image
            const clipboardItem = new ClipboardItem({
                [blob.type]: blob
            });

            // Write to clipboard
            await navigator.clipboard.write([clipboardItem]);

            // Show success state
            button.innerHTML = '<i class="fas fa-check mr-1"></i>Copied!';
            button.className = button.className.replace('bg-gray-600 hover:bg-gray-700', 'bg-green-600');

            this.showToast('Image copied to clipboard!', 'success');

            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalContent;
                button.className = button.className.replace('bg-green-600', 'bg-gray-600 hover:bg-gray-700');
                button.disabled = false;
            }, 2000);

        } catch (error) {
            console.error('Error copying image to clipboard:', error);

            // Fallback: copy URL instead
            try {
                await navigator.clipboard.writeText(imageUrl);
                button.innerHTML = '<i class="fas fa-link mr-1"></i>URL Copied';
                this.showToast('Image copy not supported, URL copied instead', 'warning');
            } catch (urlError) {
                button.innerHTML = '<i class="fas fa-times mr-1"></i>Failed';
                this.showToast('Failed to copy image or URL', 'error');
            }

            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalContent;
                button.disabled = false;
            }, 2000);
        }
    }
}

// Initialize the viewer when the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    window.extractionsViewer = new ExtractionsViewer();
});

// Export for use in HTML onclick handlers
window.ExtractionsViewer = ExtractionsViewer; 