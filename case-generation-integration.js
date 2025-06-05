// case-generation-integration.js

class AssessmentCaseGenerator {
    constructor() {
        this.modal = null;
        this.interface = null;
        this.init();
    }

    init() {
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        // Create modal overlay
        const modalHTML = `
            <div id="caseGenerationModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden flex items-center justify-center p-4">
                <div class="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                    <iframe id="caseGenerationFrame" 
                            src="case-generation.html" 
                            class="w-full flex-1 border-0"
                            style="min-height: 600px;">
                    </iframe>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('caseGenerationModal');
    }

    bindEvents() {
        // Listen for events from the iframe
        window.addEventListener('message', (event) => {
            if (event.origin !== window.location.origin) return;

            switch (event.data.type) {
                case 'casesApproved':
                    this.handleCasesApproved(event.data.payload);
                    break;
                case 'casesRejected':
                    this.handleCasesRejected(event.data.payload);
                    break;
                case 'closeModal':
                    this.close();
                    break;
            }
        });

        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    // Public method to open with topic data
    async openForTopic(topicData) {
        if (!topicData || !topicData.competencies) {
            throw new Error('Invalid topic data provided');
        }

        this.modal.classList.remove('hidden');

        // Send topic data to iframe when loaded
        const frame = document.getElementById('caseGenerationFrame');
        frame.onload = () => {
            frame.contentWindow.postMessage({
                type: 'initializeTopic',
                payload: topicData
            }, window.location.origin);
        };

        // Also send immediately in case iframe is already loaded
        try {
            frame.contentWindow.postMessage({
                type: 'initializeTopic',
                payload: topicData
            }, window.location.origin);
        } catch (e) {
            // Iframe not ready yet, will send on load
        }
    }

    close() {
        this.modal.classList.add('hidden');
    }

    handleCasesApproved(data) {
        console.log('Cases approved:', data);

        // Emit event for your main application
        const event = new CustomEvent('assessmentCasesApproved', {
            detail: data
        });
        document.dispatchEvent(event);

        this.close();

        // Show success message
        this.showNotification('Cases approved! Proceeding to case generation...', 'success');
    }

    handleCasesRejected(data) {
        console.log('Cases rejected:', data);

        // Emit event for your main application
        const event = new CustomEvent('assessmentCasesRejected', {
            detail: data
        });
        document.dispatchEvent(event);

        // Keep modal open for regeneration
        this.showNotification('Cases need revision. You can regenerate or modify the selection.', 'warning');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-60 p-4 rounded-lg shadow-lg max-w-md transition-all duration-300 transform translate-x-full`;

        const bgColor = {
            success: 'bg-green-500',
            warning: 'bg-yellow-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        }[type] || 'bg-blue-500';

        notification.classList.add(bgColor);
        notification.innerHTML = `
            <div class="text-white">
                <p class="font-medium">${message}</p>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    // Static method for easy instantiation
    static create() {
        return new AssessmentCaseGenerator();
    }
}

// Initialize automatically when script loads
window.assessmentCaseGenerator = AssessmentCaseGenerator.create();

// Usage documentation:
/*
// To open the case generation interface:
// Assuming you have topic data from your cached files
const topicData = {
    topic: "Liver Disease",
    competencies: [ ... ] // Array of competency objects
};

window.assessmentCaseGenerator.openForTopic(topicData);

// Listen for results
document.addEventListener('assessmentCasesApproved', (event) => {
    const { topic, cases, analysis } = event.detail;
    // Proceed with case generation using the approved cases
    console.log('Approved cases:', cases);
});

document.addEventListener('assessmentCasesRejected', (event) => {
    const { topic, analysis, reason } = event.detail;
    // Handle rejection - maybe log for improvement
    console.log('Cases rejected:', reason);
});
*/ 