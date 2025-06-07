/**
 * Master Case Generation Integration
 * Handles the workflow from approved assessment cases to generated master case documents
 */

// Global state management
window.masterCaseState = {
    currentTopicId: null,
    currentAssessmentResult: null,
    generationInProgress: false
};

/**
 * Main function to approve assessment and generate master cases
 */
async function approveAssessment() {
    const result = window.currentAssessmentResult;
    if (!result) {
        showError('No assessment data available');
        return;
    }

    // Close the current modal and start master case generation
    closeAssessmentResultsModal();

    try {
        // Get topic name from the current context
        const topicName = getTopicIdFromCurrentData();

        if (!topicName) {
            showError('Unable to determine topic name. Please ensure reference documents are uploaded first.');
            return;
        }

        // Show loading modal
        showMasterCaseGenerationLoading(result.recommendedCases.length);

        console.log('🚀 Starting master case generation for topic:', topicName);
        console.log('📋 Approved cases:', result.recommendedCases);

        // Call master case generation API
        const response = await fetch('/api/assessment/generate-master-cases-from-assessment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic_name: topicName,
                approved_cases: result.recommendedCases,
                original_topic_data: result.originalTopicData || window.currentSelectedTopic
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const masterCaseResult = await response.json();
        console.log('✅ Master case generation result:', masterCaseResult);

        closeMasterCaseGenerationLoading();

        if (masterCaseResult.success) {
            showMasterCaseSuccess(masterCaseResult);
        } else {
            throw new Error(masterCaseResult.message || 'Master case generation failed');
        }

    } catch (error) {
        console.error('❌ Error generating master cases:', error);
        closeMasterCaseGenerationLoading();
        showMasterCaseError(error.message);
    }
}

/**
 * Get topic name from current data context
 */
function getTopicIdFromCurrentData() {
    // Try multiple sources to get topic name

    // 1. Check if it's stored in global state
    if (window.masterCaseState.currentTopicId) {
        return window.masterCaseState.currentTopicId;
    }

    // 2. Try to get from selected topic
    if (window.currentSelectedTopic && window.currentSelectedTopic.topic) {
        const topicName = window.currentSelectedTopic.topic;
        window.masterCaseState.currentTopicId = topicName;
        return topicName;
    }

    // 3. Try to derive from current loaded JSON data
    if (window.currentJsonData && window.currentJsonData.topics && window.currentJsonData.topics.length > 0) {
        const topicName = window.currentJsonData.topics[0].topic || 'Unknown Topic';
        window.masterCaseState.currentTopicId = topicName;
        return topicName;
    }

    // 4. Fallback to a default topic name
    return 'Default Topic';
}

/**
 * Show loading modal for master case generation
 */
function showMasterCaseGenerationLoading(caseCount) {
    window.masterCaseState.generationInProgress = true;

    const modal = document.createElement('div');
    modal.id = 'masterCaseLoadingModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-8 max-w-lg w-full mx-4 text-center">
            <div class="relative">
                <div class="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mx-auto mb-6"></div>
                <div class="absolute inset-0 flex items-center justify-center">
                    <i class="fas fa-file-medical text-green-600 text-2xl"></i>
                </div>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-3">🎯 Generating Master Cases</h3>
            <p class="text-gray-600 mb-2">AI is creating comprehensive 13-part case documents...</p>
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div class="grid grid-cols-2 gap-4 text-center">
                    <div>
                        <div class="text-2xl font-bold text-blue-600">${caseCount}</div>
                        <div class="text-xs text-blue-700">Cases to Generate</div>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-green-600">13</div>
                        <div class="text-xs text-green-700">Parts per Case</div>
                    </div>
                </div>
            </div>
            <div class="space-y-2 text-sm text-gray-500">
                <div class="flex items-center justify-center space-x-2">
                    <i class="fas fa-circle-notch fa-spin text-blue-500"></i>
                    <span>Processing reference documents...</span>
                </div>
                <div class="flex items-center justify-center space-x-2">
                    <i class="fas fa-circle-notch fa-spin text-green-500"></i>
                    <span>Generating case content with AI...</span>
                </div>
                <div class="flex items-center justify-center space-x-2">
                    <i class="fas fa-circle-notch fa-spin text-purple-500"></i>
                    <span>Creating markdown documents...</span>
                </div>
            </div>
            <p class="text-xs text-gray-400 mt-4">This process may take 30-60 seconds per case...</p>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Close master case generation loading modal
 */
function closeMasterCaseGenerationLoading() {
    window.masterCaseState.generationInProgress = false;
    const modal = document.getElementById('masterCaseLoadingModal');
    if (modal) {
        document.body.removeChild(modal);
    }
}

/**
 * Show success modal with generated master cases
 */
function showMasterCaseSuccess(result) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div class="p-6 border-b border-gray-200 flex justify-between items-center">
                <div>
                    <h2 class="text-xl font-bold text-green-900">🎉 Master Cases Generated Successfully!</h2>
                    <p class="text-sm text-gray-600">Topic: ${result.topic_name}</p>
                </div>
                <button onclick="closeMasterCaseSuccessModal()" class="text-gray-400 hover:text-gray-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            
            <div class="flex-1 overflow-y-auto p-6">
                <!-- Generation Summary -->
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                    <h3 class="text-lg font-semibold text-green-900 mb-3">📊 Generation Summary</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-white p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-green-600">${result.successful_generations}</div>
                            <div class="text-sm text-green-700">Successfully Generated</div>
                        </div>
                        <div class="bg-white p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-red-600">${result.failed_generations}</div>
                            <div class="text-sm text-red-700">Failed</div>
                        </div>
                        <div class="bg-white p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-blue-600">${result.total_cases}</div>
                            <div class="text-sm text-blue-700">Total Cases</div>
                        </div>
                    </div>
                </div>

                <!-- Generated Cases List -->
                <div class="mb-6">
                    <h4 class="font-semibold text-gray-800 mb-3">✅ Generated Master Cases</h4>
                    <div class="space-y-3">
                        ${result.generated_cases.map(caseItem => `
                            <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                                <div class="flex justify-between items-start mb-2">
                                    <h5 class="font-semibold text-gray-900">${escapeHtml(caseItem.case_title)}</h5>
                                    <span class="bg-green-100 text-green-700 text-xs px-2 py-1 rounded">Generated</span>
                                </div>
                                <div class="text-sm text-gray-600 space-y-1">
                                    <div><strong>File:</strong> <code class="bg-gray-200 px-1 rounded">${caseItem.disease_name}.md</code></div>
                                    <div><strong>Path:</strong> <code class="bg-gray-200 px-1 rounded text-xs">${caseItem.saved_path}</code></div>
                                </div>
                                <div class="mt-2 flex space-x-2">
                                    <button onclick="previewMasterCase('${caseItem.saved_path}')" 
                                            class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                                        <i class="fas fa-eye mr-1"></i>Preview
                                    </button>
                                    <button onclick="downloadMasterCase('${caseItem.saved_path}', '${caseItem.disease_name}')" 
                                            class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm">
                                        <i class="fas fa-download mr-1"></i>Download
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Failed Cases (if any) -->
                ${result.failed_cases.length > 0 ? `
                    <div class="mb-6">
                        <h4 class="font-semibold text-red-800 mb-3">❌ Failed Cases</h4>
                        <div class="space-y-2">
                            ${result.failed_cases.map(failedCase => `
                                <div class="border border-red-200 rounded-lg p-3 bg-red-50">
                                    <div class="flex justify-between items-center">
                                        <span class="font-medium text-red-900">${escapeHtml(failedCase.case_title)}</span>
                                        <span class="bg-red-100 text-red-700 text-xs px-2 py-1 rounded">Failed</span>
                                    </div>
                                    <div class="text-sm text-red-700 mt-1">${escapeHtml(failedCase.error)}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Next Steps -->
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 class="font-semibold text-blue-900 mb-2">🎯 Next Steps</h4>
                    <ul class="text-sm text-blue-800 space-y-1">
                        <li>• Review and customize the generated master cases</li>
                        <li>• Integrate cases into your learning management system</li>
                        <li>• Use cases for student assessments and clinical training</li>
                        <li>• Generate additional cases for other topics as needed</li>
                    </ul>
                </div>
            </div>
            
            <div class="p-6 border-t border-gray-200 flex justify-between">
                <button onclick="openCacheDirectory()" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md">
                    <i class="fas fa-folder-open mr-2"></i>Open Cache Folder
                </button>
                <div class="space-x-3">
                    <button onclick="downloadAllCases()" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md">
                        <i class="fas fa-download mr-2"></i>Download All
                    </button>
                    <button onclick="closeMasterCaseSuccessModal()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md">
                        Done
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    window.currentMasterCaseSuccessModal = modal;
    window.currentMasterCaseResult = result;
}

/**
 * Show error modal for master case generation
 */
function showMasterCaseError(errorMessage) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <div class="flex items-center mb-4">
                <svg class="w-8 h-8 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 class="text-lg font-semibold text-red-900">Master Case Generation Failed</h3>
            </div>
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p class="text-red-800 text-sm font-medium mb-2">Error Details:</p>
                <p class="text-red-700 text-sm">${escapeHtml(errorMessage)}</p>
            </div>
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                <p class="text-yellow-800 text-sm font-medium mb-1">💡 Possible Solutions:</p>
                <ul class="text-yellow-700 text-sm space-y-1">
                    <li>• Ensure reference documents are uploaded for this topic</li>
                    <li>• Check that the Gemini API key is configured</li>
                    <li>• Verify case titles and scenarios are properly formatted</li>
                    <li>• Try again with fewer cases if there's a timeout</li>
                </ul>
            </div>
            <div class="flex justify-end space-x-3">
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        class="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md">
                    Close
                </button>
                <button onclick="this.parentElement.parentElement.parentElement.remove(); showCaseEditor();" 
                        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md">
                    Edit Cases & Retry
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Close success modal
 */
function closeMasterCaseSuccessModal() {
    if (window.currentMasterCaseSuccessModal) {
        document.body.removeChild(window.currentMasterCaseSuccessModal);
        window.currentMasterCaseSuccessModal = null;
    }
    // Refresh the cached files list to show new master cases
    if (typeof loadCachedFiles === 'function') {
        setTimeout(() => loadCachedFiles(), 500);
    }
}

/**
 * Preview a generated master case document
 */
async function previewMasterCase(filePath) {
    try {
        // You could implement a preview endpoint or download and display
        alert(`Preview functionality for: ${filePath}\n\nThis would show the 13-part master case document in a modal.`);
        // TODO: Implement actual preview functionality
    } catch (error) {
        console.error('Error previewing master case:', error);
        alert('Error previewing master case document');
    }
}

/**
 * Download a specific master case document
 */
async function downloadMasterCase(filePath, fileName) {
    try {
        // Create download link (assuming the files are accessible)
        const link = document.createElement('a');
        link.href = filePath;
        link.download = `${fileName}.md`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('Error downloading master case:', error);
        alert('Error downloading master case document');
    }
}

/**
 * Download all generated master cases
 */
async function downloadAllCases() {
    const result = window.currentMasterCaseResult;
    if (!result || !result.generated_cases) {
        alert('No generated cases available for download');
        return;
    }

    // Download each case individually
    for (const caseItem of result.generated_cases) {
        await downloadMasterCase(caseItem.saved_path, caseItem.disease_name);
        // Small delay between downloads
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    alert(`Downloaded ${result.generated_cases.length} master case documents!`);
}

/**
 * Open master case library page to view all generated cases
 */
function openCacheDirectory() {
    window.location.href = 'master-doc-list.html';
}

/**
 * Utility function to escape HTML
 */
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

/**
 * Show generic error message
 */
function showError(message) {
    alert(`Error: ${message}`);
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function () {
    console.log('📋 Master Case Integration loaded');
});

// Export functions for global access
window.masterCaseIntegration = {
    approveAssessment,
    getTopicIdFromCurrentData,
    showMasterCaseGenerationLoading,
    closeMasterCaseGenerationLoading,
    showMasterCaseSuccess,
    showMasterCaseError,
    previewMasterCase,
    downloadMasterCase,
    downloadAllCases
}; 