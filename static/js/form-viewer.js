// Form I-129 View and Download Functionality
document.addEventListener('DOMContentLoaded', function() {
    // View Form button functionality
    const viewFormBtn = document.getElementById('view-form-data');
    if(viewFormBtn) {
        viewFormBtn.addEventListener('click', function() {
            // Create modal to display form data
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content form-data-modal">
                    <div class="modal-header">
                        <h3>Form I-129 Data Summary</h3>
                        <button class="modal-close"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-data-summary">
                            <h4>Petitioner Information</h4>
                            <div class="data-row">
                                <span class="data-label">Company Name:</span>
                                <span class="data-value" id="summary-company-name">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">Federal EIN:</span>
                                <span class="data-value" id="summary-fein">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">Address:</span>
                                <span class="data-value" id="summary-address">Loading...</span>
                            </div>
                            
                            <h4>Basis for Classification</h4>
                            <div class="data-row">
                                <span class="data-label">Visa Type:</span>
                                <span class="data-value">H-1B Specialty Occupation</span>
                            </div>
                            
                            <h4>Beneficiary Information</h4>
                            <div class="data-row">
                                <span class="data-label">Full Name:</span>
                                <span class="data-value" id="summary-beneficiary-name">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">Country of Birth:</span>
                                <span class="data-value" id="summary-country">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">A-Number:</span>
                                <span class="data-value" id="summary-alien-number">Loading...</span>
                            </div>
                            
                            <h4>Employment Details</h4>
                            <div class="data-row">
                                <span class="data-label">Job Title:</span>
                                <span class="data-value" id="summary-job-title">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">LCA Number:</span>
                                <span class="data-value" id="summary-lca">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">Work Address:</span>
                                <span class="data-value" id="summary-work-address">Loading...</span>
                            </div>
                            <div class="data-row">
                                <span class="data-label">Wage:</span>
                                <span class="data-value" id="summary-wage">Loading...</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" id="modal-close-btn">Close</button>
                        <button class="btn-primary" id="modal-download-btn"><i class="fas fa-download"></i> Download PDF</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Populate the summary with actual form data
            setTimeout(() => {
                populateFormSummary();
            }, 300);
            
            // Handle modal close
            modal.querySelector('.modal-close').addEventListener('click', function() {
                document.body.removeChild(modal);
            });
            
            modal.querySelector('#modal-close-btn').addEventListener('click', function() {
                document.body.removeChild(modal);
            });
            
            // Handle download from modal
            modal.querySelector('#modal-download-btn').addEventListener('click', function() {
                generateAndDownloadPDF();
                document.body.removeChild(modal);
            });
        });
    }
    
    // Download PDF button functionality
    const downloadFormBtn = document.getElementById('download-form');
    if(downloadFormBtn) {
        downloadFormBtn.addEventListener('click', function() {
            generateAndDownloadPDF();
        });
    }
});

// Populate form summary with data from the form
function populateFormSummary() {
    // In a real app, this data would come from the actual form submission
    // or from a database/API. Here we're using example data.
    
    // Example form data (would normally be stored data)
    const formData = {
        // Petitioner Information
        companyName: "TechInnovate Solutions, Inc.",
        fein: "12-3456789",
        streetAddress: "123 Corporate Plaza",
        city: "San Francisco",
        state: "CA",
        zipCode: "94105",
        
        // Beneficiary Information
        firstName: "Raj",
        middleName: "",
        lastName: "Patel",
        alienNumber: "A-123456789",
        countryOfBirth: "India",
        
        // Employment Details
        jobTitle: "Software Engineer",
        lcaNumber: "I-200-22123-123456",
        workStreetAddress: "456 Tech Avenue",
        workCity: "San Francisco",
        workState: "CA", 
        workZipCode: "94105",
        wageAmount: "120,000",
        wagePeriod: "Year"
    };
    
    // Save this data for other functions to use
    window.formDataObj = formData;
    
    // Set values in summary
    document.getElementById('summary-company-name').textContent = formData.companyName;
    document.getElementById('summary-fein').textContent = formData.fein;
    document.getElementById('summary-address').textContent = 
        `${formData.streetAddress}, ${formData.city}, ${formData.state} ${formData.zipCode}`;
    
    document.getElementById('summary-beneficiary-name').textContent = 
        `${formData.firstName} ${formData.middleName ? formData.middleName + ' ' : ''}${formData.lastName}`;
    document.getElementById('summary-country').textContent = formData.countryOfBirth;
    document.getElementById('summary-alien-number').textContent = formData.alienNumber;
    
    document.getElementById('summary-job-title').textContent = formData.jobTitle;
    document.getElementById('summary-lca').textContent = formData.lcaNumber;
    document.getElementById('summary-work-address').textContent = 
        `${formData.workStreetAddress}, ${formData.workCity}, ${formData.workState} ${formData.workZipCode}`;
    document.getElementById('summary-wage').textContent = 
        `$${formData.wageAmount} per ${formData.wagePeriod}`;
}

// Generate and download PDF of the form
function generateAndDownloadPDF() {
    // Show loading indicator
    const loadingToast = document.createElement('div');
    loadingToast.className = 'toast-notification';
    loadingToast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Generating PDF...</span>
        </div>
    `;
    document.body.appendChild(loadingToast);
    
    // Simulate PDF generation delay
    setTimeout(() => {
        // Remove loading toast
        document.body.removeChild(loadingToast);
        
        // Show success toast
        const successToast = document.createElement('div');
        successToast.className = 'toast-notification success';
        successToast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-check-circle"></i>
                <span>Form I-129 PDF downloaded successfully</span>
            </div>
        `;
        document.body.appendChild(successToast);
        
        // Remove success toast after a few seconds
        setTimeout(() => {
            document.body.removeChild(successToast);
        }, 3000);
        
        // Create a fake download (in a real app, this would be a real file)
        const link = document.createElement('a');
        link.href = '#'; // In a real app, this would be a URL to the generated PDF
        link.download = 'Form_I-129_Petition.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, 2000);
}
