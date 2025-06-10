/**
 * Document Upload Functionality for ImmigraAssist
 * Handles document uploads for visa applications
 */

// Document priority and importance data
const documentPriority = {
    h1b: [
        {
            id: "h1b-form-129",
            name: "Form I-129 Petition",
            importance: "Critical",
            description: "The primary petition form for H-1B visa applications. Must be completed accurately with all required information about the employer, beneficiary, and position."
        },
        {
            id: "h1b-lca",
            name: "Labor Condition Application (LCA)",
            importance: "Critical",
            description: "Certified by the Department of Labor, this document verifies that the employer will pay the prevailing wage and provide working conditions that won't adversely affect U.S. workers."
        },
        {
            id: "h1b-degree",
            name: "Educational Credentials",
            importance: "Critical",
            description: "Proof that the beneficiary has at least a bachelor's degree or equivalent in a specific specialty directly related to the position."
        },
        {
            id: "h1b-passport",
            name: "Valid Passport",
            importance: "Critical",
            description: "A valid passport is required for all visa applications. Must be valid for at least six months beyond the intended period of stay in the United States."
        },
        {
            id: "h1b-support-letter",
            name: "Employer Support Letter",
            importance: "High",
            description: "Details the job offer, explains how the position qualifies as a specialty occupation, and confirms the employer-employee relationship."
        }
    ],
    l1: [
        {
            id: "l1-form-129",
            name: "Form I-129 with L Classification Supplement",
            importance: "Critical",
            description: "The primary petition form for L-1 visa applications with the L Classification Supplement that provides specific information about the intracompany transferee."
        },
        {
            id: "l1-qualifying-relationship",
            name: "Evidence of Qualifying Relationship",
            importance: "Critical",
            description: "Documentation proving the qualifying relationship between the U.S. and foreign entities (parent, subsidiary, affiliate, or branch office)."
        },
        {
            id: "l1-proof-employment",
            name: "Proof of Employment Abroad",
            importance: "Critical",
            description: "Evidence that the beneficiary has been employed by the foreign entity for at least one continuous year within the three years preceding the application."
        },
        {
            id: "l1-passport",
            name: "Valid Passport",
            importance: "Critical",
            description: "A valid passport is required for all visa applications. Must be valid for at least six months beyond the intended period of stay in the United States."
        },
        {
            id: "l1-company-letter",
            name: "Company Support Letter with Job Descriptions",
            importance: "High",
            description: "Details both the foreign and U.S. positions, explaining how they are managerial, executive, or involve specialized knowledge."
        }
    ]
};

// Initialize document upload functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const uploadButtons = document.querySelectorAll('.upload-btn');
    const modal = document.getElementById('upload-modal');
    const bulkModal = document.getElementById('bulk-upload-modal');
    const bulkUploadButton = document.getElementById('bulk-upload-button');
    const closeModal = modal.querySelector('.close-modal');
    const closeBulkModal = bulkModal.querySelector('.close-modal');
    const cancelUpload = modal.querySelector('.cancel-upload');
    const cancelBulkUpload = bulkModal.querySelector('.cancel-bulk-upload');
    const uploadDocumentType = document.getElementById('upload-document-type');
    const fileInput = document.getElementById('document-file');
    const bulkFileInput = document.getElementById('bulk-document-files');
    const uploadSubmit = document.getElementById('upload-submit');
    const bulkUploadSubmit = document.getElementById('bulk-upload-submit');
    const h1bChecklist = document.getElementById('h1b-checklist');
    const l1Checklist = document.getElementById('l1-checklist');
    
    // Show top 5 documents for each visa type
    function displayTopDocuments() {
        // Clear existing checklists
        h1bChecklist.innerHTML = '';
        l1Checklist.innerHTML = '';
        
        // Add H1B top documents
        documentPriority.h1b.forEach(doc => {
            const item = createDocumentItem(doc, 'h1b');
            h1bChecklist.appendChild(item);
        });
        
        // Add L1 top documents
        documentPriority.l1.forEach(doc => {
            const item = createDocumentItem(doc, 'l1');
            l1Checklist.appendChild(item);
        });
    }
    
    // Create document checklist item
    function createDocumentItem(doc, visaType) {
        const item = document.createElement('div');
        item.className = 'checklist-item';
        
        // Add importance badge
        const importanceBadge = document.createElement('span');
        importanceBadge.className = `importance-badge ${doc.importance.toLowerCase()}`;
        importanceBadge.textContent = doc.importance;
        
        // Create checkbox
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = doc.id;
        checkbox.className = 'checklist-checkbox';
        
        // Create label
        const label = document.createElement('label');
        label.htmlFor = doc.id;
        label.textContent = doc.name;
        
        // Create description
        const description = document.createElement('p');
        description.className = 'document-description';
        description.textContent = doc.description;
        
        // Create upload button
        const uploadBtn = document.createElement('button');
        uploadBtn.className = 'upload-btn';
        uploadBtn.dataset.document = doc.id;
        uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload';
        
        // Add event listener to upload button
        uploadBtn.addEventListener('click', function() {
            openUploadModal(doc.id, doc.name);
        });
        
        // Assemble the item
        item.appendChild(importanceBadge);
        item.appendChild(checkbox);
        item.appendChild(label);
        item.appendChild(description);
        item.appendChild(uploadBtn);
        
        return item;
    }
    
    // Tab switching functionality
    function setupTabSwitching() {
        const tabButtons = document.querySelectorAll('.upload-tab-btn');
        const tabContents = document.querySelectorAll('.upload-tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Hide all tab contents
                tabContents.forEach(content => content.style.display = 'none');
                
                // Show the selected tab content
                const tabId = this.dataset.tab;
                document.getElementById(`${tabId}-upload-tab`).style.display = 'block';
            });
        });
    }
    
    // Open upload modal
    function openUploadModal(docId, docName) {
        uploadDocumentType.querySelector('span').textContent = docName;
        modal.dataset.documentId = docId;
        modal.style.display = 'block';
        fileInput.value = ''; // Clear any previous selection
    }
    
    // Open bulk upload modal
    function openBulkUploadModal() {
        bulkModal.style.display = 'block';
        bulkFileInput.value = ''; // Clear any previous selection
        
        // Clear bulk file list
        const bulkFileList = document.getElementById('bulk-file-list');
        if (bulkFileList) {
            bulkFileList.innerHTML = '';
        }
    }
    
    // Close upload modal
    function closeUploadModal() {
        modal.style.display = 'none';
    }
    
    // Close bulk upload modal
    function closeBulkUploadModal() {
        bulkModal.style.display = 'none';
    }
    
    // Handle single file upload
    function handleFileUpload() {
        const docId = modal.dataset.documentId;
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a file to upload.');
            return;
        }
        
        // Show loading state
        uploadSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        uploadSubmit.disabled = true;
        
        // Simulate file upload (in a real app, this would be an API call)
        setTimeout(() => {
            // Mark the document as uploaded in the UI
            markDocumentAsUploaded(docId);
            
            // Reset and close modal
            uploadSubmit.innerHTML = 'Upload Document';
            uploadSubmit.disabled = false;
            closeUploadModal();
            
            // Update document step in the status tracker
            updateDocumentStep();
        }, 2000);
    }
    
    // Handle bulk file upload
    function handleBulkFileUpload() {
        const bulkFileInput = document.getElementById('bulk-document-files');
        const files = bulkFileInput.files;
        
        if (files.length === 0) {
            alert('Please select at least one file to upload.');
            return;
        }
        
        // Show loading state
        const bulkUploadSubmit = document.getElementById('bulk-upload-submit');
        bulkUploadSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...'; 
        bulkUploadSubmit.disabled = true;
        
        // Simulate processing and categorizing files
        setTimeout(() => {
            // For demo purposes, we'll randomly assign files to document types
            const visaType = document.getElementById('h1b').checked ? 'h1b' : 'l1';
            const docTypes = documentPriority[visaType].map(doc => doc.id);
            
            // Process each file
            let filesProcessed = 0;
            const totalFiles = files.length;
            
            // Create a progress indicator
            const bulkFileList = document.getElementById('bulk-file-list');
            const progressItem = document.createElement('div');
            progressItem.className = 'bulk-file-item progress-item';
            progressItem.innerHTML = `
                <div class="progress-indicator">
                    <i class="fas fa-cog fa-spin"></i>
                    <span>AI analyzing documents: <span class="progress-count">0</span>/${totalFiles}</span>
                </div>
            `;
            bulkFileList.appendChild(progressItem);
            
            // Process files with a delay to simulate AI analysis
            Array.from(files).forEach((file, index) => {
                setTimeout(() => {
                    // Update progress
                    filesProcessed++;
                    progressItem.querySelector('.progress-count').textContent = filesProcessed;
                    
                    // Randomly assign to a document type
                    const randomDocType = docTypes[Math.floor(Math.random() * docTypes.length)];
                    
                    // Mark as uploaded
                    markDocumentAsUploaded(randomDocType);
                    
                    // If all files processed, finish up
                    if (filesProcessed === totalFiles) {
                        // Remove progress indicator
                        progressItem.innerHTML = `
                            <div class="progress-indicator complete">
                                <i class="fas fa-check-circle"></i>
                                <span>All documents processed successfully!</span>
                            </div>
                        `;
                        
                        // Reset button
                        bulkUploadSubmit.innerHTML = 'Upload All Documents';
                        bulkUploadSubmit.disabled = false;
                        
                        // Update document step
                        updateDocumentStep();
                        
                        // Auto-close after a delay
                        setTimeout(() => {
                            closeUploadModal();
                        }, 2000);
                    }
                }, 1000 + (index * 800)); // Stagger the processing for effect
            });
        }, 1500);
    }
    
    // Mark a document as uploaded
    function markDocumentAsUploaded(docId) {
        // Mark the document as uploaded in the UI
        const checkbox = document.getElementById(docId);
        if (checkbox) {
            checkbox.checked = true;
            
            // Add upload success indicator
            const label = document.querySelector(`label[for="${docId}"]`);
            const parent = label.parentElement;
            
            // Check if success indicator already exists
            if (!parent.querySelector('.upload-success')) {
                const successIndicator = document.createElement('span');
                successIndicator.className = 'upload-success';
                successIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Uploaded';
                parent.appendChild(successIndicator);
            }
        }
    }
    
    // Handle bulk file selection
    function handleBulkFileSelection() {
        const bulkFileInput = document.getElementById('bulk-document-files');
        const bulkFileList = document.getElementById('bulk-file-list');
        const files = bulkFileInput.files;
        
        // Clear the list
        bulkFileList.innerHTML = '';
        
        if (files.length === 0) {
            return;
        }
        
        // Add each file to the list
        Array.from(files).forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'bulk-file-item';
            
            // Determine file icon based on type
            let fileIcon = 'fa-file';
            if (file.type.includes('pdf')) {
                fileIcon = 'fa-file-pdf';
            } else if (file.type.includes('image')) {
                fileIcon = 'fa-file-image';
            }
            
            // Format file size
            const fileSize = formatFileSize(file.size);
            
            fileItem.innerHTML = `
                <i class="fas ${fileIcon} bulk-file-icon"></i>
                <div class="bulk-file-name">${file.name}</div>
                <div class="bulk-file-size">${fileSize}</div>
                <i class="fas fa-times bulk-file-remove" data-filename="${file.name}"></i>
            `;
            
            bulkFileList.appendChild(fileItem);
        });
        
        // Add remove functionality
        document.querySelectorAll('.bulk-file-remove').forEach(removeBtn => {
            removeBtn.addEventListener('click', function() {
                // This is a bit tricky since we can't directly remove from a FileList
                // In a real app, you'd use a more robust solution
                this.closest('.bulk-file-item').remove();
            });
        });
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return bytes + ' B';
        } else if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(1) + ' KB';
        } else {
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
    }
    
    // Update document step in the status tracker
    function updateDocumentStep() {
        const documentStep = document.getElementById('document-step');
        const visaType = document.getElementById('h1b').checked ? 'h1b' : 'l1';
        const requiredDocs = documentPriority[visaType];
        
        // Count uploaded documents
        let uploadedCount = 0;
        requiredDocs.forEach(doc => {
            if (document.getElementById(doc.id).checked) {
                uploadedCount++;
            }
        });
        
        // Update status based on upload progress
        if (uploadedCount === requiredDocs.length) {
            // All documents uploaded
            documentStep.classList.add('completed');
            document.getElementById('status-badge').textContent = 'Documents Ready';
            document.getElementById('status-badge').className = 'status-badge ready';
            
            // Enable process button
            const processBtn = document.getElementById('process-btn');
            processBtn.disabled = false;
            processBtn.classList.remove('disabled');
            document.querySelector('.help-text').textContent = 'All documents uploaded. Ready to process!';
        } else if (uploadedCount > 0) {
            // Some documents uploaded
            documentStep.classList.add('in-progress');
            document.getElementById('status-badge').textContent = 'In Progress';
            document.getElementById('status-badge').className = 'status-badge in-progress';
        }
    }
    
    // Add event listeners for single upload modal
    closeModal.addEventListener('click', closeUploadModal);
    cancelUpload.addEventListener('click', closeUploadModal);
    uploadSubmit.addEventListener('click', handleFileUpload);
    
    // Add event listeners for bulk upload modal
    // closeBulkModal.addEventListener('click', closeBulkUploadModal);
    // cancelBulkUpload.addEventListener('click', closeBulkUploadModal);
    // bulkUploadButton.addEventListener('click', openBulkUploadModal);
    // bulkFileInput.addEventListener('change', handleBulkFileSelection);
    // bulkUploadSubmit.addEventListener('click', handleBulkFileUpload);
    
    // Initialize the document display
    displayTopDocuments();
    
    // Disable process button initially
    const processBtn = document.getElementById('process-btn');
    processBtn.disabled = true;
    processBtn.classList.add('disabled');
});
