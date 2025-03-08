// Main application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat application initialized');
    
    // Add initial welcome message
    const chatBox = document.getElementById('chatBox');
    if (chatBox && chatBox.children.length === 0) {
        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'message bot-message';
        welcomeMsg.textContent = 'Hello! How can I help you with your tractor needs today?';
        chatBox.appendChild(welcomeMsg);
    }
});
