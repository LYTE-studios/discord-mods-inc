document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageText');
    const messagesContainer = document.querySelector('.messages-container');

    // Auto-resize textarea as user types
    messageInput.addEventListener('input', function() {
        // Reset height to auto to get the correct scrollHeight
        this.style.height = 'auto';
        // Set new height based on content (max 120px)
        const newHeight = Math.min(this.scrollHeight, 120);
        this.style.height = newHeight + 'px';
    });

    // Handle Enter key (send on Enter, new line on Shift+Enter)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim()) {
                // Create temporary message element
                const messageContent = this.value.trim();
                const tempMessage = createMessageElement(messageContent);
                messagesContainer.appendChild(tempMessage);
                scrollToBottom();
                
                // Submit the form
                messageForm.submit();
            }
        }
    });

    // Focus input when clicking anywhere in the messages container
    messagesContainer.addEventListener('click', function(e) {
        // Only focus if not clicking on a link or button
        if (!e.target.closest('a') && !e.target.closest('button')) {
            messageInput.focus();
        }
    });

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

    // Create message element
    function createMessageElement(content) {
        const div = document.createElement('div');
        div.className = 'message message-user';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const author = document.createElement('span');
        author.className = 'message-author';
        author.textContent = 'You';
        
        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        header.appendChild(author);
        header.appendChild(time);
        div.appendChild(header);
        div.appendChild(messageContent);
        
        return div;
    }

    // Scroll to bottom of messages
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Auto-focus input on page load
    messageInput.focus();

    // Initial scroll to bottom
    scrollToBottom();
});