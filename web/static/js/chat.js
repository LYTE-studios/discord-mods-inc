// WebSocket connection and chat functionality
class ChatManager {
    constructor() {
        this.socket = null;
        this.messageHistory = document.getElementById('messageHistory');
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageText');
        this.fileInput = document.getElementById('fileInput');
        this.teamMembers = document.querySelectorAll('.team-member');
        this.currentTicket = document.getElementById('currentTicket');
        
        this.initialize();
    }

    initialize() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.setupHeartbeat();
    }

    connectWebSocket() {
        this.socket = new WebSocket(WEBSOCKET_URL);
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.updateTeamStatus('all', 'online');
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateTeamStatus('all', 'offline');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
    }

    setupEventListeners() {
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files[0]);
        });

        // Handle file drag and drop
        this.messageHistory.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.messageHistory.classList.add('drag-over');
        });

        this.messageHistory.addEventListener('dragleave', () => {
            this.messageHistory.classList.remove('drag-over');
        });

        this.messageHistory.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.messageHistory.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                this.handleFileUpload(e.dataTransfer.files[0]);
            }
        });
    }

    setupHeartbeat() {
        // Send heartbeat every 30 seconds to keep connection alive
        setInterval(() => {
            if (this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ type: 'heartbeat' }));
            }
        }, 30000);
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        const data = {
            type: 'message',
            content: message
        };

        this.socket.send(JSON.stringify(data));
        this.messageInput.value = '';
    }

    async handleFileUpload(file) {
        try {
            // Read file content
            const content = await this.readFileContent(file);
            
            // Prepare file data
            const fileData = {
                type: 'file_upload',
                file: {
                    name: file.name,
                    type: file.type,
                    content: content,
                    size: file.size
                }
            };

            // Send file through WebSocket
            this.socket.send(JSON.stringify(fileData));

        } catch (error) {
            console.error('File upload error:', error);
            this.showError('Failed to upload file: ' + error.message);
        }
    }

    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                resolve(e.target.result);
            };
            
            reader.onerror = (e) => {
                reject(new Error('Failed to read file'));
            };

            if (file.type.startsWith('text/') || file.type === 'application/json') {
                reader.readAsText(file);
            } else {
                reader.readAsDataURL(file);
            }
        });
    }

    async handleFileDownload(fileData) {
        try {
            const blob = await this.createFileBlob(fileData);
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = fileData.name;
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('File download error:', error);
            this.showError('Failed to download file: ' + error.message);
        }
    }

    createFileBlob(fileData) {
        if (fileData.content.startsWith('data:')) {
            // Handle base64 encoded files
            const base64Content = fileData.content.split(',')[1];
            const byteCharacters = atob(base64Content);
            const byteArrays = [];

            for (let offset = 0; offset < byteCharacters.length; offset += 512) {
                const slice = byteCharacters.slice(offset, offset + 512);
                const byteNumbers = new Array(slice.length);
                
                for (let i = 0; i < slice.length; i++) {
                    byteNumbers[i] = slice.charCodeAt(i);
                }
                
                byteArrays.push(new Uint8Array(byteNumbers));
            }

            return new Blob(byteArrays, { type: fileData.type });
        } else {
            // Handle text files
            return new Blob([fileData.content], { type: fileData.type });
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message':
                this.addMessage(data);
                break;
            case 'status':
                this.updateTeamStatus(data.role, data.status);
                break;
            case 'ticket':
                this.updateTicket(data);
                break;
            case 'file_download':
                this.handleFileDownload(data.file);
                break;
            case 'error':
                this.showError(data.message);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    addMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.role === 'user' ? 'message-user' : 'message-ai'}`;
        messageElement.dataset.role = message.role;

        messageElement.innerHTML = `
            <div class="message-header">
                <span class="message-author">${message.role}</span>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            ${message.ticket_id ? `
                <div class="message-ticket">
                    Ticket: #${message.ticket_id}
                </div>
            ` : ''}
        `;

        this.messageHistory.appendChild(messageElement);
        this.scrollToBottom();
    }

    updateTeamStatus(role, status) {
        const members = role === 'all' ? 
            this.teamMembers : 
            document.querySelectorAll(`.team-member[data-role="${role}"]`);

        members.forEach(member => {
            const statusDot = member.querySelector('.status-dot');
            statusDot.style.backgroundColor = status === 'online' ? 
                'var(--success-color)' : 'var(--error-color)';
        });
    }

    updateTicket(ticketData) {
        this.currentTicket.innerHTML = ticketData.ticket ? `
            <div class="ticket-header">
                <span class="ticket-id">#${ticketData.ticket.id}</span>
                <span class="ticket-status">${ticketData.ticket.status}</span>
            </div>
            <div class="ticket-title">${this.escapeHtml(ticketData.ticket.title)}</div>
            <div class="ticket-description">${this.escapeHtml(ticketData.ticket.description)}</div>
            <div class="ticket-assignee">
                Assigned to: ${this.escapeHtml(ticketData.ticket.assignee)}
            </div>
        ` : '<p>No active ticket</p>';
    }

    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'message message-error';
        errorElement.innerHTML = `
            <div class="message-content">
                Error: ${this.escapeHtml(message)}
            </div>
        `;
        this.messageHistory.appendChild(errorElement);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.messageHistory.scrollTop = this.messageHistory.scrollHeight;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatManager = new ChatManager();
});