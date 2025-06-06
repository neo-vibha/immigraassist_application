// Attorney Review Form JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Handle decision buttons
    const decisionButtons = document.querySelectorAll('.decision-btn');
    const decisionForm = document.getElementById('petition-decision-form');
    const decisionStatusInput = document.getElementById('decision-status');
    
    if (decisionButtons && decisionForm) {
        decisionButtons.forEach(button => {
            button.addEventListener('click', function() {
                const status = this.getAttribute('data-status');
                decisionStatusInput.value = status;
                
                // Show confirmation dialog
                if (confirm(`Are you sure you want to mark this petition as "${status}"?`)) {
                    decisionForm.submit();
                }
            });
        });
    }
    
    // Handle document viewer
    const viewDocButtons = document.querySelectorAll('.view-doc-btn');
    const documentViewerModal = document.getElementById('documentViewerModal');
    
    if (viewDocButtons && documentViewerModal) {
        viewDocButtons.forEach(button => {
            button.addEventListener('click', function() {
                const docId = this.getAttribute('data-doc-id');
                // Here you would typically fetch the document content via AJAX
                // and display it in the modal
                
                // For now, we'll just show the modal with a placeholder
                const modalBody = documentViewerModal.querySelector('.modal-body');
                modalBody.innerHTML = `<div class="text-center p-5">
                    <i class="fas fa-spinner fa-spin fa-3x mb-3"></i>
                    <p>Loading document ID: ${docId}...</p>
                </div>`;
                
                // Show the modal using Bootstrap's modal API
                const modal = new bootstrap.Modal(documentViewerModal);
                modal.show();
            });
        });
    }
    
    // Handle feedback saving
    const saveFeedbackBtn = document.getElementById('save-feedback-btn');
    const feedbackNotes = document.getElementById('feedback-notes');
    
    if (saveFeedbackBtn && feedbackNotes) {
        saveFeedbackBtn.addEventListener('click', function() {
            const notes = feedbackNotes.value.trim();
            const petitionId = this.getAttribute('data-petition-id');
            
            if (!notes) {
                alert('Please enter feedback notes before saving.');
                return;
            }
            
            // Here you would typically send an AJAX request to save the feedback
            // For now, we'll just show a success message
            alert('Feedback saved successfully!');
        });
    }
    
    // Initialize progress bars
    const progressFills = document.querySelectorAll('.progress-fill');
    progressFills.forEach(fill => {
        const percentage = fill.getAttribute('data-percentage');
        fill.style.width = `${percentage}%`;
    });
    
    // Handle re-check matches button
    const checkMatchesBtn = document.getElementById('check-matches-btn');
    if (checkMatchesBtn) {
        checkMatchesBtn.addEventListener('click', function() {
            // Here you would typically send an AJAX request to re-check matches
            // For now, we'll just show a loading indicator and success message
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
            this.disabled = true;
            
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-sync-alt"></i> Re-Check Matches';
                this.disabled = false;
                alert('Document matching check completed!');
            }, 2000);
        });
    }
});
