/**
 * Table Processor Component
 * Handles table extraction and processing functionality
 */

import { CONFIG } from '../config.js';
import { API, DOM, UI, Logger, Clipboard, DateTime } from '../utils.js';

export class TableProcessorComponent {
    constructor(containerId, options = {}) {
        this.container = DOM.getElementById(containerId);
        this.options = {
            extractEndpoint: CONFIG.API.ENDPOINTS.EXTRACT_TABLE_JSON,
            processEndpoint: CONFIG.API.ENDPOINTS.PROCESS_TABLE,
            enablePreview: true,
            enableDownload: true,
            enableCopy: true,
            ...options
        };

        this.currentData = null;
        this.processingHistory = [];
        this.init();
    }

    init() {
        if (!this.container) {
            Logger.error('Table processor container not found');
            return;
        }

        this.createProcessorUI();
        this.setupEventListeners();
        Logger.log('Table processor component initialized');
    }

    createProcessorUI() {
        this.container.innerHTML = `
            <div class="table-processor-wrapper">
                <div class="processor-header mb-6">
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">Table Extraction & Processing</h3>
                    <p class="text-gray-600">Extract and process tables from your uploaded documents</p>
                </div>

                <div class="processor-controls mb-6">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="control-group">
                            <label class="block text-sm font-medium text-gray-700 mb-2">File Selection</label>
                            <select class="file-selector w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                                <option value="">Select a file to process...</option>
                            </select>
                        </div>
                        
                        <div class="control-group">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Processing Options</label>
                            <div class="space-y-2">
                                <label class="flex items-center">
                                    <input type="checkbox" class="option-full-rows mr-2" checked>
                                    <span class="text-sm">Extract full row objects</span>
                                </label>
                                <label class="flex items-center">
                                    <input type="checkbox" class="option-preserve-format mr-2" checked>
                                    <span class="text-sm">Preserve table formatting</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div class="action-buttons mt-4 flex flex-wrap gap-3">
                        <button class="btn-extract bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors">
                            Extract Tables
                        </button>
                        <button class="btn-process bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg transition-colors hidden">
                            Process Data
                        </button>
                        <button class="btn-clear bg-gray-400 hover:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors">
                            Clear
                        </button>
                    </div>
                </div>

                <div class="processing-status mb-4 hidden">
                    <div class="status-indicator flex items-center p-4 bg-blue-50 rounded-lg">
                        <div class="spinner animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-3"></div>
                        <span class="status-text">Processing...</span>
                    </div>
                </div>

                <div class="results-container hidden">
                    <div class="results-header flex items-center justify-between mb-4">
                        <h4 class="text-lg font-medium text-gray-800">Extraction Results</h4>
                        <div class="result-actions flex gap-2">
                            <button class="btn-copy-json bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 text-sm rounded">
                                Copy JSON
                            </button>
                            <button class="btn-download-json bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 text-sm rounded">
                                Download JSON
                            </button>
                            <button class="btn-toggle-view bg-green-500 hover:bg-green-600 text-white px-3 py-1 text-sm rounded">
                                Toggle View
                            </button>
                        </div>
                    </div>

                    <div class="results-content">
                        <div class="tab-navigation mb-4">
                            <div class="flex border-b">
                                <button class="tab-btn active px-4 py-2 border-b-2 border-blue-500 text-blue-600" data-tab="preview">
                                    Preview
                                </button>
                                <button class="tab-btn px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-tab="json">
                                    JSON
                                </button>
                                <button class="tab-btn px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-tab="raw">
                                    Raw Data
                                </button>
                            </div>
                        </div>

                        <div class="tab-content">
                            <div class="tab-pane tab-preview active">
                                <div class="preview-container"></div>
                            </div>
                            <div class="tab-pane tab-json hidden">
                                <pre class="json-container bg-gray-100 p-4 rounded-lg overflow-auto max-h-96 text-sm"></pre>
                            </div>
                            <div class="tab-pane tab-raw hidden">
                                <div class="raw-container bg-gray-100 p-4 rounded-lg overflow-auto max-h-96"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="history-container mt-6 hidden">
                    <h4 class="text-lg font-medium text-gray-800 mb-4">Processing History</h4>
                    <div class="history-list space-y-2"></div>
                </div>
            </div>
        `;

        this.setupElementReferences();
    }

    setupElementReferences() {
        // Controls
        this.fileSelector = this.container.querySelector('.file-selector');
        this.optionFullRows = this.container.querySelector('.option-full-rows');
        this.optionPreserveFormat = this.container.querySelector('.option-preserve-format');

        // Buttons
        this.btnExtract = this.container.querySelector('.btn-extract');
        this.btnProcess = this.container.querySelector('.btn-process');
        this.btnClear = this.container.querySelector('.btn-clear');
        this.btnCopyJson = this.container.querySelector('.btn-copy-json');
        this.btnDownloadJson = this.container.querySelector('.btn-download-json');
        this.btnToggleView = this.container.querySelector('.btn-toggle-view');

        // Status and results
        this.processingStatus = this.container.querySelector('.processing-status');
        this.statusText = this.container.querySelector('.status-text');
        this.resultsContainer = this.container.querySelector('.results-container');

        // Tabs
        this.tabButtons = this.container.querySelectorAll('.tab-btn');
        this.previewContainer = this.container.querySelector('.preview-container');
        this.jsonContainer = this.container.querySelector('.json-container');
        this.rawContainer = this.container.querySelector('.raw-container');

        // History
        this.historyContainer = this.container.querySelector('.history-container');
        this.historyList = this.container.querySelector('.history-list');
    }

    setupEventListeners() {
        // Extract button
        this.btnExtract.addEventListener('click', () => {
            this.extractTables();
        });

        // Process button
        this.btnProcess.addEventListener('click', () => {
            this.processData();
        });

        // Clear button
        this.btnClear.addEventListener('click', () => {
            this.clearResults();
        });

        // Copy JSON button
        this.btnCopyJson.addEventListener('click', () => {
            this.copyJsonToClipboard();
        });

        // Download JSON button
        this.btnDownloadJson.addEventListener('click', () => {
            this.downloadJson();
        });

        // Tab switching
        this.tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchTab(btn.dataset.tab);
            });
        });

        // File selector change
        this.fileSelector.addEventListener('change', () => {
            this.onFileSelectionChange();
        });
    }

    async loadAvailableFiles() {
        try {
            const response = await API.get(CONFIG.API.ENDPOINTS.UPLOAD_STATS);
            if (response.files && response.files.length > 0) {
                this.populateFileSelector(response.files);
            }
        } catch (error) {
            Logger.error('Failed to load available files:', error);
        }
    }

    populateFileSelector(files) {
        this.fileSelector.innerHTML = '<option value="">Select a file to process...</option>';

        files.forEach(file => {
            const option = DOM.createElement('option', {
                value: file.id || file.name
            }, `${file.name} (${DateTime.formatDate(file.uploaded_at || Date.now())})`);

            this.fileSelector.appendChild(option);
        });
    }

    onFileSelectionChange() {
        const selectedFile = this.fileSelector.value;
        if (selectedFile) {
            Logger.log('File selected for processing:', selectedFile);
            this.btnExtract.disabled = false;
        } else {
            this.btnExtract.disabled = true;
        }
    }

    async extractTables() {
        const selectedFile = this.fileSelector.value;
        if (!selectedFile) {
            UI.showToast('Please select a file first', 'warning');
            return;
        }

        try {
            this.showProcessingStatus('Extracting tables...');

            const formData = new FormData();
            formData.append('file_id', selectedFile);
            formData.append('full_rows', this.optionFullRows.checked);
            formData.append('preserve_format', this.optionPreserveFormat.checked);

            const result = await API.post(this.options.extractEndpoint, formData);

            this.currentData = result;
            this.displayResults(result);
            this.addToHistory('extraction', result);

            DOM.show(this.btnProcess);
            UI.showToast('Tables extracted successfully!', 'success');

        } catch (error) {
            Logger.error('Table extraction failed:', error);
            UI.showToast('Extraction failed: ' + error.message, 'error');
        } finally {
            this.hideProcessingStatus();
        }
    }

    async processData() {
        if (!this.currentData) {
            UI.showToast('No data to process', 'warning');
            return;
        }

        try {
            this.showProcessingStatus('Processing data...');

            const result = await API.post(this.options.processEndpoint, {
                data: this.currentData,
                options: {
                    full_rows: this.optionFullRows.checked,
                    preserve_format: this.optionPreserveFormat.checked
                }
            });

            this.currentData = result;
            this.displayResults(result);
            this.addToHistory('processing', result);

            UI.showToast('Data processed successfully!', 'success');

        } catch (error) {
            Logger.error('Data processing failed:', error);
            UI.showToast('Processing failed: ' + error.message, 'error');
        } finally {
            this.hideProcessingStatus();
        }
    }

    displayResults(data) {
        // Show results container
        DOM.show(this.resultsContainer);

        // Update preview
        this.updatePreview(data);

        // Update JSON view
        this.jsonContainer.textContent = JSON.stringify(data, null, 2);

        // Update raw view
        this.updateRawView(data);

        // Switch to preview tab
        this.switchTab('preview');
    }

    updatePreview(data) {
        if (!data) {
            this.previewContainer.innerHTML = '<p class="text-gray-500">No data available</p>';
            return;
        }

        let html = '<div class="preview-content space-y-6">';

        if (data.topics && Array.isArray(data.topics)) {
            data.topics.forEach((topic, index) => {
                html += `
                    <div class="topic-section border rounded-lg p-4">
                        <h5 class="font-medium text-lg mb-3">${topic.topic || `Topic ${index + 1}`}</h5>
                        ${this.renderCompetencies(topic.competencies || [])}
                    </div>
                `;
            });
        } else if (data.tables && Array.isArray(data.tables)) {
            data.tables.forEach((table, index) => {
                html += `<div class="table-section mb-6">${this.renderTable(table, index)}</div>`;
            });
        } else {
            html += '<p class="text-gray-500">Unable to preview this data format</p>';
        }

        html += '</div>';
        this.previewContainer.innerHTML = html;
    }

    renderCompetencies(competencies) {
        if (!competencies || competencies.length === 0) {
            return '<p class="text-gray-500 text-sm">No competencies found</p>';
        }

        let html = '<div class="competencies-list space-y-2">';
        competencies.forEach((comp, index) => {
            html += `
                <div class="competency-item bg-gray-50 p-3 rounded">
                    <div class="competency-header font-medium text-sm mb-1">
                        Competency ${index + 1}
                    </div>
                    <div class="competency-content text-sm">
                        ${typeof comp === 'string' ? comp : JSON.stringify(comp, null, 2)}
                    </div>
                </div>
            `;
        });
        html += '</div>';

        return html;
    }

    renderTable(table, index) {
        if (!table || !table.rows) {
            return `<p class="text-gray-500">Table ${index + 1}: No data available</p>`;
        }

        let html = `
            <div class="table-wrapper">
                <h6 class="font-medium mb-2">Table ${index + 1}</h6>
                <div class="overflow-x-auto">
                    <table class="min-w-full border border-gray-200">
        `;

        // Render table rows
        table.rows.forEach((row, rowIndex) => {
            html += '<tr class="' + (rowIndex % 2 === 0 ? 'bg-gray-50' : 'bg-white') + '">';

            if (Array.isArray(row)) {
                row.forEach(cell => {
                    html += `<td class="border border-gray-200 px-3 py-2 text-sm">${cell || ''}</td>`;
                });
            } else if (typeof row === 'object') {
                Object.values(row).forEach(cell => {
                    html += `<td class="border border-gray-200 px-3 py-2 text-sm">${cell || ''}</td>`;
                });
            }

            html += '</tr>';
        });

        html += `
                    </table>
                </div>
            </div>
        `;

        return html;
    }

    updateRawView(data) {
        this.rawContainer.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }

    switchTab(tabName) {
        // Update tab buttons
        this.tabButtons.forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active', 'border-blue-500', 'text-blue-600');
                btn.classList.remove('border-transparent', 'text-gray-500');
            } else {
                btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
                btn.classList.add('border-transparent', 'text-gray-500');
            }
        });

        // Update tab panes
        this.container.querySelectorAll('.tab-pane').forEach(pane => {
            if (pane.classList.contains(`tab-${tabName}`)) {
                pane.classList.remove('hidden');
                pane.classList.add('active');
            } else {
                pane.classList.add('hidden');
                pane.classList.remove('active');
            }
        });
    }

    async copyJsonToClipboard() {
        if (!this.currentData) {
            UI.showToast('No data to copy', 'warning');
            return;
        }

        const success = await Clipboard.copy(JSON.stringify(this.currentData, null, 2));
        if (success) {
            UI.showToast('JSON copied to clipboard!', 'success');
        } else {
            UI.showToast('Failed to copy to clipboard', 'error');
        }
    }

    downloadJson() {
        if (!this.currentData) {
            UI.showToast('No data to download', 'warning');
            return;
        }

        const blob = new Blob([JSON.stringify(this.currentData, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `table-extraction-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        UI.showToast('JSON downloaded successfully!', 'success');
    }

    addToHistory(type, data) {
        const historyItem = {
            id: Date.now(),
            type,
            timestamp: new Date(),
            data,
            fileId: this.fileSelector.value
        };

        this.processingHistory.unshift(historyItem);
        this.updateHistoryDisplay();
        DOM.show(this.historyContainer);
    }

    updateHistoryDisplay() {
        this.historyList.innerHTML = this.processingHistory.map(item => `
            <div class="history-item bg-white border rounded-lg p-3 cursor-pointer hover:bg-gray-50" data-id="${item.id}">
                <div class="flex justify-between items-start">
                    <div>
                        <span class="font-medium capitalize">${item.type}</span>
                        <span class="text-sm text-gray-500 ml-2">${DateTime.formatDate(item.timestamp)}</span>
                    </div>
                    <button class="text-blue-500 hover:text-blue-700 text-sm">Load</button>
                </div>
            </div>
        `).join('');

        // Add click listeners for history items
        this.historyList.querySelectorAll('.history-item button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const itemId = parseInt(e.target.closest('.history-item').dataset.id);
                this.loadFromHistory(itemId);
            });
        });
    }

    loadFromHistory(itemId) {
        const historyItem = this.processingHistory.find(item => item.id === itemId);
        if (historyItem) {
            this.currentData = historyItem.data;
            this.displayResults(historyItem.data);
            UI.showToast('Data loaded from history', 'success');
        }
    }

    showProcessingStatus(message) {
        this.statusText.textContent = message;
        DOM.show(this.processingStatus);
        this.btnExtract.disabled = true;
        this.btnProcess.disabled = true;
    }

    hideProcessingStatus() {
        DOM.hide(this.processingStatus);
        this.btnExtract.disabled = false;
        this.btnProcess.disabled = false;
    }

    clearResults() {
        this.currentData = null;
        DOM.hide(this.resultsContainer);
        DOM.hide(this.btnProcess);
        DOM.hide(this.historyContainer);
        this.fileSelector.value = '';
        UI.showToast('Results cleared', 'info');
    }

    // Public API methods
    getData() {
        return this.currentData;
    }

    setData(data) {
        this.currentData = data;
        this.displayResults(data);
    }

    getHistory() {
        return this.processingHistory;
    }

    clearHistory() {
        this.processingHistory = [];
        this.updateHistoryDisplay();
        DOM.hide(this.historyContainer);
    }
}