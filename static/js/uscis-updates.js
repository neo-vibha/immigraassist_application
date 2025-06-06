/**
 * USCIS Policy Updates Integration
 * For ImmigraAssist Dashboard
 */

// API endpoint for USCIS updates
const API_URL = 'http://localhost:3000/api/uscis-updates';

// Function to fetch USCIS updates from our backend API
async function fetchUSCISUpdates() {
  try {
    const response = await fetch(API_URL);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const updates = await response.json();
    return updates;
  } catch (error) {
    console.error('Error fetching USCIS updates:', error);
    return getFallbackUpdates();
  }
}

// Function to update the news ticker with the fetched updates
function updateNewsTicker(updates) {
  const tickerItems = document.querySelector('.ticker-items');
  
  // Clear existing ticker items
  if (tickerItems) {
    tickerItems.innerHTML = '';
    
    // Add new updates to the ticker
    updates.forEach(update => {
      const span = document.createElement('span');
      
      // Create link element inside span
      const link = document.createElement('a');
      link.href = update.url;
      link.target = '_blank';
      link.textContent = update.title;
      link.className = 'ticker-link';
      
      // Add error handling for broken links
      link.addEventListener('click', function(e) {
        // If the link might be broken, provide a fallback
        if (update.url.includes('uscis.gov')) {
          // Store the original URL for reference
          link.setAttribute('data-original-url', update.url);
          
          // Add click handler to handle potential 404s by redirecting to USCIS homepage if needed
          e.preventDefault();
          
          // Open in new window so we can control the experience
          const newWindow = window.open('about:blank', '_blank');
          
          // Attempt to fetch the URL to check if it's valid
          fetch(update.url, { mode: 'no-cors' })
            .then(() => {
              // If successful, navigate to the URL
              newWindow.location.href = update.url;
            })
            .catch(() => {
              // If failed, redirect to USCIS homepage with a search query
              const searchQuery = encodeURIComponent(update.title);
              newWindow.location.href = `https://www.uscis.gov/search?query=${searchQuery}`;
              console.warn(`Redirected from broken link: ${update.url}`);
            });
        }
      });
      
      // Add icon based on update type
      const icon = document.createElement('i');
      icon.className = update.type.includes('Policy') 
        ? 'fas fa-file-alt policy-icon' 
        : 'fas fa-newspaper news-icon';
      
      span.appendChild(icon);
      span.appendChild(document.createTextNode(' '));
      span.appendChild(link);
      
      tickerItems.appendChild(span);
    });
  } else {
    console.error('Ticker items container not found');
  }
  
  // Also update the Recent USCIS Policy Updates section
  updatePolicyUpdatesSection(updates);
}

// Fallback updates in case API is not available
function getFallbackUpdates() {
  return [
    {
      title: "USCIS announces new H1B visa registration process for FY2026",
      date: "May 15, 2025",
      url: "https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations",
      type: "News Update"
    },
    {
      title: "Premium processing expanded for certain employment-based green card applications",
      date: "May 10, 2025",
      url: "https://www.uscis.gov/forms/all-forms",
      type: "Policy Alert"
    },
    {
      title: "L1 visa adjudication guidance updated to streamline inter-company transfers",
      date: "May 5, 2025",
      url: "https://www.uscis.gov/working-in-the-united-states/temporary-nonimmigrant-workers/l-nonimmigrant-visas",
      type: "Policy Alert"
    },
    {
      title: "USCIS releases new edition of Form I-129 for nonimmigrant worker petitions",
      date: "April 28, 2025",
      url: "https://www.uscis.gov/i-129",
      type: "News Update"
    },
    {
      title: "FY2026 H1B cap registration period to open on March 1, 2026",
      date: "April 20, 2025",
      url: "https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations",
      type: "News Update"
    }
  ];
}

// Add a USCIS updates section to the dashboard
function addUSCISUpdatesSection() {
  fetchUSCISUpdates().then(updates => {
    // Update the news ticker and policy updates section
    updateNewsTicker(updates);
  });
}

// Create a detailed USCIS updates section
function createDetailedUpdatesSection(updates) {
  const dashboardContent = document.querySelector('.dashboard-content');
  const sidebarContainer = document.querySelector('.sidebar-container');
  
  if (sidebarContainer) {
    // If the sidebar already exists, update it
    const updatesList = sidebarContainer.querySelector('.updates-list');
    if (updatesList) {
      updatesList.innerHTML = '';
      renderUpdatesInContainer(updates, updatesList);
    }
  } else if (dashboardContent) {
    // Create new sidebar container
    const sidebar = document.createElement('div');
    sidebar.className = 'sidebar-container';
    
    const header = document.createElement('div');
    header.className = 'section-header';
    
    const title = document.createElement('h2');
    title.innerHTML = '<i class="fas fa-globe-americas"></i> USCIS Policy Updates';
    
    const description = document.createElement('p');
    description.textContent = 'Latest immigration policy changes and news';
    
    header.appendChild(title);
    header.appendChild(description);
    
    const updatesList = document.createElement('div');
    updatesList.className = 'updates-list';
    
    renderUpdatesInContainer(updates, updatesList);
    
    sidebar.appendChild(header);
    sidebar.appendChild(updatesList);
    
    // Add view all button
    const viewAllBtn = document.createElement('a');
    viewAllBtn.href = 'https://www.uscis.gov/news/all-news';
    viewAllBtn.target = '_blank';
    viewAllBtn.className = 'btn-primary view-all-btn';
    viewAllBtn.innerHTML = 'View All Updates <i class="fas fa-external-link-alt"></i>';
    
    sidebar.appendChild(viewAllBtn);
    
    // Add to dashboard
    dashboardContent.appendChild(sidebar);
  }
}

// Function to update the Recent USCIS Policy Updates section
function updatePolicyUpdatesSection(updates) {
  // Get the policy updates container
  const policyUpdateList = document.getElementById('policy-update-list');
  
  if (policyUpdateList) {
    // Clear existing updates
    policyUpdateList.innerHTML = '';
    
    // Get all updates - limit to 10
    const limitedUpdates = updates.slice(0, 10);
    
    // If there are no updates, show a message
    if (limitedUpdates.length === 0) {
      const noUpdates = document.createElement('div');
      noUpdates.className = 'no-updates';
      noUpdates.textContent = 'No recent updates available.';
      policyUpdateList.appendChild(noUpdates);
      return;
    }
    
    // Create a carousel container
    const carouselContainer = document.createElement('div');
    carouselContainer.className = 'updates-carousel-container';
    
    // Create carousel track for continuous motion
    const carouselTrack = document.createElement('div');
    carouselTrack.className = 'updates-carousel-track';
    
    // Add each update to the carousel - duplicating items for continuous scroll
    const createUpdateItem = (update) => {
      const updateItem = document.createElement('div');
      updateItem.className = 'update-item';
      
      // Create update date
      const updateDate = document.createElement('div');
      updateDate.className = 'update-date';
      updateDate.textContent = update.date;
      
      // Create update type badge with icon
      const updateType = document.createElement('div');
      updateType.className = `update-type ${update.type.toLowerCase().replace(' ', '-')}`;
      const typeIcon = document.createElement('i');
      typeIcon.className = update.type.includes('Policy') 
        ? 'fas fa-file-alt' 
        : 'fas fa-newspaper';
      updateType.appendChild(typeIcon);
      updateType.appendChild(document.createTextNode(` ${update.type}`));
      
      // Create title
      const updateTitle = document.createElement('h4');
      updateTitle.className = 'update-title';
      updateTitle.textContent = update.title;
      
      // Create "Read More" link
      const readMore = document.createElement('a');
      readMore.href = update.url;
      readMore.target = '_blank';
      readMore.className = 'read-more';
      readMore.innerHTML = 'Read More <i class="fas fa-arrow-right"></i>';
      
      // Add error handling for broken links
      readMore.addEventListener('click', function(e) {
        // If the link might be broken, provide a fallback
        if (update.url.includes('uscis.gov')) {
          // Store the original URL for reference
          readMore.setAttribute('data-original-url', update.url);
          
          // Add click handler to handle potential 404s
          e.preventDefault();
          
          // Open in new window so we can control the experience
          const newWindow = window.open('about:blank', '_blank');
          
          // Attempt to fetch the URL to check if it's valid
          fetch(update.url, { mode: 'no-cors' })
            .then(() => {
              // If successful, navigate to the URL
              newWindow.location.href = update.url;
            })
            .catch(() => {
              // If failed, redirect to USCIS homepage with a search query
              const searchQuery = encodeURIComponent(update.title);
              newWindow.location.href = `https://www.uscis.gov/search?query=${searchQuery}`;
              console.warn(`Redirected from broken link: ${update.url}`);
            });
        }
      });
      
      // Add elements to the update item
      updateItem.appendChild(updateDate);
      updateItem.appendChild(updateType);
      updateItem.appendChild(updateTitle);
      updateItem.appendChild(readMore);
      
      return updateItem;
    };
    
    // Create the initial set of items
    limitedUpdates.forEach(update => {
      carouselTrack.appendChild(createUpdateItem(update));
    });
    
    // Duplicate items for continuous scrolling
    limitedUpdates.forEach(update => {
      carouselTrack.appendChild(createUpdateItem(update));
    });
    
    // Add the carousel track to the container
    carouselContainer.appendChild(carouselTrack);
    
    // Add controls to pause/resume animation
    const carouselControls = document.createElement('div');
    carouselControls.className = 'updates-carousel-controls';
    
    const pauseButton = document.createElement('button');
    pauseButton.className = 'carousel-control';
    pauseButton.innerHTML = '<i class="fas fa-pause"></i>';
    pauseButton.addEventListener('click', function() {
      if (carouselTrack.classList.contains('paused')) {
        carouselTrack.classList.remove('paused');
        this.innerHTML = '<i class="fas fa-pause"></i>';
      } else {
        carouselTrack.classList.add('paused');
        this.innerHTML = '<i class="fas fa-play"></i>';
      }
    });
    
    carouselControls.appendChild(pauseButton);
    carouselContainer.appendChild(carouselControls);
    
    // Add the carousel container to the policy update list
    policyUpdateList.appendChild(carouselContainer);
    
    // Start the animation after a short delay
    setTimeout(() => {
      carouselTrack.classList.add('animate');
    }, 500);
  } else {
    console.error('Policy update list container not found');
  }
}

// Helper function to render updates in a container
function renderUpdatesInContainer(updates, container) {
  updates.slice(0, 5).forEach(update => {
    const updateItem = document.createElement('div');
    updateItem.className = 'update-item';
    
    const updateType = document.createElement('div');
    updateType.className = `update-type ${update.type.toLowerCase().replace(' ', '-')}`;
    updateType.innerHTML = `<i class="${update.type.includes('Policy') ? 'fas fa-file-alt' : 'fas fa-newspaper'}"></i> ${update.type}`;
    
    const updateTitle = document.createElement('h3');
    updateTitle.className = 'update-title';
    
    const updateLink = document.createElement('a');
    updateLink.href = update.url;
    updateLink.target = '_blank';
    updateLink.textContent = update.title;
    
    updateTitle.appendChild(updateLink);
    
    const updateDate = document.createElement('div');
    updateDate.className = 'update-date';
    updateDate.textContent = update.date;
    
    updateItem.appendChild(updateType);
    updateItem.appendChild(updateTitle);
    updateItem.appendChild(updateDate);
    
    container.appendChild(updateItem);
  });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Load USCIS updates
  addUSCISUpdatesSection();
  
  // Refresh updates every 30 minutes
  setInterval(addUSCISUpdatesSection, 30 * 60 * 1000);
});
