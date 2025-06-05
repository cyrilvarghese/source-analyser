// Global variables
let currentFileId = null;
let currentDocumentInfo = null;
let allTocItems = [];
let tocHierarchy = [];
let extractedChapters = {}; // Store chapter extractions
const API_BASE = 'http://localhost:8001';

// DOM elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadProgress = document.getElementById('uploadProgress');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const documentInfo = document.getElementById('documentInfo');
const tocSection = document.getElementById('tocSection');
const tocTree = document.getElementById('tocTree');
const cropPanel = document.getElementById('cropPanel');
const loadingOverlay = document.getElementById('loadingOverlay');
const tocSearch = document.getElementById('tocSearch');
const clearSearch = document.getElementById('clearSearch');
const searchResults = document.getElementById('searchResults');

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
    loadExtractedChapters(); // Load any existing chapters
});

function initializeEventListeners() {
    // File upload events
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent event bubbling to dropzone
        fileInput.click();
    });
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop events
    dropzone.addEventListener('dragover', handleDragOver);
    dropzone.addEventListener('drop', handleDrop);
    dropzone.addEventListener('click', (e) => {
        // Only trigger if clicking on dropzone itself, not on the browse button
        if (e.target === dropzone || e.target.closest('#browseBtn') === null) {
            fileInput.click();
        }
    });

    // Search functionality
    tocSearch.addEventListener('input', handleSearch);
    clearSearch.addEventListener('click', clearSearchResults);

    // TOC controls
    document.getElementById('expandAllBtn').addEventListener('click', expandAllTocItems);
    document.getElementById('collapseAllBtn').addEventListener('click', collapseAllTocItems);

    // Crop panel controls
    document.getElementById('cancelCrop').addEventListener('click', hideCropPanel);
    document.getElementById('cropBtn').addEventListener('click', cropSection);
    document.getElementById('startPage').addEventListener('input', updatePageRange);
    document.getElementById('endPage').addEventListener('input', updatePageRange);

    // Add null check for enableExtraction checkbox
    const enableExtractionCheckbox = document.getElementById('enableExtraction');
    if (enableExtractionCheckbox) {
        enableExtractionCheckbox.addEventListener('change', updateCropButtonText);
    }

    // Toast close
    document.getElementById('toastClose').addEventListener('click', hideToast);
}

function handleDragOver(e) {
    e.preventDefault();
    dropzone.classList.add('border-primary', 'bg-blue-50');
}

function handleDrop(e) {
    e.preventDefault();
    dropzone.classList.remove('border-primary', 'bg-blue-50');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
        // Reset the file input to ensure consistency
        resetFileInput();
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
    // Reset the file input so the same file can be selected again
    resetFileInput();
}

function handleFile(file) {
    if (!file.type === 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Please select a PDF file', 'error');
        return;
    }

    uploadFile(file);
}

function resetFileInput() {
    fileInput.value = '';
}

async function uploadFile(file) {
    showUploadProgress();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/upload-document/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();
        currentFileId = result.file_id;
        currentDocumentInfo = result.document_info;

        hideUploadProgress();
        displayDocumentInfo(result);
        displayTOC(result.document_info.toc);
        showToast('Document uploaded successfully!', 'success');

        // Reset file input after successful upload
        resetFileInput();

    } catch (error) {
        hideUploadProgress();
        showToast(`Upload failed: ${error.message}`, 'error');
        console.error('Upload error:', error);

        // Reset file input after failed upload
        resetFileInput();
    }
}

function showUploadProgress() {
    uploadProgress.classList.remove('hidden');
    progressBar.style.width = '0%';

    // Simulate progress (in real app, you'd track actual upload progress)
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 90) {
            progress = 90;
            clearInterval(interval);
        }
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `Uploading... ${Math.round(progress)}%`;
    }, 200);
}

function hideUploadProgress() {
    progressBar.style.width = '100%';
    progressText.textContent = 'Processing complete!';
    setTimeout(() => {
        uploadProgress.classList.add('hidden');
    }, 1000);
}

function displayDocumentInfo(result) {
    document.getElementById('fileName').textContent = result.filename;
    document.getElementById('pageCount').textContent = result.document_info.page_count;
    document.getElementById('docFormat').textContent = result.document_info.is_pdf ? 'PDF' : 'Other';
    document.getElementById('tocCount').textContent = result.document_info.toc.length;

    documentInfo.classList.remove('hidden');
}

function displayTOC(tocEntries) {
    tocTree.innerHTML = '';
    allTocItems = tocEntries; // Store for search

    if (tocEntries.length === 0) {
        tocTree.innerHTML = '<p class="text-gray-500 text-center py-8">No table of contents found in this document.</p>';
        tocSection.classList.remove('hidden');
        return;
    }

    // Group TOC entries by hierarchy
    tocHierarchy = buildTOCHierarchy(tocEntries);
    renderTOCTree(tocHierarchy, tocTree);

    tocSection.classList.remove('hidden');
}

function buildTOCHierarchy(tocEntries) {
    const hierarchy = [];
    const stack = [];

    tocEntries.forEach(entry => {
        const item = { ...entry, children: [] };

        // Find parent based on level
        while (stack.length > 0 && stack[stack.length - 1].level >= item.level) {
            stack.pop();
        }

        if (stack.length === 0) {
            hierarchy.push(item);
        } else {
            stack[stack.length - 1].children.push(item);
        }

        stack.push(item);
    });

    return hierarchy;
}

function renderTOCTree(tocItems, container, level = 0) {
    tocItems.forEach(item => {
        const itemElement = createTOCItem(item, level);
        container.appendChild(itemElement);

        if (item.children.length > 0) {
            const childContainer = document.createElement('div');
            childContainer.className = `toc-children ml-6 mt-2 ${level === 0 ? 'toc-level-0' : ''}`;
            childContainer.dataset.parentId = item.id;
            childContainer.style.display = level === 0 ? 'block' : 'none'; // Collapse by default except top level
            renderTOCTree(item.children, childContainer, level + 1);
            container.appendChild(childContainer);
        }
    });
}

function createTOCItem(item, level) {
    const div = document.createElement('div');
    div.className = 'toc-item group cursor-pointer hover:bg-gray-50 p-2 rounded-md border border-transparent hover:border-gray-200 transition-all duration-200';
    div.dataset.tocId = item.id;
    div.dataset.title = item.title;
    div.dataset.page = item.page_number;
    div.dataset.level = level;

    const hasChildren = item.children && item.children.length > 0;
    const expandIcon = hasChildren ?
        `<button class="expand-btn mr-2 text-gray-400 hover:text-gray-600 transition-colors duration-200" data-expanded="false">
            <svg class="w-4 h-4 transform transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
        </button>` : '<span class="w-6"></span>';

    const pageInfo = item.page_number ? ` (Page ${item.page_number})` : '';

    div.innerHTML = `
        <div class="flex justify-between items-center">
            <div class="flex items-center flex-1">
                ${expandIcon}
                <span class="text-gray-800 font-medium">${item.title}</span>
            </div>
            <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-500">${pageInfo}</span>
                <button class="crop-btn opacity-0 group-hover:opacity-100 bg-primary text-white px-2 py-1 rounded text-xs hover:bg-blue-600 transition-all duration-200">
                    Crop Section
                </button>
            </div>
        </div>
    `;

    // Add expand/collapse functionality
    if (hasChildren) {
        const expandBtn = div.querySelector('.expand-btn');
        expandBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleTocItem(item.id);
        });
    }

    // Add click event for cropping
    const cropBtn = div.querySelector('.crop-btn');
    cropBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showCropPanel(item);
    });

    return div;
}

function toggleTocItem(itemId) {
    const childContainer = document.querySelector(`[data-parent-id="${itemId}"]`);
    const expandBtn = document.querySelector(`[data-toc-id="${itemId}"] .expand-btn`);
    const expandIcon = expandBtn.querySelector('svg');

    if (childContainer) {
        const isExpanded = expandBtn.dataset.expanded === 'true';

        if (isExpanded) {
            childContainer.style.display = 'none';
            expandBtn.dataset.expanded = 'false';
            expandIcon.style.transform = 'rotate(0deg)';
        } else {
            childContainer.style.display = 'block';
            expandBtn.dataset.expanded = 'true';
            expandIcon.style.transform = 'rotate(90deg)';
        }
    }
}

function showCropPanel(tocItem) {
    document.getElementById('sectionTitle').value = tocItem.title;
    const startPage = tocItem.page_number || 1;
    document.getElementById('startPage').value = startPage;

    // Calculate end page with improved logic
    const endPage = calculateEndPage(tocItem, startPage);
    document.getElementById('endPage').value = endPage;

    updatePageRange();
    cropPanel.classList.remove('hidden');
    cropPanel.scrollIntoView({ behavior: 'smooth' });
}

function calculateEndPage(currentItem, startPage) {
    const allTocItems = currentDocumentInfo.toc;
    const currentIndex = allTocItems.findIndex(item => item.id === currentItem.id);
    const currentLevel = currentItem.level;

    // Look for the next TOC item at the same level or higher (less deep)
    let nextSameLevelPage = null;

    for (let i = currentIndex + 1; i < allTocItems.length; i++) {
        const nextItem = allTocItems[i];

        // If we find an item at the same level or higher level (parent/sibling)
        if (nextItem.level <= currentLevel && nextItem.page_number) {
            nextSameLevelPage = nextItem.page_number;
            break;
        }
    }

    let endPage;
    if (nextSameLevelPage && nextSameLevelPage > startPage) {
        // Use the page before the next same-level section
        endPage = nextSameLevelPage - 1;
    } else {
        // No next same-level section found, use document end
        endPage = currentDocumentInfo.page_count;
    }

    // Ensure end page is at least equal to start page
    if (endPage < startPage) {
        // If we still have an invalid range, use a reasonable default
        endPage = Math.min(startPage + 5, currentDocumentInfo.page_count); // Default to 5 pages or document end
    }

    return endPage;
}

function findNextTocPage(currentItem) {
    const allTocItems = currentDocumentInfo.toc;
    const currentIndex = allTocItems.findIndex(item => item.id === currentItem.id);
    const startPage = currentItem.page_number || 1;

    // Look for the next item with a page number greater than current start page
    for (let i = currentIndex + 1; i < allTocItems.length; i++) {
        const nextItem = allTocItems[i];
        if (nextItem.page_number && nextItem.page_number > startPage) {
            return nextItem.page_number;
        }
    }

    return null;
}

function hideCropPanel() {
    cropPanel.classList.add('hidden');
}

function updatePageRange() {
    const startPage = parseInt(document.getElementById('startPage').value) || 1;
    const endPage = parseInt(document.getElementById('endPage').value) || 1;
    const totalPages = currentDocumentInfo.page_count;

    let rangeText = '';
    let isValid = true;

    if (startPage > endPage) {
        rangeText = 'Invalid range: Start page must be ≤ End page';
        isValid = false;
    } else if (startPage < 1) {
        rangeText = 'Invalid range: Start page must be ≥ 1';
        isValid = false;
    } else if (endPage > totalPages) {
        rangeText = `Pages ${startPage} to ${endPage} (Warning: Document has only ${totalPages} pages)`;
        isValid = true; // Still allow cropping, will be handled by backend
    } else {
        const pageCount = endPage - startPage + 1;
        rangeText = `Pages ${startPage} to ${endPage} (${pageCount} page${pageCount === 1 ? '' : 's'})`;
        isValid = true;
    }

    const pageRangeElement = document.getElementById('pageRange');
    pageRangeElement.textContent = rangeText;

    // Update styling based on validity
    if (isValid) {
        pageRangeElement.className = 'text-sm text-gray-600';
    } else {
        pageRangeElement.className = 'text-sm text-red-600 font-medium';
    }

    // Enable/disable crop button based on validity
    const cropBtn = document.getElementById('cropBtn');
    if (isValid && startPage <= endPage && startPage >= 1) {
        cropBtn.disabled = false;
        cropBtn.className = 'bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors duration-200';
    } else {
        cropBtn.disabled = true;
        cropBtn.className = 'bg-gray-400 text-white px-4 py-2 rounded-md cursor-not-allowed';
    }
}

function updateCropButtonText() {
    const enableExtractionCheckbox = document.getElementById('enableExtraction');
    const cropBtnText = document.getElementById('cropBtnText');

    // Add null checks
    if (!enableExtractionCheckbox || !cropBtnText) {
        return;
    }

    const enableExtraction = enableExtractionCheckbox.checked;

    if (enableExtraction) {
        cropBtnText.textContent = 'Crop & Extract';
    } else {
        cropBtnText.textContent = 'Crop Only';
    }
}

async function cropSection() {
    const sectionTitle = document.getElementById('sectionTitle').value;
    const startPage = parseInt(document.getElementById('startPage').value);
    const endPage = parseInt(document.getElementById('endPage').value);

    // Add null check for enableExtraction checkbox
    const enableExtractionCheckbox = document.getElementById('enableExtraction');
    const enableExtraction = enableExtractionCheckbox ? enableExtractionCheckbox.checked : false;
    const skipExtraction = !enableExtraction; // Invert the logic for backend compatibility

    if (!sectionTitle || !startPage || !endPage) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    if (startPage > endPage) {
        showToast('Start page must be less than or equal to end page', 'error');
        return;
    }

    showLoadingOverlay();

    try {
        const formData = new FormData();
        formData.append('file_id', currentFileId);
        formData.append('start_page', startPage);
        formData.append('end_page', endPage);
        formData.append('section_title', sectionTitle);
        formData.append('skip_extraction', skipExtraction);

        const response = await fetch(`${API_BASE}/crop-section/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Crop failed: ${response.statusText}`);
        }

        const result = await response.json();

        hideLoadingOverlay();
        hideCropPanel();

        if (result.success) {
            // Store the extracted chapter
            extractedChapters[result.chapter_id] = result;

            // Show success message with extraction details
            let successMessage = `Section cropped successfully!`;

            if (!enableExtraction) {
                successMessage += `\nImage extraction was skipped (crop only mode).`;
                showToast(successMessage, 'success');

                // For crop-only mode, directly download the PDF
                const downloadUrl = result.cropped_pdf.download_full_url || result.cropped_pdf.download_url;
                if (downloadUrl) {
                    window.open(downloadUrl, '_blank');
                }
            } else if (result.extraction.success) {
                successMessage += `\nExtracted ${result.extraction.total_images} images!`;
                showToast(successMessage, 'success');

                // Show modal with all options for successful extraction
                showExtractionResultModal(result);
            } else {
                successMessage += `\nImage extraction failed: ${result.extraction.error}`;
                showToast(successMessage, 'error');

                // Show modal even for failed extraction to allow download
                showExtractionResultModal(result);
            }

            // Refresh chapters list to show the new chapter
            loadExtractedChapters();
        } else {
            showToast('Crop failed', 'error');
        }

    } catch (error) {
        hideLoadingOverlay();
        showToast(`Crop failed: ${error.message}`, 'error');
        console.error('Crop error:', error);
    }
}

function showLoadingOverlay() {
    loadingOverlay.classList.remove('hidden');
}

function hideLoadingOverlay() {
    loadingOverlay.classList.add('hidden');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');

    toastMessage.textContent = message;

    // Set icon and color based on type
    if (type === 'error') {
        toastIcon.className = 'h-5 w-5 text-red-500';
        toastIcon.innerHTML = '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>';
    } else {
        toastIcon.className = 'h-5 w-5 text-green-500';
        toastIcon.innerHTML = '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>';
    }

    toast.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideToast();
    }, 5000);
}

function hideToast() {
    document.getElementById('toast').classList.add('hidden');
}

function handleSearch() {
    const searchTerm = tocSearch.value.toLowerCase().trim();

    if (searchTerm === '') {
        clearSearchResults();
        return;
    }

    // Show clear button
    clearSearch.classList.remove('hidden');

    // Search through all TOC items
    const results = searchInTocItems(allTocItems, searchTerm);

    // Display search results
    displaySearchResults(results, searchTerm);
}

function searchInTocItems(items, searchTerm) {
    const results = [];

    items.forEach(item => {
        if (item.title.toLowerCase().includes(searchTerm)) {
            results.push(item);
        }
    });

    return results;
}

function displaySearchResults(results, searchTerm) {
    searchResults.innerHTML = '';

    if (results.length === 0) {
        searchResults.innerHTML = `<p class="text-gray-500">No results found for "${searchTerm}"</p>`;
        searchResults.classList.remove('hidden');
        return;
    }

    const resultInfo = document.createElement('p');
    resultInfo.className = 'text-gray-600 mb-2';
    resultInfo.textContent = `Found ${results.length} result${results.length === 1 ? '' : 's'} for "${searchTerm}"`;
    searchResults.appendChild(resultInfo);

    const resultsList = document.createElement('div');
    resultsList.className = 'space-y-1';

    results.forEach(item => {
        const resultElement = createSearchResultItem(item, searchTerm);
        resultsList.appendChild(resultElement);
    });

    searchResults.appendChild(resultsList);
    searchResults.classList.remove('hidden');
}

function createSearchResultItem(item, searchTerm) {
    const div = document.createElement('div');
    div.className = 'search-result-item group cursor-pointer hover:bg-blue-50 p-2 rounded border border-transparent hover:border-blue-200 transition-all duration-200';

    const pageInfo = item.page_number ? ` (Page ${item.page_number})` : '';

    // Highlight search term
    const highlightedTitle = highlightSearchTerm(item.title, searchTerm);

    div.innerHTML = `
        <div class="flex justify-between items-center">
            <div class="flex items-center flex-1">
                <span class="text-gray-700">${highlightedTitle}</span>
            </div>
            <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-500">${pageInfo}</span>
                <button class="crop-btn opacity-0 group-hover:opacity-100 bg-primary text-white px-2 py-1 rounded text-xs hover:bg-blue-600 transition-all duration-200">
                    Crop
                </button>
            </div>
        </div>
    `;

    // Add click events
    div.addEventListener('click', () => {
        scrollToTocItem(item.id);
    });

    const cropBtn = div.querySelector('.crop-btn');
    cropBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showCropPanel(item);
    });

    return div;
}

function highlightSearchTerm(text, searchTerm) {
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');
}

function scrollToTocItem(itemId) {
    const tocItem = document.querySelector(`[data-toc-id="${itemId}"]`);
    if (tocItem) {
        // Expand parent containers if needed
        expandParentsOfItem(itemId);

        // Scroll to item
        tocItem.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Highlight temporarily
        tocItem.classList.add('bg-yellow-100', 'border-yellow-300');
        setTimeout(() => {
            tocItem.classList.remove('bg-yellow-100', 'border-yellow-300');
        }, 2000);
    }
}

function expandParentsOfItem(itemId) {
    // Find and expand all parent containers for the item
    let currentElement = document.querySelector(`[data-toc-id="${itemId}"]`);

    while (currentElement) {
        const parentContainer = currentElement.closest('.toc-children');
        if (parentContainer) {
            const parentId = parentContainer.dataset.parentId;
            if (parentId) {
                const parentExpandBtn = document.querySelector(`[data-toc-id="${parentId}"] .expand-btn`);
                if (parentExpandBtn && parentExpandBtn.dataset.expanded === 'false') {
                    toggleTocItem(parentId);
                }
            }
        }
        currentElement = parentContainer;
    }
}

function clearSearchResults() {
    tocSearch.value = '';
    clearSearch.classList.add('hidden');
    searchResults.classList.add('hidden');
    searchResults.innerHTML = '';
}

function expandAllTocItems() {
    const expandBtns = tocTree.querySelectorAll('.expand-btn');
    expandBtns.forEach(btn => {
        if (btn.dataset.expanded === 'false') {
            const itemId = btn.closest('[data-toc-id]').dataset.tocId;
            toggleTocItem(itemId);
        }
    });
}

function collapseAllTocItems() {
    const expandBtns = tocTree.querySelectorAll('.expand-btn');
    expandBtns.forEach(btn => {
        if (btn.dataset.expanded === 'true') {
            const itemId = btn.closest('[data-toc-id]').dataset.tocId;
            toggleTocItem(itemId);
        }
    });
}

async function loadExtractedChapters() {
    // Load previously extracted chapters from the server.
    try {
        const response = await fetch(`${API_BASE}/list-chapters`);
        if (response.ok) {
            const result = await response.json();
            extractedChapters = {};

            // Convert array to object for easier access
            result.chapters.forEach(chapter => {
                extractedChapters[chapter.chapter_id] = chapter;
            });

            // Display chapters if any exist
            if (result.chapters.length > 0) {
                displayExtractedChapters(result.chapters);
            }
        }
    } catch (error) {
        console.error('Error loading extracted chapters:', error);
    }
}

function displayExtractedChapters(chapters) {
    // Display extracted chapters in a dedicated section.
    // Create or update chapters section
    let chaptersSection = document.getElementById('chaptersSection');
    if (!chaptersSection) {
        chaptersSection = document.createElement('div');
        chaptersSection.id = 'chaptersSection';
        chaptersSection.className = 'mt-8';

        // Insert after document info section
        const documentInfoSection = document.getElementById('documentInfo');
        // if (documentInfoSection) {
        //     documentInfoSection.parentNode.insertBefore(chaptersSection, documentInfoSection.nextSibling);
        // } else {
        //     document.body.appendChild(chaptersSection);
        // }
    }

    chaptersSection.innerHTML = `
        <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-xl font-semibold text-gray-800 mb-4">Extracted Chapters (${chapters.length})</h3>
            <div class="space-y-4" id="chaptersList">
                ${chapters.map(chapter => createChapterCard(chapter)).join('')}
            </div>
        </div>
    `;

    // Add event listeners for chapter actions
    addChapterEventListeners();
}

function createChapterCard(chapter) {
    // Create HTML for a chapter card.
    const statusBadge = chapter.extraction_success ?
        '<span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">Extracted</span>' :
        '<span class="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">Failed</span>';

    const htmlUrl = chapter.html_url || (chapter.extraction_result && chapter.extraction_result.html_full_url);
    const downloadUrl = chapter.download_full_url || chapter.download_url;

    const actionButtons = chapter.extraction_success ? `
        <div class="flex space-x-2">
            ${chapter.html_available ? `<button class="view-html-btn bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600" data-chapter-id="${chapter.chapter_id}" data-html-url="${htmlUrl}">View HTML</button>` : ''}
            <button class="browse-images-btn bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600" data-chapter-id="${chapter.chapter_id}">Browse Images (${chapter.total_images})</button>
            <button class="download-pdf-btn bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600" data-chapter-id="${chapter.chapter_id}" data-download-url="${downloadUrl}">Download PDF</button>
            <button class="delete-chapter-btn bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600" data-chapter-id="${chapter.chapter_id}">Delete</button>
        </div>
    ` : `
        <div class="flex space-x-2">
            <button class="download-pdf-btn bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600" data-chapter-id="${chapter.chapter_id}" data-download-url="${downloadUrl}">Download PDF</button>
            <button class="delete-chapter-btn bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600" data-chapter-id="${chapter.chapter_id}">Delete</button>
        </div>
    `;

    return `
        <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <h4 class="font-medium text-gray-800">${chapter.section_title}</h4>
                    <p class="text-sm text-gray-600">Pages ${chapter.page_range}</p>
                    <div class="mt-2">${statusBadge}</div>
                </div>
                <div class="ml-4">
                    ${actionButtons}
                </div>
            </div>
        </div>
    `;
}

function addChapterEventListeners() {
    // Add event listeners for chapter action buttons.
    // View HTML buttons
    document.querySelectorAll('.view-html-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const htmlUrl = e.target.dataset.htmlUrl;
            window.open(htmlUrl, '_blank');
        });
    });

    // Browse images buttons
    document.querySelectorAll('.browse-images-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const chapterId = e.target.dataset.chapterId;
            browseChapterImages(chapterId);
        });
    });

    // Download PDF buttons
    document.querySelectorAll('.download-pdf-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const downloadUrl = e.target.dataset.downloadUrl;
            window.open(downloadUrl, '_blank');
        });
    });

    // Delete chapter buttons
    document.querySelectorAll('.delete-chapter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const chapterId = e.target.dataset.chapterId;
            deleteChapter(chapterId);
        });
    });
}

async function browseChapterImages(chapterId) {
    // Display images from a chapter in a modal.
    try {
        const response = await fetch(`${API_BASE}/browse-chapter/${chapterId}`);
        if (!response.ok) {
            throw new Error('Failed to load chapter details');
        }

        const chapterData = await response.json();
        const images = chapterData.extraction_result.images;

        // Create and show image browser modal
        showImageBrowserModal(chapterData.section_title, images);

    } catch (error) {
        showToast(`Error loading images: ${error.message}`, 'error');
    }
}

function showImageBrowserModal(sectionTitle, images) {
    // Show a modal with image browser.
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50';
    modal.onclick = (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    };

    const imagesGrid = images.length > 0 ?
        images.map(img => `
            <div class="bg-white rounded-lg overflow-hidden shadow-md">
                <img src="${img.url}" alt="${img.filename}" class="w-full h-48 object-cover cursor-pointer" onclick="window.open('${img.url}', '_blank')">
                <div class="p-2">
                    <p class="text-sm font-medium truncate">${img.filename}</p>
                    <p class="text-xs text-gray-500">${formatFileSize(img.size)}</p>
                </div>
            </div>
        `).join('') :
        '<p class="text-gray-500 col-span-full text-center py-8">No images found</p>';

    modal.innerHTML = `
        <div class="bg-white rounded-lg max-w-6xl max-h-5/6 overflow-hidden">
            <div class="p-4 border-b border-gray-200">
                <div class="flex justify-between items-center">
                    <h3 class="text-lg font-semibold">${sectionTitle} - Images (${images.length})</h3>
                    <button class="text-gray-500 hover:text-gray-700" onclick="document.body.removeChild(this.closest('.fixed'))">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="p-4 overflow-auto max-h-96">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    ${imagesGrid}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

async function deleteChapter(chapterId) {
    // Delete a chapter and refresh the list.
    if (!confirm('Are you sure you want to delete this chapter? This will remove all extracted files.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/delete-chapter/${chapterId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Chapter deleted successfully', 'success');
            // Remove from local storage
            delete extractedChapters[chapterId];
            // Reload chapters list
            loadExtractedChapters();
        } else {
            throw new Error('Failed to delete chapter');
        }
    } catch (error) {
        showToast(`Error deleting chapter: ${error.message}`, 'error');
    }
}

function formatFileSize(bytes) {
    // Format file size in human readable format.
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showExtractionResultModal(result) {
    // Show a modal with extraction results and quick actions.
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50';

    const extractionStatus = result.extraction.success ?
        `<div class="text-green-600 mb-4">
            <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <p>Successfully extracted ${result.extraction.total_images} images!</p>
        </div>` :
        `<div class="text-red-600 mb-4">
            <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <p>Image extraction failed: ${result.extraction.error}</p>
        </div>`;

    const htmlViewUrl = result.extraction.html_full_url || result.extraction.html_url;
    const downloadUrl = result.cropped_pdf.download_full_url || result.cropped_pdf.download_url;

    const actionButtons = result.extraction.success ? `
        <div class="flex flex-wrap gap-2 justify-center">
            ${htmlViewUrl ? `<button class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600" onclick="window.open('${htmlViewUrl}', '_blank')">View HTML</button>` : ''}
            <button class="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600" onclick="browseChapterImages('${result.chapter_id}')">Browse Images</button>
            <button class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600" onclick="window.open('${downloadUrl}', '_blank')">Download PDF</button>
        </div>
    ` : `
        <div class="flex justify-center">
            <button class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600" onclick="window.open('${downloadUrl}', '_blank')">Download PDF</button>
        </div>
    `;

    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full text-center">
            <h3 class="text-lg font-semibold mb-4">${result.section_title}</h3>
            <p class="text-gray-600 mb-4">Pages ${result.page_range}</p>
            
            ${extractionStatus}
            
            ${actionButtons}
            
            <button class="mt-4 text-gray-500 hover:text-gray-700" onclick="document.body.removeChild(this.closest('.fixed'))">
                Close
            </button>
        </div>
    `;

    modal.onclick = (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    };

    document.body.appendChild(modal);
} 