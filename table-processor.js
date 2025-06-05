// Table Processor JavaScript
let selectedFile = null;
let processingOptions = {
    generateCSV: true,
    generateHTML: true,
    generateMarkdown: true
};

// DOM Elements
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const dropzone = document.getElementById('dropzone');
const uploadProgress = document.getElementById('uploadProgress');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const processBtn = document.getElementById('processBtn');
const resultsSection = document.getElementById('resultsSection');
const processingStatus = document.getElementById('processingStatus');
const downloadSection = document.getElementById('downloadSection');
const downloadLinks = document.getElementById('downloadLinks');
const previewSection = document.getElementById('previewSection');
const tablePreview = document.getElementById('tablePreview');
const markdownSection = document.getElementById('markdownSection');
const markdownPreview = document.getElementById('markdownPreview');
const copyMarkdown = document.getElementById('copyMarkdown');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');

// Toast notification elements
const toast = document.getElementById('toast');
const toastIcon = document.getElementById('toastIcon');
const toastMessage = document.getElementById('toastMessage');
const toastClose = document.getElementById('toastClose');

// Checkboxes
const generateCSV = document.getElementById('generateCSV');
const generateHTML = document.getElementById('generateHTML');
const generateMarkdown = document.getElementById('generateMarkdown');

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
});

function initializeEventListeners() {
    // File input events
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop events
    dropzone.addEventListener('dragover', handleDragOver);
    dropzone.addEventListener('dragleave', handleDragLeave);
    dropzone.addEventListener('drop', handleDrop);

    // Process button
    processBtn.addEventListener('click', processTableImage);

    // Copy markdown button
    copyMarkdown.addEventListener('click', copyMarkdownToClipboard);

    // Toast close button
    toastClose.addEventListener('click', hideToast);

    // Checkbox event listeners
    generateCSV.addEventListener('change', updateProcessingOptions);
    generateHTML.addEventListener('change', updateProcessingOptions);
    generateMarkdown.addEventListener('change', updateProcessingOptions);
}

function updateProcessingOptions() {
    processingOptions.generateCSV = generateCSV.checked;
    processingOptions.generateHTML = generateHTML.checked;
    processingOptions.generateMarkdown = generateMarkdown.checked;
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    dropzone.classList.add('border-primary', 'border-solid');
    dropzone.classList.remove('border-dashed');
}

function handleDragLeave(event) {
    event.preventDefault();
    dropzone.classList.remove('border-primary', 'border-solid');
    dropzone.classList.add('border-dashed');
}

function handleDrop(event) {
    event.preventDefault();
    dropzone.classList.remove('border-primary', 'border-solid');
    dropzone.classList.add('border-dashed');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        validateAndSetFile(files[0]);
    }
}

function validateAndSetFile(file) {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!allowedTypes.includes(file.type)) {
        showToast('Please select a PNG, JPEG, or PDF file.', 'error');
        return;
    }

    if (file.size > maxSize) {
        showToast('File size must be less than 50MB.', 'error');
        return;
    }

    selectedFile = file;
    processBtn.disabled = false;
    showToast(`File selected: ${file.name}`, 'success');

    // Update UI to show selected file
    const fileInfo = dropzone.querySelector('.flex-col');
    fileInfo.innerHTML = `
        <svg class="w-12 h-12 text-green-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <p class="text-lg text-green-600 mb-2">File ready for processing</p>
        <p class="text-sm text-gray-600 font-medium">${file.name}</p>
        <p class="text-xs text-gray-500">${formatFileSize(file.size)}</p>
        <button type="button" id="changeBrowseBtn" 
            class="mt-4 bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 transition-colors duration-200">
            Change File
        </button>
    `;

    // Re-attach event listener for change file button
    document.getElementById('changeBrowseBtn').addEventListener('click', () => {
        fileInput.value = '';
        selectedFile = null;
        processBtn.disabled = true;
        resetDropzone();
    });
}

function resetDropzone() {
    const fileInfo = dropzone.querySelector('.flex-col');
    fileInfo.innerHTML = `
        <svg class="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z">
            </path>
        </svg>
        <p class="text-lg text-gray-600 mb-2">Drop your table image here or click to browse</p>
        <p class="text-sm text-gray-500">Supports PNG, JPG, JPEG, and PDF files</p>
        <input type="file" id="fileInput" accept=".png,.jpg,.jpeg,.pdf" class="hidden">
        <button type="button" id="browseBtn"
            class="mt-4 bg-primary text-white px-6 py-2 rounded-md hover:bg-blue-600 transition-colors duration-200">
            Browse Files
        </button>
    `;

    // Re-initialize event listeners
    document.getElementById('browseBtn').addEventListener('click', () => document.getElementById('fileInput').click());
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
}

async function processTableImage() {
    if (!selectedFile) {
        showToast('Please select a file first.', 'error');
        return;
    }

    showLoading('Processing table image with Docling...');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('generate_csv', processingOptions.generateCSV);
    formData.append('generate_html', processingOptions.generateHTML);
    formData.append('generate_markdown', processingOptions.generateMarkdown);

    try {
        const response = await fetch('/process-table/', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            displayResults(result);
            showToast('Table processing completed successfully!', 'success');
        } else {
            throw new Error(result.message || 'Processing failed');
        }
    } catch (error) {
        console.error('Error processing table:', error);
        showToast(`Error: ${error.message}`, 'error');
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

function displayResults(result) {
    resultsSection.classList.remove('hidden');

    // Display processing status
    processingStatus.innerHTML = `
        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
            <div class="flex items-center">
                <svg class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                <div>
                    <h4 class="text-green-800 font-semibold">Processing Completed</h4>
                    <p class="text-green-700 text-sm">Tables extracted: ${result.tables_found || 0}</p>
                    <p class="text-green-700 text-sm">Processing time: ${result.processing_time || 'N/A'}</p>
                </div>
            </div>
        </div>
    `;

    // Display download links
    if (result.files && result.files.length > 0) {
        downloadSection.classList.remove('hidden');
        downloadLinks.innerHTML = '';

        result.files.forEach(file => {
            const downloadCard = document.createElement('div');
            downloadCard.className = 'bg-gray-50 border border-gray-200 rounded-lg p-4 text-center';
            downloadCard.innerHTML = `
                <div class="mb-2">
                    <i class="fas ${getFileIcon(file.type)} text-2xl text-gray-600"></i>
                </div>
                <p class="text-sm font-medium text-gray-800 mb-1">${file.filename}</p>
                <p class="text-xs text-gray-600 mb-3">${file.type.toUpperCase()}</p>
                <a href="${file.url}" download="${file.filename}"
                   class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors duration-200">
                    <i class="fas fa-download mr-1"></i>
                    Download
                </a>
            `;
            downloadLinks.appendChild(downloadCard);
        });
    }

    // Display table preview if available
    if (result.tables && result.tables.length > 0) {
        previewSection.classList.remove('hidden');
        displayTablePreview(result.tables[0]); // Show first table
    }

    // Display markdown preview if available
    if (result.markdown_content) {
        markdownSection.classList.remove('hidden');
        markdownPreview.textContent = result.markdown_content;
    }
}

function displayTablePreview(tableData) {
    if (tableData.html) {
        tablePreview.innerHTML = tableData.html;
    } else if (tableData.csv) {
        // Convert CSV to basic HTML table for preview
        const lines = tableData.csv.split('\n');
        let htmlTable = '<table class="min-w-full border-collapse border border-gray-300">';

        lines.forEach((line, index) => {
            if (line.trim()) {
                const cells = line.split(',');
                const tag = index === 0 ? 'th' : 'td';
                const rowClass = index === 0 ? 'bg-gray-100' : '';

                htmlTable += `<tr class="${rowClass}">`;
                cells.forEach(cell => {
                    htmlTable += `<${tag} class="border border-gray-300 px-2 py-1 text-sm">${cell.trim()}</${tag}>`;
                });
                htmlTable += '</tr>';
            }
        });

        htmlTable += '</table>';
        tablePreview.innerHTML = htmlTable;
    }
}

function displayError(errorMessage) {
    resultsSection.classList.remove('hidden');
    processingStatus.innerHTML = `
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-center">
                <svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                </svg>
                <div>
                    <h4 class="text-red-800 font-semibold">Processing Failed</h4>
                    <p class="text-red-700 text-sm">${errorMessage}</p>
                </div>
            </div>
        </div>
    `;
}

function copyMarkdownToClipboard() {
    const markdownText = markdownPreview.textContent;
    navigator.clipboard.writeText(markdownText).then(() => {
        showToast('Markdown copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy markdown:', err);
        showToast('Failed to copy markdown to clipboard.', 'error');
    });
}

function getFileIcon(fileType) {
    switch (fileType.toLowerCase()) {
        case 'csv':
            return 'fa-file-csv';
        case 'html':
            return 'fa-file-code';
        case 'markdown':
        case 'md':
            return 'fa-file-alt';
        default:
            return 'fa-file';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(message = 'Processing...') {
    loadingText.textContent = message;
    loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

function showToast(message, type = 'success') {
    toastMessage.textContent = message;

    // Update icon based on type
    if (type === 'success') {
        toastIcon.innerHTML = `
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        `;
        toastIcon.className = 'h-5 w-5 text-green-500';
    } else if (type === 'error') {
        toastIcon.innerHTML = `
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
        `;
        toastIcon.className = 'h-5 w-5 text-red-500';
    }

    toast.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideToast();
    }, 5000);
}

function hideToast() {
    toast.classList.add('hidden');
} 