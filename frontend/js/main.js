// Main JavaScript for Admin AI website

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add js-enabled class to body to enable animations
    document.body.classList.add('js-enabled');
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';
    
    // Create mobile menu content
    const navLinks = document.querySelector('.nav-links').cloneNode(true);
    const authButtons = document.querySelector('.auth-buttons').cloneNode(true);
    const closeButton = document.createElement('div');
    closeButton.className = 'close-menu';
    closeButton.innerHTML = '&times;';
    
    // Append elements to mobile menu
    mobileMenu.appendChild(closeButton);
    mobileMenu.appendChild(navLinks);
    mobileMenu.appendChild(authButtons);
    document.body.appendChild(mobileMenu);
    
    // Toggle mobile menu
    hamburger.addEventListener('click', function() {
        mobileMenu.classList.add('active');
    });
    
    closeButton.addEventListener('click', function() {
        mobileMenu.classList.remove('active');
    });
    
    // Initialize animations for statistics
    const statBlocks = document.querySelectorAll('.stat-block');
    statBlocks.forEach((block, index) => {
        block.style.animationDelay = `${0.3 * (index + 1)}s`;
        block.style.animation = 'fadeIn 0.8s ease forwards';
    });
    
    // Initialize scroll animations
    function initScrollAnimations() {
        // Elements to animate on scroll
        const animateOnScroll = [
            { selector: '.card', animation: 'fadeIn', stagger: 0.2 },
            { selector: '.step', animation: 'fadeIn', stagger: 0.2 },
            { selector: '.testimonial', animation: 'fadeIn', stagger: 0.2 },
            { selector: '.advantage-item', animation: 'fadeInLeft', stagger: 0.15 },
            { selector: '.resource-card', animation: 'fadeInRight', stagger: 0.15 },
        ];
        
        // Apply animations
        animateOnScroll.forEach(item => {
            const elements = document.querySelectorAll(item.selector);
            elements.forEach((element, index) => {
                element.dataset.animation = item.animation;
                element.dataset.delay = (item.stagger * index).toFixed(2);
            });
        });
        
        // Check if elements are in viewport and trigger animations
        checkScrollAnimations();
        window.addEventListener('scroll', checkScrollAnimations);
    }
    
    // Helper function to check if element is in viewport
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.85 &&
            rect.bottom >= 0
        );
    }
    
    // Check and trigger animations for elements in viewport
    function checkScrollAnimations() {
        const elements = document.querySelectorAll('[data-animation]');
        
        elements.forEach(element => {
            if (isInViewport(element) && !element.classList.contains('animated')) {
                const animation = element.dataset.animation;
                const delay = element.dataset.delay || 0;
                
                element.style.animationDelay = `${delay}s`;
                element.style.animation = `${animation} 0.8s ease forwards`;
                element.classList.add('animated');
            }
        });
    }
    
    // Initialize scroll animations when page is loaded
    initScrollAnimations();
    
    // Testimonial slider functionality
    const testimonials = document.querySelectorAll('.testimonial');
    let currentTestimonial = 0;
    
    if (testimonials.length > 1) {
        setInterval(() => {
            testimonials[currentTestimonial].style.opacity = '0';
            currentTestimonial = (currentTestimonial + 1) % testimonials.length;
            setTimeout(() => {
                testimonials[currentTestimonial].style.opacity = '1';
            }, 500);
        }, 5000);
    }
    
    // Form validation for login and signup pages
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    showError(field, 'This field is required');
                } else {
                    clearError(field);
                    
                    // Email validation
                    if (field.type === 'email') {
                        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                        if (!emailRegex.test(field.value)) {
                            isValid = false;
                            showError(field, 'Please enter a valid email address');
                        }
                    }
                    
                    // Password validation
                    if (field.type === 'password' && field.id === 'password') {
                        if (field.value.length < 8) {
                            isValid = false;
                            showError(field, 'Password must be at least 8 characters long');
                        }
                    }
                    
                    // Password confirmation
                    if (field.id === 'confirmPassword') {
                        const password = document.getElementById('password');
                        if (field.value !== password.value) {
                            isValid = false;
                            showError(field, 'Passwords do not match');
                        }
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
    
    // Helper functions for form validation
    function showError(field, message) {
        const errorElement = field.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.textContent = message;
        } else {
            const error = document.createElement('div');
            error.className = 'error-message';
            error.textContent = message;
            error.style.color = 'var(--error-color)';
            error.style.fontSize = '0.8rem';
            error.style.marginTop = '0.3rem';
            field.insertAdjacentElement('afterend', error);
        }
        
        field.style.borderColor = 'var(--error-color)';
    }
    
    function clearError(field) {
        const errorElement = field.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.remove();
        }
        
        field.style.borderColor = 'var(--border-color)';
    }
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });
});
