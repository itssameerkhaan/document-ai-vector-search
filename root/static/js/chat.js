function autoExpand(textarea) {
    const container = textarea.closest('.input-container');
    const currentScrollPos = container.offsetTop;
    
    textarea.style.height = 'auto';
    const newHeight = Math.max(44, Math.min(textarea.scrollHeight, 200));
    textarea.style.height = newHeight + 'px';
}

// Better markdown formatter
function formatMarkdown(text) {
    // First, convert **bold** to <strong>
    text = text.replace(/\*\*([^\*]+?)\*\*/g, '<strong>$1</strong>');
    
    // Split text into lines
    let lines = text.split('\n');
    let html = '';
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Check if line starts with * (bullet point)
        if (line.startsWith('*')) {
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            // Remove the * and add as list item
            html += '<li>' + line.substring(1).trim() + '</li>';
        } else {
            // If we were in a list, close it
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            // Add regular line
            if (line) {
                html += '<p>' + line + '</p>';
            }
        }
    }
    
    // Close list if still open
    if (inList) {
        html += '</ul>';
    }
    
    return html;
}

async function sendMessage() {
    console.log("submitting .................................")
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (message === '') return;
    
    const chatBox = document.querySelector('.output_section');
    
    // Remove empty state if it exists
    const emptyState = chatBox.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create user message element FIRST
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user-message';
    
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    userMessageDiv.innerHTML = `
        <div>${message}</div>
        <div class="timestamp">${timeString}</div>
    `;
    
    chatBox.appendChild(userMessageDiv);
    
    // Clear input immediately after showing user message
    input.value = '';
    input.style.height = 'auto';
    
    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Show loading animation
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message loading-message';
    loadingDiv.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatBox.appendChild(loadingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    try {
        // Send to Flask backend and WAIT for response
        const response = await fetch(`/process?message=${encodeURIComponent(message)}`);
        const data = await response.json();
        console.log("RECEIVED DATA IS :- ", data);
        
        // Remove loading animation
        loadingDiv.remove();
        
        // Create bot response message with formatted markdown
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'message bot-message';
        
        // Format the AI response
        const formattedResponse = formatMarkdown(data.received);
        
        botMessageDiv.innerHTML = `
            <div class="bot-content">${formattedResponse}</div>
            <div class="timestamp">${timeString}</div>
        `;
        
        chatBox.appendChild(botMessageDiv);
        
    } catch (error) {
        // Remove loading animation on error
        loadingDiv.remove();
        
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message bot-message';
        errorDiv.innerHTML = `
            <div class="bot-content"><p>Sorry, something went wrong. Please try again.</p></div>
            <div class="timestamp">${timeString}</div>
        `;
        chatBox.appendChild(errorDiv);
    }
    
    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Focus back on input
    input.focus();
}

window.onload = function() {
  fetch('/reset');
};



document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.querySelector('.chat-input');
    
    // Auto-expand textarea as user types
    textarea.addEventListener('input', function() {
        autoExpand(this);
    });
    
    // Attach button functionality
    document.querySelector('.attach-button').addEventListener('click', function() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.onchange = function(e) {
            const files = Array.from(e.target.files);
            console.log('Files selected:', files);
            // You can add file upload logic here
        };
        input.click();
    });

    // Allow Enter key to send message (Shift+Enter for new line)
    document.getElementById('messageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent new line in textarea
            sendMessage();
        }
    });
});