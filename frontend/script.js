document.addEventListener('DOMContentLoaded', function() {
    // --- 💻 DOM ELEMENTS ---
    const chatMessages = document.getElementById('chatMessages');
    const promptInput = document.getElementById('promptInput');
    const sendPromptBtn = document.getElementById('sendPrompt');
    const formatSelector = document.getElementById('formatSelector');
    
    // New Output Elements
    const codeOutput = document.getElementById('codeOutput');
    const variablesOutput = document.getElementById('variablesOutput');
    const simulationOutput = document.getElementById('simulationOutput');
    const verificationNotesOutput = document.getElementById('verificationNotesOutput');

    // Button Elements
    const downloadBtn = document.getElementById('downloadBtn');
    const validateBtn = document.getElementById('validateBtn'); // Ensure your button has this ID
    const copyBtn = document.querySelector('[title="Copy Code"]'); // A way to select the copy button
    
    // Tab Elements
    const tabs = document.querySelectorAll('.tab-button');
    const panes = document.querySelectorAll('.tab-pane');

    // n8n Webhook URL
    const N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/plc-generator?sessionId=my-conversation-1'; // Your n8n URL

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
            // Deactivate all tabs and panes
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            // Activate the clicked tab and corresponding pane
            tab.classList.add('active');
            const targetPaneId = tab.getAttribute('data-tab');
            document.getElementById(`${targetPaneId}-tab`).classList.add('active');
        });
    });


    // --- 🤖 CORE AI FUNCTIONS ---

    async function sendPrompt() {
        const userInput = promptInput.value.trim();
        if (!userInput) return;

        addMessage('user', userInput);
        promptInput.value = '';
        showNotification('Sending prompt to AI...', 'info');

        try {
            const response = await fetch(N8N_WEBHOOK_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userInput })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const result = await response.json();
            console.log("Received from n8n:", result);
            
            // Populate the UI with the full, structured response
            populateOutputs(result);

        } catch (error) {
            console.error("Error sending to n8n:", error);
            addMessage('assistant', "⚠️ Error: Could not reach the AI server.");
        }
    }

    function populateOutputs(data) {
        // Add explanation to chat
        if (data.explanation) {
            addMessage('assistant', data.explanation);
        } else {
            addMessage('assistant', "Generated PLC logic received. See output panels for details.");
        }

        // Populate the output panes
        variablesOutput.textContent = data.required_variables || "// No variables declared.";
        codeOutput.textContent = data.structured_text || "// No code generated.";
        simulationOutput.textContent = data.simulation_trace || "No simulation trace provided.";
        verificationNotesOutput.textContent = data.verification_notes || "No verification notes provided.";

        // Re-run the syntax highlighter after updating content
        // You MUST include highlight.js in your HTML for this to work
        if (typeof hljs !== 'undefined') {
            hljs.highlightAll();
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
        const VERIFICATION_SERVICE_URL = 'http://localhost:8002/verify'; // Member 3's service URL

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
    
    // A simple, non-library notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`; // You'll need to style .notification .info .success .error
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }
});