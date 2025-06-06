/**
 * ImmigraAssist API Client
 * Handles authentication and API requests
 */

// Initialize the API namespace
window.immigraAPI = window.immigraAPI || {};

// Base API URL - change this to your actual backend URL in production
const API_BASE_URL = 'http://localhost:5000/api';

// Authentication module
window.immigraAPI.auth = {
    // Register a new user
    async register(userData) {
        try {
            // For the prototype, we'll simulate successful registration
            // In production, this would make an actual API call
            console.log('Registering user:', userData);
            
            // Store user data in localStorage (simulating successful registration)
            localStorage.setItem('user', JSON.stringify({
                id: 'user-' + Date.now(),
                firstName: userData.firstName,
                lastName: userData.lastName,
                email: userData.email,
                phone: userData.phone
            }));
            
            // Set auth token
            localStorage.setItem('token', 'simulated-jwt-token-' + Date.now());
            
            return {
                success: true,
                message: 'Registration successful'
            };
        } catch (error) {
            console.error('Registration error:', error);
            return {
                success: false,
                message: error.message || 'Registration failed'
            };
        }
    },
    
    // Login a user
    async login(email, password) {
        try {
            console.log('Logging in user with backend:', email);
            
            // Make the actual login API call to the backend
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'email': email,
                    'password': password
                }),
                redirect: 'follow'
            });
            
            if (!response.ok) {
                throw new Error('Login failed');
            }
            const userData = await response.json();  // assuming backend returns JSON user data

            // Save user data to localStorage here
        localStorage.setItem("immigra_user", JSON.stringify(userData));

        return userData;  // or whatever you do after login
        
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }        
                
    },
    
    // Check if user is logged in
    isLoggedIn() {
        return !!localStorage.getItem('token');
    },
    
    // Get current user
    getCurrentUser() {
        // return JSON.parse(localStorage.getItem('user') || '{}');
        return JSON.parse(localStorage.getItem("immigra_user"));
    },
    
    // Logout
    async logout() {
        try {
            console.log('Logging out user with backend');
            
            // Make the actual logout API call to the backend
            const response = await fetch('/logout');
            
            // Clean up localStorage regardless of response
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            
            // Redirect to home or login page
            window.location.href = '/login';
            
            return true;
        } catch (error) {
            console.error('Logout error:', error);
            
            // Still clean up localStorage even if there was an error
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            
            return false;
        }
    }
};

// Document processing module
window.immigraAPI.documents = {
    // Upload a document
    async uploadDocument(documentType, file) {
        try {
            // For prototype, simulate document upload
            console.log(`Uploading ${documentType} document:`, file.name);
            
            // Simulate processing delay
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            return {
                success: true,
                documentId: 'doc-' + Date.now(),
                documentType,
                fileName: file.name,
                uploadDate: new Date().toISOString()
            };
        } catch (error) {
            console.error('Document upload error:', error);
            return {
                success: false,
                message: error.message || 'Document upload failed'
            };
        }
    },
    
    // Get document status
    async getDocumentStatus(documentId) {
        // For prototype, simulate document status
        return {
            status: 'processed',
            message: 'Document processed successfully'
        };
    }
};

// Visa processing module
window.immigraAPI.visa = {
    // Process visa application
    async processApplication(visaType, documents) {
        try {
            console.log(`Processing ${visaType} visa application`);
            
            // Simulate processing delay
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Simulate visa eligibility check
            const eligible = Math.random() > 0.3; // 70% chance of success
            
            return {
                success: true,
                eligible,
                applicationId: 'app-' + Date.now(),
                visaType,
                processingDate: new Date().toISOString(),
                factors: eligible ? [
                    'All required documents submitted',
                    'Document verification passed',
                    'Applicant meets qualification criteria'
                ] : [
                    'Missing required documents',
                    'Documentation issues found',
                    'Additional evidence required'
                ],
                recommendations: eligible ? [
                    'Application ready for submission',
                    'Schedule interview preparation',
                    'Review USCIS guidelines for next steps'
                ] : [
                    'Submit missing documentation',
                    'Consult with an immigration admin',
                    'Reapply after addressing issues'
                ]
            };
        } catch (error) {
            console.error('Visa processing error:', error);
            return {
                success: false,
                message: error.message || 'Visa processing failed'
            };
        }
    },
    
    async getUserPetition() {
        try {
            const currentUser = this.auth.getCurrentUser();
            const userId = currentUser?.user_id;
    
            if (!userId) {
                throw new Error("User ID not found.");
            }
    
            const response = await axios.get(`${baseUrl}/user_petition?user_id=${userId}`);
            const data = response.data;
    
            return data;
        } catch (error) {
            console.error('Error fetching user petition:', error);
            return {
                success: false,
                message: error.message || 'Failed to fetch petition data'
            };
        }
    },
    
    // Save petition data (for partial form submissions)
    async savePetitionData(formData) {
        try {
            console.log('Sending petition data to backend:', formData);
            
            // Send data to the backend API
            const response = await fetch('/api/user_petition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            // Check if the save was successful
            if (result.success) {
                console.log('Petition data saved successfully:', result);
                return {
                    success: true,
                    message: 'Data saved successfully',
                    id: result.id
                };
            } else {
                console.error('Server rejected petition data:', result.message);
                return {
                    success: false,
                    message: result.message || 'Server rejected the data'
                };
            }
        } catch (error) {
            console.error('Error saving petition data:', error);
            return {
                success: false,
                message: error.message || 'Failed to save petition data'
            };
        }
    }
};

console.log('ImmigraAssist API client initialized');
