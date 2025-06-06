// Visa Form Handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('*** DOM Content Loaded - Visa Form ***');
    
    // Check if the user is logged in
    if (window.immigraAPI && window.immigraAPI.auth && window.immigraAPI.auth.isLoggedIn()) {
        console.log('User appears to be logged in, fetching existing petition data...');
    } else {
        console.log('User does not appear to be logged in');
    }
    
    // Fetch existing petition data if available
    fetchExistingPetitionData();
    
    // Setup auto-save functionality
    setupAutoSave();
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
    const form = document.getElementById('i129-form');
    const formContainer = document.querySelector('.form-container');
    const formPageIndicator = document.getElementById('form-page-indicator');
    const docsPageIndicator = document.getElementById('documents-page-indicator');
    
    if(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
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
            
            if (isValid) {
                // Show loading indicator
                const submitBtn = form.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
                
                // Gather form data for potential API submission
                const formData = new FormData(form);
                const formDataObj = {};
                
                formData.forEach((value, key) => {
                    formDataObj[key] = value;
                });
                
                console.log('Form data:', formDataObj);
                
                // Save the form data to the backend before proceeding
                // Use await with async/await pattern to ensure save completes before continuing
                window.immigraAPI.visa.savePetitionData(formDataObj)
                    .then(result => {
                        console.log('Form data saved to backend before submission:', result);
                        if (!result.success) {
                            alert('Warning: Failed to save your form data. Your progress might not be saved.');
                        }
                        
                        // Only continue to next step AFTER save completes successfully
                        continueToDocumentsStep();
                    })
                    .catch(error => {
                        console.error('Error saving form data:', error);
                        alert('There was a problem saving your data. Please try again.');
                        
                        // Re-enable submit button if save fails
                        const submitBtn = form.querySelector('button[type="submit"]');
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                    });
                
                // Function to continue to documents step after save completes
                function continueToDocumentsStep() {
                    // Show success message and transition to page 2
                    document.getElementById('form-success-message').classList.remove('hidden');
                    
                    // Hide form container and show document requirements
                    setTimeout(() => {
                        // Update pagination indicators
                        formPageIndicator.classList.remove('active');
                        docsPageIndicator.classList.add('active');
                        
                        // Hide form and show documents
                        formContainer.classList.add('hidden');
                        documentRequirements.classList.remove('hidden');
                        documentRequirements.style.display = 'block';
                        
                        // Scroll to the top of documents section
                        i129Form.scrollIntoView({ behavior: 'smooth' });
                        
                        // Reset button
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                        
                        // Setup back button functionality
                        const backToFormBtn = document.getElementById('back-to-form');
                        if(backToFormBtn) {
                            backToFormBtn.addEventListener('click', function() {
                                // Hide documents and show form
                                documentRequirements.classList.add('hidden');
                                documentRequirements.style.display = 'none';
                                formContainer.classList.remove('hidden');
                                
                                // Update pagination indicators
                                docsPageIndicator.classList.remove('active');
                                formPageIndicator.classList.add('active');
                                
                                // Scroll to the top of form section
                                i129Form.scrollIntoView({ behavior: 'smooth' });
                            });
                        }
                    }, 1000);
                }
                
                // In a real app, you would submit this data to your backend
                // submitFormToBackend(formDataObj);
            } else {
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

// Function to fetch existing petition data from the backend
function fetchExistingPetitionData() {
    console.log('Attempting to fetch existing petition data...');
    
    // Debug the user's current session state
    const currentUser = window.immigraAPI.auth.getCurrentUser();
    console.log('Current user info from localStorage:', currentUser);
    
    // Use the API client to get user's petition data
    window.immigraAPI.visa.getUserPetition()
        .then(data => {
            console.log('Response from getUserPetition:', data);
            
            if (data.success && data.petition) {
                // Populate form fields with petition data
                const form = document.getElementById('i129-form');
                if (form) {
                    console.log('Populating form fields with petition data:', data.petition);
                    Object.entries(data.petition).forEach(([key, value]) => {
                        const field = form.querySelector(`[name="${key}"]`);
                        if (field) {
                            console.log(`Setting field '${key}' to`, value, `(type: ${field.type})`);
                            if (field.type === 'checkbox') {
                                field.checked = Boolean(value);
                            } else if (field.type === 'radio') {
                                const radioToCheck = form.querySelector(`[name="${key}"][value="${value}"]`);
                                if (radioToCheck) {
                                    radioToCheck.checked = true;
                                    console.log(`Checked radio for '${key}' value '${value}'`);
                                }
                            } else {
                                field.value = value;
                            }
                        } else {
                            console.warn(`No form field found for key '${key}'`);
                        }
                    });
                }

                console.log('SUCCESS! Existing petition data found:', data.petition);
                console.log('User ID in petition:', data.petition.user_id);
                console.log('Email in petition:', data.petition.email);
                
                // Show notification that we're loading saved data
                const formContainer = document.querySelector('.form-container');
                if (formContainer) {
                    const notification = document.createElement('div');
                    notification.className = 'data-loaded-notification';
                    notification.innerHTML = `
                        <i class="fas fa-info-circle"></i>
                        <p>Loading your previously saved data. Please wait...</p>
                    `;
                    formContainer.insertBefore(notification, formContainer.firstChild);
                }
                
                // Small delay to ensure the DOM is ready before populating
                setTimeout(() => {
                    populateFormWithExistingData(data.petition);
                    
                    // Update the notification
                    const notification = document.querySelector('.data-loaded-notification');
                    if (notification) {
                        notification.innerHTML = `
                            <i class="fas fa-check-circle"></i>
                            <p>Your previously saved form data has been loaded successfully!</p>
                        `;
                        
                        // Remove the notification after 5 seconds
                        setTimeout(() => {
                            notification.style.opacity = '0';
                            notification.style.transition = 'opacity 0.5s';
                            setTimeout(() => notification.remove(), 500);
                        }, 5000);
                    }
                    
                    // Show the form since we have existing data
                    const showFormBtn = document.getElementById('show-i129-form');
                    const i129Form = document.getElementById('i129-form-section');
                    if (showFormBtn && i129Form) {
                        i129Form.classList.remove('hidden');
                        showFormBtn.classList.add('hidden');
                    }
                }, 300);
            } else {
                console.log('No existing petition data found');
            }
        })
        .catch(error => {
            console.error('Error fetching petition data:', error);
        });
}

// Function to setup auto-save functionality
function setupAutoSave() {
    const form = document.getElementById('i129-form');
    if (!form) return;
    
    // Variables to track form changes
    let formChanged = false;
    let autoSaveTimer = null;
    const AUTO_SAVE_INTERVAL = 30000; // Auto-save every 30 seconds if changes detected
    
    // Add change event listener to all form elements
    const formElements = form.elements;
    for (let i = 0; i < formElements.length; i++) {
        const element = formElements[i];
        if (!element.name || element.type === 'button' || element.type === 'submit') continue;
        
        element.addEventListener('change', function() {
            formChanged = true;
        });
        
        // For text inputs, also listen for keyup events
        if (element.type === 'text' || element.type === 'textarea' || element.type === 'email' || element.type === 'tel' || element.type === 'number') {
            element.addEventListener('keyup', function() {
                formChanged = true;
            });
        }
    }
    
    // Function to save form data
    function saveFormData() {
        if (!formChanged) return;
        
        // Get form data
        const formData = new FormData(form);
        const formDataObj = {};
        formData.forEach((value, key) => {
            formDataObj[key] = value;
        });
        
        const currentUser = this.auth.getCurrentUser();
        if (currentUser && currentUser.user_id) {
            formDataObj.user_id = currentUser.user_id;
        }

        // Send data directly to the backend API
        fetch('/api/user_petition', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formDataObj)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Form data auto-saved successfully');
                formChanged = false;
                
                // Show a temporary auto-save notification
                showAutoSaveNotification();
            } else {
                console.error('Failed to auto-save form data:', data.message);
            }
        })
        .catch(error => {
            console.error('Error during auto-save:', error);
        });
    }
    
    // Function to show auto-save notification
    function showAutoSaveNotification() {
        // Check if notification already exists
        let notification = document.querySelector('.auto-save-notification');
        
        if (!notification) {
            // Create notification element
            notification = document.createElement('div');
            notification.className = 'auto-save-notification';
            notification.innerHTML = `
                <i class="fas fa-save"></i>
                <span>Progress auto-saved</span>
            `;
            
            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .auto-save-notification {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    z-index: 1000;
                    opacity: 0;
                    transform: translateY(20px);
                    transition: opacity 0.3s, transform 0.3s;
                }
                .auto-save-notification.show {
                    opacity: 1;
                    transform: translateY(0);
                }
                .auto-save-notification i {
                    margin-right: 8px;
                }
            `;
            document.head.appendChild(style);
            
            // Add to document
            document.body.appendChild(notification);
        }
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
            
            // Hide after 3 seconds
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }, 100);
    }
    
    // Set up auto-save timer
    autoSaveTimer = setInterval(saveFormData, AUTO_SAVE_INTERVAL);
    
    // Also save when user navigates away from the page
    window.addEventListener('beforeunload', function() {
        if (formChanged) {
            saveFormData();
        }
    });
    
    // Add save button to the form
    const formControls = form.querySelector('.form-controls');
    if (formControls) {
        const saveButton = document.createElement('button');
        saveButton.type = 'button';
        saveButton.className = 'btn-secondary save-progress-btn';
        saveButton.innerHTML = '<i class="fas fa-save"></i> Save Progress';
        
        saveButton.addEventListener('click', function() {
            saveFormData();
        });
        
        // Insert before the submit button
        const submitButton = formControls.querySelector('button[type="submit"]');
        if (submitButton) {
            formControls.insertBefore(saveButton, submitButton);
        } else {
            formControls.appendChild(saveButton);
        }
    }
}

// Function to populate form fields with existing data
function populateFormWithExistingData(petitionData) {
    // Get the form
    const form = document.getElementById('i129-form');
    if (!form) return;
    
    // Loop through all form elements and set values from petition data
    const formElements = form.elements;
    for (let i = 0; i < formElements.length; i++) {
        const element = formElements[i];
        
        // Skip buttons and elements without name attribute
        if (!element.name || element.type === 'button' || element.type === 'submit') continue;
        
        // Handle different input types
        if (element.type === 'radio') {
            // For radio buttons, check the one that matches the value
            if (element.value === petitionData[element.name]) {
                element.checked = true;
                
                // Trigger change event for conditional fields
                const event = new Event('change');
                element.dispatchEvent(event);
            }
        } else if (element.type === 'checkbox') {
            // For checkboxes, check if true
            element.checked = petitionData[element.name] === true || petitionData[element.name] === 'yes';
        } else {
            // For text inputs, selects, etc.
            if (petitionData[element.name] !== undefined) {
                element.value = petitionData[element.name];
            }
        }
    }
    
    // Handle any special cases or fields that need additional processing
    // For example, trigger change events for fields with conditional visibility
    const passportRadios = document.querySelectorAll('input[name="validPassport"]');
    const thirdPartyRadios = document.querySelectorAll('input[name="thirdParty1"]');
    const fullTimeRadios = document.querySelectorAll('input[name="fullTime"]');
    
    // Trigger change events for these fields to ensure conditional fields are shown/hidden correctly
    passportRadios.forEach(radio => {
        if (radio.checked) {
            const event = new Event('change');
            radio.dispatchEvent(event);
        }
    });
    
    thirdPartyRadios.forEach(radio => {
        if (radio.checked) {
            const event = new Event('change');
            radio.dispatchEvent(event);
        }
    });
    
    fullTimeRadios.forEach(radio => {
        if (radio.checked) {
            const event = new Event('change');
            radio.dispatchEvent(event);
        }
    });
    
    // Add a notification to inform the user their data was loaded
    const formContainer = document.querySelector('.form-container');
    if (formContainer) {
        const notification = document.createElement('div');
        notification.className = 'data-loaded-notification';
        notification.innerHTML = `
            <i class="fas fa-info-circle"></i>
            <p>Your previously saved data has been loaded. You can continue where you left off.</p>
        `;
        
        // Insert at the beginning of the form container
        formContainer.insertBefore(notification, formContainer.firstChild);
        
        // Add style for the notification
        const style = document.createElement('style');
        style.textContent = `
            .data-loaded-notification {
                background-color: #e7f3fe;
                border-left: 4px solid #2196F3;
                margin-bottom: 15px;
                padding: 12px;
                display: flex;
                align-items: center;
                border-radius: 4px;
            }
            .data-loaded-notification i {
                color: #2196F3;
                font-size: 20px;
                margin-right: 10px;
            }
            .data-loaded-notification p {
                margin: 0;
                color: #0c5460;
            }
        `;
        document.head.appendChild(style);
        
        // Remove the notification after 10 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => notification.remove(), 500);
        }, 10000);
    }
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
