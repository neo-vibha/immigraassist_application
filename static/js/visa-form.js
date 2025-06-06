// Visa Form Handling
document.addEventListener('DOMContentLoaded', function() {
    // Form visibility toggle
    const showFormBtn = document.getElementById('show-i129-form');
    const i129Form = document.getElementById('i129-form-section');
    const documentRequirements = document.getElementById('h1b-document-requirements');
    
    if(showFormBtn) {
        showFormBtn.addEventListener('click', function() {
            i129Form.classList.remove('hidden');
            showFormBtn.classList.add('hidden');
            // Scroll to the form
            i129Form.scrollIntoView({ behavior: 'smooth' });
        });
    }
    
    // Handle conditional fields
    // Part 4: Passport explanation
    const passportRadios = document.querySelectorAll('input[name="validPassport"]');
    const passportExplanation = document.getElementById('passport-explanation');
    
    if(passportRadios.length) {
        passportRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'no') {
                    passportExplanation.classList.remove('hidden');
                    document.getElementById('passport-explanation-text').setAttribute('required', true);
                } else {
                    passportExplanation.classList.add('hidden');
                    document.getElementById('passport-explanation-text').removeAttribute('required');
                }
            });
        });
    }
    
    // Part 5: Third-party location
    const thirdPartyRadios = document.querySelectorAll('input[name="thirdParty1"]');
    const thirdPartyName = document.getElementById('third-party-name-1');
    
    if(thirdPartyRadios.length) {
        thirdPartyRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'yes') {
                    thirdPartyName.classList.remove('hidden');
                    document.getElementById('third-party-org-1').setAttribute('required', true);
                } else {
                    thirdPartyName.classList.add('hidden');
                    document.getElementById('third-party-org-1').removeAttribute('required');
                }
            });
        });
    }
    
    // Part 5: Full-time position
    const fullTimeRadios = document.querySelectorAll('input[name="fullTime"]');
    const partTimeHours = document.getElementById('part-time-hours');
    
    if(fullTimeRadios.length) {
        fullTimeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'no') {
                    partTimeHours.classList.remove('hidden');
                    document.getElementById('hours-per-week').setAttribute('required', true);
                } else {
                    partTimeHours.classList.add('hidden');
                    document.getElementById('hours-per-week').removeAttribute('required');
                }
            });
        });
    }
    
    // Form submission and validation
    const form = document.querySelector('.visa-form');
    const formContainer = document.querySelector('.form-container');
    const formPageIndicator = document.getElementById('form-page-indicator');
    const docsPageIndicator = document.getElementById('documents-page-indicator');
    
    if(form) {
        form.addEventListener('submit', function(e) {
            // Basic validation
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });
            
            if (!isValid) {
                e.preventDefault(); // Only prevent default if validation fails
                
                // Show validation error
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                // Show error message
                alert('Please fill out all required fields.');
            }
        });
    }
    
    // Reset form button
    const resetBtn = document.getElementById('reset-form');
    if(resetBtn) {
        resetBtn.addEventListener('click', function() {
            form.reset();
            document.getElementById('form-success-message').classList.add('hidden');
        });
    }
    
    // Document upload handling
    const fileInputs = document.querySelectorAll('.document-upload input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0].name;
            const uploadStatus = this.closest('.document-upload').querySelector('.upload-status');
            uploadStatus.textContent = `Selected: ${fileName}`;
            uploadStatus.classList.add('file-selected');
        });
    });
});

// Function to simulate document upload
function uploadDocument(docType) {
    const fileInput = document.querySelector(`#${docType}-upload`);
    const uploadStatus = document.querySelector(`#${docType}-status`);
    
    if (fileInput.files.length === 0) {
        alert('Please select a file first.');
        return;
    }
    
    // Show loading
    uploadStatus.textContent = 'Uploading...';
    uploadStatus.className = 'upload-status uploading';
    
    // Simulate upload delay
    setTimeout(() => {
        uploadStatus.textContent = 'Uploaded successfully';
        uploadStatus.className = 'upload-status success';
        
        // Add to documents list
        const docName = fileInput.files[0].name;
        addToDocumentsList(docType, docName);
    }, 1500);
}

// Add document to the uploaded documents list
function addToDocumentsList(docType, fileName) {
    const docTypeMap = {
        'i129': 'Form I-129',
        'lca': 'Labor Condition Application',
        'education': 'Educational Credentials',
        'support': 'Employer Support Letter',
        'resume': 'Resume/CV'
    };
    
    const docList = document.getElementById('uploaded-documents-list');
    const listItem = document.createElement('li');
    listItem.className = 'document-item';
    listItem.innerHTML = `
        <div class="document-icon"><i class="far fa-file-pdf"></i></div>
        <div class="document-details">
            <h4>${docTypeMap[docType] || docType}</h4>
            <p>${fileName}</p>
            <span class="document-status approved">Verified</span>
        </div>
    `;
    
    docList.appendChild(listItem);
}
