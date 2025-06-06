const axios = require('axios');
const cheerio = require('cheerio');

// USCIS URLs to scrape for policy updates
const USCIS_POLICY_URL = 'https://www.uscis.gov/news/all-news';
const USCIS_POLICY_ALERTS_URL = 'https://www.uscis.gov/policy-manual/updates';

/**
 * Scrapes the USCIS website for the latest policy updates
 * @returns {Promise<Array>} Array of policy update objects
 */
async function fetchUpdates() {
  try {
    // Fetch news and policy updates from two sources
    const [newsUpdates, policyAlerts] = await Promise.all([
      fetchNewsUpdates(),
      fetchPolicyAlerts()
    ]);
    
    // Combine and sort by date (newest first)
    const allUpdates = [...newsUpdates, ...policyAlerts]
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 10); // Limit to 10 most recent updates
      
    return allUpdates;
  } catch (error) {
    console.error('Error fetching USCIS updates:', error);
    return getMockUpdates(); // Return mock data in case of error
  }
}

/**
 * Scrapes USCIS news updates
 * @returns {Promise<Array>} Array of news update objects
 */
async function fetchNewsUpdates() {
  try {
    const response = await axios.get(USCIS_POLICY_URL);
    const $ = cheerio.load(response.data);
    const updates = [];

    // Find and extract news items
    $('.views-row').each((i, element) => {
      try {
        const title = $(element).find('h3').text().trim();
        const date = $(element).find('.datetime').text().trim();
        const url = 'https://www.uscis.gov' + $(element).find('a').attr('href');
        const type = 'News Update';

        if (title && date) {
          updates.push({ title, date, url, type });
        }
      } catch (err) {
        console.error('Error parsing news item:', err);
      }
    });

    return updates;
  } catch (error) {
    console.error('Error fetching news updates:', error);
    return [];
  }
}

/**
 * Scrapes USCIS policy manual alerts
 * @returns {Promise<Array>} Array of policy alert objects
 */
async function fetchPolicyAlerts() {
  try {
    const response = await axios.get(USCIS_POLICY_ALERTS_URL);
    const $ = cheerio.load(response.data);
    const updates = [];

    // Find and extract policy alerts
    $('.usa-accordion__heading').each((i, element) => {
      try {
        const title = $(element).text().trim();
        const dateMatch = title.match(/([A-Z][a-z]+ \d{1,2}, \d{4})/);
        const date = dateMatch ? dateMatch[0] : '';
        const url = 'https://www.uscis.gov/policy-manual/updates';
        const type = 'Policy Alert';

        if (title && date) {
          updates.push({ 
            title: title.replace(date, '').trim(), 
            date, 
            url, 
            type 
          });
        }
      } catch (err) {
        console.error('Error parsing policy alert:', err);
      }
    });

    return updates;
  } catch (error) {
    console.error('Error fetching policy alerts:', error);
    return [];
  }
}

// Mock data for testing when USCIS site can't be accessed
function getMockUpdates() {
  return [
    {
      title: "USCIS Announces FY 2026 H-1B Cap Season",
      date: "May 20, 2025",
      url: "https://www.uscis.gov/newsroom/news-releases/uscis-announces-fy-2026-h-1b-cap-season",
      type: "News Update"
    },
    {
      title: "USCIS Updates Policy on Employment Authorization for Certain H-4 Dependent Spouses",
      date: "May 15, 2025",
      url: "https://www.uscis.gov/newsroom/alerts/uscis-updates-policy-on-employment-authorization-for-certain-h-4-dependent-spouses",
      type: "Policy Alert"
    },
    {
      title: "DHS Designates Ukraine for Temporary Protected Status for Additional 18 Months",
      date: "May 10, 2025",
      url: "https://www.uscis.gov/newsroom/news-releases/dhs-designates-ukraine-for-temporary-protected-status-for-additional-18-months",
      type: "News Update"
    },
    {
      title: "USCIS Releases New Editions of Forms I-129 and I-140",
      date: "May 5, 2025",
      url: "https://www.uscis.gov/newsroom/alerts/uscis-releases-new-editions-of-forms-i-129-and-i-140",
      type: "Policy Alert"
    },
    {
      title: "USCIS Expands Premium Processing for Additional Form Types",
      date: "April 28, 2025",
      url: "https://www.uscis.gov/newsroom/news-releases/uscis-expands-premium-processing-for-additional-form-types",
      type: "News Update"
    }
  ];
}

module.exports = {
  fetchUpdates,
  getMockUpdates
};
