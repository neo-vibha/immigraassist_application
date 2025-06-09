$(document).ready(function() {
    let isResizing = false;
    let lastDownX = 0;
    let lastDownY = 0;
    let startWidth = 0;
    let startHeight = 0;
    let isBotOpen = false;

    // Add the bot toggle button to the page if it doesn't exist
    if ($('.copilot-button').length === 0) {
        $('body').append('<div class="copilot-button"><i class="fas fa-robot"></i></div>');
    }

    // Toggle bot visibility when button is clicked
    $('.copilot-button').on('click', function() {
        if (isBotOpen) {
            $('#copilot-container').hide();
            $('.copilot-button i').removeClass('fa-times').addClass('fa-robot');
        } else {
            $('#copilot-container').show();
            $('.copilot-button i').removeClass('fa-robot').addClass('fa-times');
        }
        isBotOpen = !isBotOpen;
    });

    // Resize functionality
    $('.resize-handle').on('mousedown', function(e) {
        isResizing = true;
        lastDownX = e.clientX;
        lastDownY = e.clientY;
        startWidth = $('#copilot-container').width();
        startHeight = $('#copilot-container').height();
        e.preventDefault();
    });

    $(document).on('mousemove', function(e) {
        if (!isResizing) return;

        const newWidth = startWidth + (e.clientX - lastDownX);
        const newHeight = startHeight + (e.clientY - lastDownY);

        // Set minimum size
        if (newWidth > 250 && newHeight > 300) {
            $('#copilot-container').width(newWidth);
            $('#copilot-container').height(newHeight);
        }
    });

    $(document).on('mouseup', function() {
        isResizing = false;
    });
});
