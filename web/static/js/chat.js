document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageText');
    const messagesContainer = document.querySelector('.messages-container');

    // Auto-resize textarea as user types
    messageInput.addEventListener('input', function() {
        // Reset height to auto to get the correct scrollHeight
        this.style.height = 'auto';
        // Set new height based on content
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle Enter key (send on Enter, new line on Shift+Enter)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim()) {
                messageForm.submit();
            }
        }
    });

    // Focus input when clicking anywhere in the messages container
    messagesContainer.addEventListener('click', function() {
        messageInput.focus();
    });

    // Scroll to bottom of messages
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Scroll to bottom on page load
    scrollToBottom();

    // Handle form submission
    messageForm.addEventListener('submit', function(e) {
        const messageContent = messageInput.value.trim();
        if (!messageContent) {
            e.preventDefault();
            return;
        }

        // Clear input after sending
        messageInput.value = '';
        messageInput.style.height = 'auto';
    });

    // Auto-focus input on page load
    messageInput.focus();
});