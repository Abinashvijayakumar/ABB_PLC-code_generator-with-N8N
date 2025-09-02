// FINAL SCRIPT.JS FOR FASTAPI ARCHITECTURE

document.addEventListener('DOMContentLoaded', function() {
    // --- 💻 DOM ELEMENTS ---
    const chatMessages = document.getElementById('chatMessages');
    const promptInput = document.getElementById('promptInput');
    const sendPromptBtn = document.getElementById('sendPrompt');
    
    // Output Elements from Tabbed View
    const codeOutput = document.getElementById('codeOutput');
    const variablesOutput = document.getElementById('variablesOutput');
    const simulationOutput = document.getElementById('simulationOutput');
    const verificationNotesOutput = document.getElementById('verificationNotesOutput');

    // Button Elements
    const downloadBtn = document.getElementById('downloadBtn');
    const validateBtn = document.getElementById('validateBtn');
    const copyBtn = document.querySelector('[title="Copy Code"]');
    
    // Tab Elements
    const tabs = document.querySelectorAll('.tab-button');
    const panes = document.querySelectorAll('.tab-pane');

    // --- 🎯 API ENDPOINTS ---
    // We NO LONGER use n8n. All generation requests go to our main orchestrator.
    const ORCHESTRATOR_URL = 'http://localhost:8000/generate';
    const VERIFICATION_SERVICE_URL = 'http://localhost:8002/verify';

    // --- 🚀 EVENT LISTENERS ---
    sendPromptBtn.addEventListener('click', sendPrompt);
    promptInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendPrompt();
        }
    });

    validateBtn.addEventListener('click', validateCode);
    downloadBtn.addEventListener('click', downloadCode);
    copyBtn.addEventListener('click', () => copyToClipboard(codeOutput.textContent));

    // Tab switching logic
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const targetPaneId = tab.getAttribute('data-tab');
            document.getElementById(`${targetPaneId}-tab`).classList.add('active');
        });
    });

    // --- 🤖 CORE AI FUNCTIONS ---
// In script.js, replace the entire sendPrompt function

async function sendPrompt() {
    const userInput = promptInput.value.trim();
    if (!userInput) return;

    addMessage('user', userInput);
    promptInput.value = '';
    showNotification('Contacting AI Orchestrator...', 'info');

    try {
        const response = await fetch(ORCHESTRATOR_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: userInput })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const result = await response.json();
        console.log("Received from FastAPI Orchestrator:", result);
        
        // --- NEW LOGIC TO HANDLE DIFFERENT RESPONSE TYPES ---
        if (result.response_type === "chat") {
            // It's a simple chat message, just add it to the chat window
            addMessage('assistant', result.message);
            showNotification('Received a message.', 'success');

        } else if (result.response_type === "plc_code") {
            // It's a full code generation response
            populateOutputs(result.final_json);
            showNotification(`Code received. Verification status: ${result.verification_status.status}`, 'success');
        
        } else {
            // Handle unexpected responses
            addMessage('assistant', "Sorry, I received an unexpected response from the server.");
            showNotification('Received an unknown response type.', 'error');
        }

    } catch (error) {
        console.error("Error sending to FastAPI Orchestrator:", error);
        const errorMessage = error.message.includes('Failed to fetch') 
            ? "⚠️ Error: Could not reach the AI Orchestrator server. Is main.py running?"
            : `⚠️ An error occurred: ${error.message}`;
        addMessage('assistant', errorMessage);
        showNotification('Error: Could not reach the main server.', 'error');
    }
}

    // --- ✅ VERIFICATION FUNCTION ---
    async function validateCode() {
        const codeToValidate = codeOutput.textContent;
        if (!codeToValidate || codeToValidate.startsWith("//")) {
            showNotification('Nothing to validate.', 'warning');
            return;
        }

        showNotification('Sending code for validation...', 'info');
        
        try {
            const response = await fetch(VERIFICATION_SERVICE_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ st_code: codeToValidate })
            });

            if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
            const validationResult = await response.json();

            if (validationResult.status === 'success') {
                showNotification('Validation Successful: Syntax OK!', 'success');
            } else {
                addMessage('assistant', `⚠️ Validation Failed:\n${validationResult.details}`);
                showNotification(`Validation Failed: Check chat for error details.`, 'error');
            }
        } catch (error) {
            console.error("Error connecting to validation service:", error);
            addMessage('assistant', '⚠️ Error: Could not reach the validation server. Make sure the service is running.');
            showNotification('Error: Could not reach the validation server.', 'error');
        }
    }

    // --- 🛠️ UTILITY FUNCTIONS ---
    function addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'user' ? 'user-message' : 'system-message';
        const messageP = document.createElement('p');
        messageP.textContent = content;
        messageDiv.appendChild(messageP);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Code copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            showNotification('Failed to copy code.', 'error');
        });
    }

    function downloadCode() {
        const codeToDownload = codeOutput.textContent;
        const blob = new Blob([codeToDownload], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'program.st';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => { notification.remove(); }, 4000);
    }
});