const express = require('express');
const cors = require('cors');
const path = require('path');
const cron = require('node-cron');
const uscisUpdates = require('./services/uscisUpdates');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize updates
let policyUpdates = [];

// Fetch USCIS updates initially
uscisUpdates.fetchUpdates()
  .then(updates => {
    policyUpdates = updates;
    console.log('Initial USCIS updates fetched:', updates.length);
  })
  .catch(err => {
    console.error('Error fetching initial USCIS updates:', err);
  });

// Schedule update every 6 hours
cron.schedule('0 */6 * * *', async () => {
  try {
    const updates = await uscisUpdates.fetchUpdates();
    policyUpdates = updates;
    console.log('USCIS updates refreshed:', updates.length);
  } catch (err) {
    console.error('Error refreshing USCIS updates:', err);
  }
});

// API Routes
app.get('/api/uscis-updates', (req, res) => {
  res.json(policyUpdates);
});

// Start the server
app.listen(PORT, () => {
  console.log(`ImmigraAssist API server running on port ${PORT}`);
});
