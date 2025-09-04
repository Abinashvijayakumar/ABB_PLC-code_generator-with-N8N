document.addEventListener('DOMContentLoaded', function () {
    // --- 💻 DOM ELEMENTS ---
    const sendPromptBtn = document.getElementById('sendPrompt');
    const promptInput = document.getElementById('promptInput');
    const chatMessages = document.getElementById('chatMessages');
    const codeCanvas = document.getElementById('codeCanvas');
    const variablesOutput = document.getElementById('variablesOutput');
    const simulationOutput = document.getElementById('simulationOutput');
    const verificationNotesOutput = document.getElementById('verificationNotesOutput');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingStatus = document.getElementById('loadingStatus');
    const validationIndicator = document.getElementById('validationIndicator');
    const validationIcon = document.getElementById('validationIcon');
    const validationText = document.getElementById('validationText');
    const clearChatBtn = document.getElementById('refreshChatBtn');
    const attachFileBtn = document.getElementById('attachFileBtn');
    const fileAttachmentInput = document.getElementById('fileAttachmentInput');
    const downloadBtn = document.getElementById('downloadBtn');
    const copyCodeBtn = document.getElementById('copyCodeBtn');
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const helpBtn = document.getElementById('helpBtn');
    const tabs = document.querySelectorAll('.tab-button');
    const panes = document.querySelectorAll('.tab-pane');
    const htmlEl = document.documentElement;

    // --- 🎯 API ENDPOINT ---
    const ORCHESTRATOR_URL = 'http://localhost:8000/generate';
    let chatHistory = [];

    // --- 🚀 EVENT LISTENERS ---
    sendPromptBtn.addEventListener('click', sendPrompt);
    promptInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendPrompt(); } });
    clearChatBtn.addEventListener('click', clearChat);
    attachFileBtn.addEventListener('click', () => fileAttachmentInput.click());
    fileAttachmentInput.addEventListener('change', handleFileUpload);
    downloadBtn.addEventListener('click', downloadCode);
    copyCodeBtn.addEventListener('click', () => copyToClipboard(codeCanvas.value));
    themeToggleBtn.addEventListener('click', toggleTheme);
    helpBtn.addEventListener('click', showHelp);
    tabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab)));

    // --- 💡 INITIALIZATION ---
    loadHistory();
    loadTheme();

    // --- 🎨 UI & UX FUNCTIONS ---
    function switchTab(tab) {
        tabs.forEach(t => t.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
    }

    function setLoading(isLoading, statusText) {
        loadingOverlay.classList.toggle('hidden', !isLoading);
        loadingStatus.textContent = statusText;
    }

    function updateValidationIndicator(isSuccess, message = '') {
        validationIndicator.className = 'validation-indicator';
        if (isSuccess === null) {
            validationIndicator.classList.add('pending');
            validationIcon.className = 'fas fa-circle';
            validationText.textContent = 'Awaiting Code';
        } else if (isSuccess) {
            validationIndicator.classList.add('success');
            validationIcon.className = 'fas fa-check-circle';
            validationText.textContent = 'Verified';
        } else {
            validationIndicator.classList.add('error');
            validationIcon.className = 'fas fa-times-circle';
            validationText.textContent = message || 'Error';
        }
    }

    function showHelp() {
        addMessage('system-info', "This is the PLC Co-pilot, an AI assistant for automation tasks. To use me:\n\n1.  **Describe Logic:** Type a description of the automation task you want to perform in the prompt box.\n\n2.  **Generate:** Press Send, and I will generate the Structured Text code, variable declarations, and a simulation trace.\n\n3.  **Review & Edit:** The generated code appears in an editable canvas on the right. You can modify it as needed.\n\n4.  **Download:** Use the download button to save your code as a `.st` file.");
    }

    // --- 💾 HISTORY & THEME ---
    function addMessage(type, content) {
        const sanitizedContent = DOMPurify.sanitize(content);
        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'user' ? 'user-message' : 'system-message';
        messageDiv.innerHTML = `<p>${sanitizedContent.replace(/\n/g, '<br>')}</p>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        if (type !== 'system-info') {
            chatHistory.push({ type, content });
            localStorage.setItem('plcChatHistory', JSON.stringify(chatHistory));
        }
    }
    
    function loadHistory() {
        const history = localStorage.getItem('plcChatHistory');
        if (history) {
            chatHistory = JSON.parse(history);
            chatMessages.innerHTML = '';
            chatHistory.forEach(msg => addMessage(msg.type, msg.content));
        }
    }

    function clearChat() {
        chatHistory = [];
        localStorage.removeItem('plcChatHistory');
        chatMessages.innerHTML = '<div class="system-message"><p>Chat history cleared. How can I help you?</p></div>';
        showNotification('Chat history cleared!', 'info');
    }
    
    function toggleTheme() {
        htmlEl.classList.toggle('dark-mode');
        htmlEl.classList.toggle('light-mode');
        const theme = htmlEl.classList.contains('dark-mode') ? 'dark' : 'light';
        localStorage.setItem('plcTheme', theme);
    }

    function loadTheme() {
        const theme = localStorage.getItem('plcTheme');
        if (theme === 'dark') {
            htmlEl.classList.add('dark-mode');
            htmlEl.classList.remove('light-mode');
        } else {
            htmlEl.classList.add('light-mode');
            htmlEl.classList.remove('dark-mode');
        }
    }
    
    // --- 🛠️ UTILITIES ---
    function handleFileUpload(e) {
        const file = e.target.files[0];
        if (file && file.type === "text/plain") {
            const reader = new FileReader();
            reader.onload = function(event) {
                const fileContent = event.target.result;
                promptInput.value += `\n\n--- CONTENT FROM ${file.name} ---\n${fileContent}`;
                showNotification(`Content from ${file.name} added to prompt.`, 'info');
            };
            reader.readAsText(file);
        } else if (file) {
            showNotification('Please select a valid .txt file.', 'error');
        }
        e.target.value = null;
    }

    function downloadCode() {
        const fileName = prompt("Enter the file name (e.g., 'motor_logic'):", "program");
        if (fileName === null || fileName.trim() === "") {
            showNotification('Download cancelled.', 'info');
            return;
        }
        const codeToDownload = codeCanvas.value;
        const blob = new Blob([codeToDownload], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${fileName.trim()}.st`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Code copied to clipboard!', 'success');
        }).catch(err => showNotification('Failed to copy code.', 'error'));
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // --- 🤖 CORE AI FUNCTIONS ---
    async function sendPrompt() {
        const userInput = promptInput.value.trim();
        if (!userInput) return;
        addMessage('user', userInput);
        promptInput.value = '';
        setLoading(true, "Contacting AI Orchestrator...");
        updateValidationIndicator(null);

        try {
            const response = await fetch(ORCHESTRATOR_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userInput })
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || `Server error: ${response.status}`);
            }
            const result = await response.json();
            
            setLoading(true, "AI is performing self-correction review...");
            setTimeout(() => {
                if (result.response_type === "chat") {
                    addMessage('assistant', result.message);
                    updateValidationIndicator(true);
                } else if (result.response_type === "plc_code") {
                    populateOutputs(result.final_json);
                    updateValidationIndicator(true);
                }
                setLoading(false);
            }, 1500);
        } catch (error) {
            console.error("Error:", error);
            addMessage('assistant', `⚠️ An error occurred: ${error.message}`);
            updateValidationIndicator(false, 'Failed');
            setLoading(false);
        }
    }

    function populateOutputs(data) {
        addMessage('assistant', data.explanation);
        codeCanvas.value = data.structured_text || "";
        variablesOutput.textContent = data.required_variables || "";
        simulationOutput.textContent = data.simulation_trace || "";
        verificationNotesOutput.textContent = data.verification_notes || "";
        if(variablesOutput.textContent) hljs.highlightElement(variablesOutput);
        if(simulationOutput.textContent) hljs.highlightElement(simulationOutput);
    }

    sendPromptBtn.addEventListener('click', sendPrompt);
    promptInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendPrompt(); } });
    clearChatBtn.addEventListener('click', clearChat);
    attachFileBtn.addEventListener('click', () => fileAttachmentInput.click());
    fileAttachmentInput.addEventListener('change', handleFileUpload);
    downloadBtn.addEventListener('click', downloadCode);
    copyCodeBtn.addEventListener('click', () => copyToClipboard(codeCanvas.value));
    themeToggleBtn.addEventListener('click', toggleTheme);
    helpBtn.addEventListener('click', showHelp);
    tabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab)));

    loadHistory();
    loadTheme();
});

