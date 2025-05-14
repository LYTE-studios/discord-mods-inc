document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageText');
    const messagesContainer = document.querySelector('.messages-container');

    // Auto-resize textarea as user types
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        const newHeight = Math.min(this.scrollHeight, 120);
        this.style.height = newHeight + 'px';
    });

    // Handle Enter key (send on Enter, new line on Shift+Enter)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim()) {
                handleSubmit();
            }
        }
    });

    // Focus input when clicking anywhere in the messages container
    messagesContainer.addEventListener('click', function(e) {
        if (!e.target.closest('a') && !e.target.closest('button')) {
            messageInput.focus();
        }
    });

    // Handle form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent form from submitting normally
        handleSubmit();
        return false; // Extra prevention of form submission
    });

    async function handleSubmit() {
        const messageContent = messageInput.value.trim();
        if (!messageContent) return;

        // Add user message immediately
        const userMessage = createMessageElement(messageContent, false);
        messagesContainer.appendChild(userMessage);
        scrollToBottom();

        // Add loading message
        const loadingMessage = createLoadingMessage();
        messagesContainer.appendChild(loadingMessage);
        scrollToBottom();

        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';

        try {
            // Create form data
            const formData = new FormData();
            formData.append('message', messageContent);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            // Send message to server using fetch
            const response = await fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            
            // Remove loading message
            loadingMessage.remove();

            // Add AI response
            if (data.status === 'success' && data.message) {
                const aiMessageElement = createMessageElement(data.message.content, true);
                messagesContainer.appendChild(aiMessageElement);
                scrollToBottom();
            } else {
                throw new Error(data.message || 'Invalid response format');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingMessage.remove();
            // Show error message
            const errorMessage = createErrorMessage(error.message);
            messagesContainer.appendChild(errorMessage);
            scrollToBottom();
        }
    }

    // Create message element
    function createMessageElement(content, isAi) {
        const div = document.createElement('div');
        div.className = `message ${isAi ? 'message-ai' : 'message-user'}`;
        div.innerHTML = `
            <div class="message-header">
                <span class="message-author">${isAi ? (current_chat_type === 'cto' ? 'CTO' : 'Developer') : 'You'}</span>
                <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div class="message-content">${content}</div>
        `;
        return div;
    }

    // Create loading message element
    function createLoadingMessage() {
        const div = document.createElement('div');
        div.className = 'message message-ai message-loading';
        div.innerHTML = `
            <div class="message-header">
                <span class="message-author">${current_chat_type === 'cto' ? 'CTO' : 'Developer'}</span>
                <span class="message-time">...</span>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        return div;
    }

    // Create error message element
    function createErrorMessage(message) {
        const div = document.createElement('div');
        div.className = 'message message-error';
        div.innerHTML = `
            <div class="message-content">
                ${message || 'Failed to send message. Please try again.'}
            </div>
        `;
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