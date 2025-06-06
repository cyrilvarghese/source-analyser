/**
 * Master Case Library - JavaScript functionality
 * Handles loading, displaying, and managing generated master case documents
 */

// Global state
let masterCases = [];
let filteredCases = [];
let currentPreviewCase = null;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function () {
    console.log('📚 Master Case Library initialized');
    loadMasterCases();

    // Setup event listeners
    setupEventListeners();
});

/**
 * Setup event listeners for search, filters, etc.
 */
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('input', handleSearch);
}

/**
 * Load master cases from the backend
 */
async function loadMasterCases() {
    const loading = document.getElementById('loading');
    const content = document.getElementById('caseLibraryContent');
    const emptyState = document.getElementById('emptyState');

    try {
        loading.classList.remove('hidden');
        content.classList.add('hidden');
        emptyState.classList.add('hidden');

        // Fetch master cases from backend
        const response = await fetch('/api/master-cases/list/');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Store topics and flatten cases for filtering
            window.masterCaseTopics = result.topics || {};
            masterCases = [];

            // Flatten all cases from topics
            Object.values(result.topics || {}).forEach(topicCases => {
                masterCases.push(...topicCases);
            });

            filteredCases = [...masterCases];

            if (masterCases.length === 0) {
                emptyState.classList.remove('hidden');
            } else {
                renderCaseLibrary(result.topics);
                content.classList.remove('hidden');
            }

            updateStatistics(result.stats);
        } else {
            throw new Error(result.message || 'Failed to load master cases');
        }

    } catch (error) {
        console.error('Error loading master cases:', error);
        showError('Failed to load master cases: ' + error.message);
        emptyState.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

/**
 * Render the case library grouped by topics in table format
 */
function renderCaseLibrary(topicsData = null) {
    const content = document.getElementById('caseLibraryContent');

    // Use provided topics data or group filtered cases
    let topicsToRender = topicsData || {};

    if (!topicsData) {
        // Group filtered cases by topic if no topics data provided
        const topicsMap = new Map();
        filteredCases.forEach(caseItem => {
            const topicName = caseItem.topic || 'Uncategorized';
            if (!topicsMap.has(topicName)) {
                topicsMap.set(topicName, []);
            }
            topicsMap.get(topicName).push(caseItem);
        });
        topicsToRender = Object.fromEntries(topicsMap.entries());
    }

    // Sort topics alphabetically
    const sortedTopics = Object.entries(topicsToRender).sort((a, b) => a[0].localeCompare(b[0]));

    let html = '';

    sortedTopics.forEach(([topicName, cases]) => {
        const topicId = sanitizeTopicName(topicName);
        const generatedCount = cases.filter(c => c.status === 'generated').length;
        const failedCount = cases.filter(c => c.status === 'failed').length;
        const pendingCount = cases.filter(c => c.status === 'pending').length;
        const totalCases = cases.length;

        html += `
            <div class="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
                <!-- Topic Header -->
                <div class="bg-slate-50 border-b border-slate-200 p-4">
                                            <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <input type="checkbox" 
                                   id="selectAll-${topicId}" 
                                   onchange="toggleSelectAllTopic('${topicId}')"
                                   class="w-4 h-4 text-stone-600 bg-gray-100 border-gray-300 rounded focus:ring-stone-500 focus:ring-2"
                                   title="Select All Cases">
                            <h2 class="text-xl font-semibold text-slate-800">${escapeHtml(topicName)}</h2>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button id="uploadMasterCases-${topicId}" 
                                    onclick="uploadMasterCases('${topicId}')" 
                                    class="bg-stone-600 hover:bg-stone-700 text-white px-3 py-1 rounded text-sm hidden">
                                <i class="fas fa-upload mr-1"></i>Upload Master Cases
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Cases Table -->
                <div id="cases-${topicId}" class="overflow-hidden">
                    <div class="bg-slate-50 border-b border-slate-200">
                        <div class="grid grid-cols-8 gap-4 p-3 text-sm font-medium text-slate-700 uppercase tracking-wide">
                            <div class="col-span-1 text-center">SELECT</div>
                            <div class="col-span-3">CASE TITLE</div>
                            <div class="col-span-2">CREATED</div>
                            <div class="col-span-2 text-center">ACTIONS</div>
                        </div>
                    </div>
                    ${cases.map(caseItem => renderCaseTableRow(caseItem)).join('')}
                </div>
            </div>
        `;
    });

    content.innerHTML = html;
}

/**
 * Render individual case table row
 */
function renderCaseTableRow(caseItem) {
    const statusColors = {
        'generated': 'bg-green-100 text-green-700',
        'failed': 'bg-red-100 text-red-700',
        'pending': 'bg-yellow-100 text-yellow-700'
    };

    const statusIcons = {
        'generated': 'fas fa-check-circle',
        'failed': 'fas fa-exclamation-triangle',
        'pending': 'fas fa-clock'
    };

    return `
        <div class="border-b border-slate-200 hover:bg-slate-50 transition-colors duration-200 case-row" 
             data-case-id="${caseItem.id}" data-topic="${caseItem.topic}">
            <div class="grid grid-cols-8 gap-4 p-4 items-center">
                <!-- Checkbox -->
                <div class="col-span-1 text-center">
                    <input type="checkbox" 
                           class="case-checkbox w-4 h-4 text-stone-600 bg-gray-100 border-gray-300 rounded focus:ring-stone-500 focus:ring-2"
                           data-case-id="${caseItem.id}" 
                           data-topic-id="${sanitizeTopicName(caseItem.topic)}"
                           onchange="updateSelectAllState('${sanitizeTopicName(caseItem.topic)}')">
                </div>
                
                <!-- Case Title -->
                <div class="col-span-3">
                    <div class="font-medium text-slate-800 text-sm leading-tight">
                        ${escapeHtml(caseItem.title)}
                    </div>
                    ${caseItem.file_size ? `
                        <div class="text-xs text-slate-500 mt-1">
                            <i class="fas fa-file mr-1"></i>${formatFileSize(caseItem.file_size)}
                        </div>
                    ` : ''}
                </div>
                
                <!-- Created Date -->
                <div class="col-span-2">
                    <div class="text-sm text-slate-600">
                        ${formatDate(caseItem.created_at)}
                    </div>
                </div>
                
                <!-- Actions -->
                <div class="col-span-2 text-center">
                    <button onclick="uploadMasterCases('${caseItem.id}')" 
                            class="bg-stone-600 hover:bg-stone-700 text-white px-3 py-1 rounded text-sm" 
                            title="Upload Master Case">
                        Upload Master Case
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Update statistics in the header cards (deprecated - cards removed)
 */
function updateStatistics(stats = null) {
    // Statistics cards were removed from the UI
    // This function is kept for compatibility but does nothing
    console.log('Statistics cards removed - no longer updating UI elements');
}

/**
 * Handle search functionality
 */
function handleSearch() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    applyFilters(searchTerm);
}

/**
 * Apply search criteria
 */
function applyFilters(searchTerm) {
    // Filter cases
    filteredCases = masterCases.filter(caseItem => {
        // Search filter
        const matchesSearch = !searchTerm ||
            (caseItem.title && caseItem.title.toLowerCase().includes(searchTerm)) ||
            (caseItem.topic && caseItem.topic.toLowerCase().includes(searchTerm)) ||
            (caseItem.disease_name && caseItem.disease_name.toLowerCase().includes(searchTerm));

        return matchesSearch;
    });

    // Group filtered cases by topic for rendering
    const filteredTopics = {};
    filteredCases.forEach(caseItem => {
        const topicName = caseItem.topic || 'Uncategorized';
        if (!filteredTopics[topicName]) {
            filteredTopics[topicName] = [];
        }
        filteredTopics[topicName].push(caseItem);
    });

    renderCaseLibrary(filteredTopics);
}

/**
 * Toggle visibility of cases under a topic
 */
function toggleTopicCases(topicId) {
    const casesContainer = document.getElementById(`cases-${topicId}`);
    const toggleIcon = document.getElementById(`toggle-${topicId}`);

    if (casesContainer.style.display === 'none') {
        casesContainer.style.display = 'block';
        toggleIcon.className = 'fas fa-chevron-down';
    } else {
        casesContainer.style.display = 'none';
        toggleIcon.className = 'fas fa-chevron-right';
    }
}

/**
 * Toggle select all checkboxes for a topic
 */
function toggleSelectAllTopic(topicId) {
    const selectAllCheckbox = document.getElementById(`selectAll-${topicId}`);
    const caseCheckboxes = document.querySelectorAll(`input[data-topic-id="${topicId}"]`);
    const uploadButton = document.getElementById(`uploadMasterCases-${topicId}`);

    caseCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });

    // Show/hide upload button based on select all state
    if (selectAllCheckbox.checked) {
        uploadButton.classList.remove('hidden');
    } else {
        uploadButton.classList.add('hidden');
    }
}

/**
 * Update the select all checkbox state based on individual selections
 */
function updateSelectAllState(topicId) {
    const selectAllCheckbox = document.getElementById(`selectAll-${topicId}`);
    const caseCheckboxes = document.querySelectorAll(`input[data-topic-id="${topicId}"]`);
    const checkedBoxes = document.querySelectorAll(`input[data-topic-id="${topicId}"]:checked`);
    const uploadButton = document.getElementById(`uploadMasterCases-${topicId}`);

    if (checkedBoxes.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
        uploadButton.classList.add('hidden');
    } else if (checkedBoxes.length === caseCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
        uploadButton.classList.remove('hidden');
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
        uploadButton.classList.add('hidden');
    }
}

/**
 * Upload master cases - handles both topic-level and individual case uploads
 */
async function uploadMasterCases(idParam) {
    let selectedCaseIds = [];
    let topicId = '';
    let uploadButton = null;

    // Check if this is a single case ID or a topic ID
    const caseRow = document.querySelector(`[data-case-id="${idParam}"]`);

    if (caseRow) {
        // This is a single case upload
        selectedCaseIds = [idParam];
        topicId = caseRow.dataset.topic;
        uploadButton = caseRow.querySelector('button');
        console.log(`Single case upload: ${idParam} from topic: ${topicId}`);
    } else {
        // This is a topic-level upload
        const checkedBoxes = document.querySelectorAll(`input[data-topic-id="${idParam}"]:checked`);

        if (checkedBoxes.length === 0) {
            showError('No cases selected for upload');
            return;
        }

        selectedCaseIds = Array.from(checkedBoxes).map(checkbox => checkbox.dataset.caseId);
        topicId = idParam;
        uploadButton = document.getElementById(`uploadMasterCases-${idParam}`);
        console.log(`Topic-level upload: ${selectedCaseIds.length} cases from topic: ${topicId}`);
    }

    try {
        // Show loading state
        const originalText = uploadButton.innerHTML;
        uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Uploading...';
        uploadButton.disabled = true;

        console.log(`Uploading ${selectedCaseIds.length} master cases for topic ${topicId}:`, selectedCaseIds);

        // Call backend API
        const response = await fetch('/api/master-cases/upload-cases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                case_ids: selectedCaseIds,
                topic_id: topicId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            showSuccess(result.message || `Successfully uploaded ${selectedCaseIds.length} master case(s)`);
            console.log('Upload response:', result);
        } else {
            throw new Error(result.message || 'Upload failed');
        }

        // Reset button
        uploadButton.innerHTML = originalText;
        uploadButton.disabled = false;

        // Reset checkboxes after successful upload (only for topic-level uploads)
        if (!caseRow) {
            // This was a topic-level upload, reset all checkboxes
            const selectAllCheckbox = document.getElementById(`selectAll-${topicId}`);
            const checkedBoxes = document.querySelectorAll(`input[data-topic-id="${topicId}"]:checked`);
            selectAllCheckbox.checked = false;
            checkedBoxes.forEach(checkbox => checkbox.checked = false);
            uploadButton.classList.add('hidden');
        }

    } catch (error) {
        console.error('Upload failed:', error);
        showError(`Failed to upload master cases: ${error.message}`);

        // Reset button on error
        if (caseRow) {
            uploadButton.innerHTML = '<i class="fas fa-upload mr-1"></i>Upload Master Case';
        } else {
            uploadButton.innerHTML = '<i class="fas fa-upload mr-1"></i>Upload Master Cases';
        }
        uploadButton.disabled = false;
    }
}

/**
 * Proceed with a case (preview and download functionality)
 */
async function proceedWithCase(caseId) {
    const caseItem = masterCases.find(c => c.id === caseId);
    if (!caseItem) {
        showError('Case not found');
        return;
    }

    // Open preview modal
    await previewCase(caseId);
}

/**
 * Preview a case in modal
 */
async function previewCase(caseId) {
    const caseItem = masterCases.find(c => c.id === caseId);
    if (!caseItem) {
        showError('Case not found');
        return;
    }

    currentPreviewCase = caseItem;

    const modal = document.getElementById('casePreviewModal');
    const title = document.getElementById('previewTitle');
    const content = document.getElementById('previewContent');

    title.textContent = `${caseItem.case_title || caseItem.title} - Preview`;
    content.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-3xl text-slate-500 mb-4"></i><p>Loading case content...</p></div>';

    modal.classList.remove('hidden');

    try {
        // Fetch case content
        const response = await fetch(`/api/master-cases/${caseId}/content/`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Convert markdown to HTML or display as formatted text
            content.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <h3 class="font-semibold text-blue-900 mb-2">${escapeHtml(caseItem.case_title || caseItem.title)}</h3>
                    <p class="text-sm text-blue-800">Disease: ${escapeHtml(caseItem.disease_name || 'N/A')}</p>
                    <p class="text-sm text-blue-800">Topic: ${escapeHtml(caseItem.topic || 'N/A')}</p>
                </div>
                <div class="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                    ${escapeHtml(result.content)}
                </div>
            `;
        } else {
            throw new Error(result.message || 'Failed to load case content');
        }

    } catch (error) {
        console.error('Error loading case content:', error);
        content.innerHTML = `
            <div class="text-center py-8 text-red-600">
                <i class="fas fa-exclamation-triangle text-3xl mb-4"></i>
                <p>Error loading case content: ${error.message}</p>
            </div>
        `;
    }
}

/**
 * Close case preview modal
 */
function closeCasePreview() {
    document.getElementById('casePreviewModal').classList.add('hidden');
    currentPreviewCase = null;
}

/**
 * Download current previewed case
 */
function downloadCurrentCase() {
    if (currentPreviewCase) {
        downloadCase(currentPreviewCase.id);
    }
}

/**
 * Download a specific case
 */
async function downloadCase(caseId) {
    try {
        const response = await fetch(`/api/master-cases/${caseId}/download/`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');

        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        const filename = contentDisposition ?
            contentDisposition.split('filename=')[1]?.replace(/"/g, '') :
            `master-case-${caseId}.md`;

        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Error downloading case:', error);
        showError('Failed to download case: ' + error.message);
    }
}

/**
 * Download all cases for a specific topic
 */
async function downloadTopicCases(topicName) {
    const topicCases = masterCases.filter(c => c.topic === topicName && c.status === 'generated');

    if (topicCases.length === 0) {
        showError('No generated cases found for this topic');
        return;
    }

    try {
        for (const caseItem of topicCases) {
            await downloadCase(caseItem.id);
            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        showSuccess(`Downloaded ${topicCases.length} cases for ${topicName}`);

    } catch (error) {
        console.error('Error downloading topic cases:', error);
        showError('Failed to download all cases: ' + error.message);
    }
}

/**
 * Download all generated cases
 */
async function downloadAllCases() {
    const generatedCases = masterCases.filter(c => c.status === 'generated');

    if (generatedCases.length === 0) {
        showError('No generated cases available for download');
        return;
    }

    const confirmed = confirm(`Download all ${generatedCases.length} generated master cases?`);
    if (!confirmed) return;

    try {
        for (const caseItem of generatedCases) {
            await downloadCase(caseItem.id);
            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        showSuccess(`Downloaded ${generatedCases.length} master cases`);

    } catch (error) {
        console.error('Error downloading all cases:', error);
        showError('Failed to download all cases: ' + error.message);
    }
}

/**
 * Show case error details
 */
async function showCaseError(caseId) {
    const caseItem = masterCases.find(c => c.id === caseId);
    if (!caseItem) return;

    alert(`Case Generation Error\n\nCase: ${caseItem.case_title || caseItem.title}\nError: ${caseItem.error_message || 'Unknown error occurred'}\n\nYou can try regenerating this case.`);
}

/**
 * Regenerate a failed case
 */
async function regenerateCase(caseId) {
    const confirmed = confirm('Regenerate this failed case? This will attempt to create the master case document again.');
    if (!confirmed) return;

    try {
        const response = await fetch(`/api/master-cases/${caseId}/regenerate/`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            showSuccess('Case regeneration started. Refresh the page in a few moments to see the result.');
        } else {
            throw new Error(result.message || 'Regeneration failed');
        }

    } catch (error) {
        console.error('Error regenerating case:', error);
        showError('Failed to regenerate case: ' + error.message);
    }
}

/**
 * Refresh case list
 */
function refreshCaseList() {
    loadMasterCases();
}

/**
 * Utility functions
 */
function sanitizeTopicName(topicName) {
    if (!topicName) return 'unknown_topic';
    return topicName.replace(/[^\w\s-]/g, '').replace(/[-\s]+/g, '_').trim('_').toLowerCase();
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function (m) { return map[m]; });
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (!bytes) return '';
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert('Success: ' + message);
} 