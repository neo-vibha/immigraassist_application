// Admin Corner specific JavaScript

// Initialize on document load
document.addEventListener('DOMContentLoaded', function() {
    // Set progress bar widths based on data attributes
    initializeProgressBars();
    
    // Initialize filters for petition cards
    initializeFilters();
    
    // Initialize mobile menu toggle
    initializeMobileMenu();
});

// Set progress bar widths based on data-percentage attributes
function initializeProgressBars() {
    const progressFills = document.querySelectorAll('.progress-fill');
    progressFills.forEach(fill => {
        const percentage = fill.getAttribute('data-percentage');
        if (percentage) {
            fill.style.width = percentage + '%';
        }
    });
}

// Handle petition filtering and search
function initializeFilters() {
    const statusFilter = document.getElementById('status-filter');
    const caseTypeFilter = document.getElementById('case-type-filter');
    const searchInput = document.getElementById('search-petition');
    const petitionCards = document.querySelectorAll('.petition-card');
    
    // Function to filter cards based on current filter values
    function filterCards() {
        const statusValue = statusFilter.value;
        const caseTypeValue = caseTypeFilter.value;
        const searchValue = searchInput.value.toLowerCase();
        
        petitionCards.forEach(card => {
            // Status filter
            const statusMatch = statusValue === 'all' || 
                card.querySelector('.status-badge').textContent.toLowerCase() === statusValue.toLowerCase();
            
            // Case type filter
            const caseTypeMatch = caseTypeValue === 'all' || 
                card.querySelector('.petition-type').textContent.toLowerCase().includes(caseTypeValue.toLowerCase());
            
            // Search filter
            const beneficiaryName = card.querySelector('.petition-title').textContent.toLowerCase();
            const searchMatch = searchValue === '' || beneficiaryName.includes(searchValue);
            
            // Show/hide based on combined filters
            if (statusMatch && caseTypeMatch && searchMatch) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    // Add event listeners
    if (statusFilter) statusFilter.addEventListener('change', filterCards);
    if (caseTypeFilter) caseTypeFilter.addEventListener('change', filterCards);
    if (searchInput) searchInput.addEventListener('input', filterCards);
}

// Toggle mobile menu
function initializeMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show-sidebar');
        });
    }
}
