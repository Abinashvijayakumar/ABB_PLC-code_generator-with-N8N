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
    // Detect if we're running on GitHub Pages
    const isGitHubPages = window.location.hostname === 'abinashvijayakumar.github.io';
    const ORCHESTRATOR_URL = isGitHubPages ? null : 'http://localhost:8000/generate';
    let chatHistory = [];
    let isDemoMode = isGitHubPages;

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
    
    // Show demo mode notification and banner if on GitHub Pages
    if (isDemoMode) {
        // Show the demo banner
        const demoBanner = document.getElementById('demoBanner');
        if (demoBanner) {
            demoBanner.style.display = 'block';
        }
        
        // Show welcome message
        setTimeout(() => {
            addMessage('system-info', '🌐 Welcome to PLC Co-pilot Demo! You are viewing a demonstration version hosted on GitHub Pages. This interface shows sample responses to demonstrate the UI functionality. For full AI-powered code generation, please run the application locally with backend services or visit the live deployment.');
        }, 1000);
    }

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
        const helpText = isDemoMode 
            ? "This is the PLC Co-pilot demo interface. You are viewing a demonstration version with sample responses.\n\n**Demo Features:**\n1. **Try Examples:** Type 'start stop motor' or 'timer' to see sample PLC code generation\n2. **UI Preview:** Explore all interface features including code editing and download\n3. **Sample Outputs:** View generated Structured Text, variables, and simulation traces\n\n**For Full Functionality:** Run the complete application locally with backend services for real AI-powered code generation.\n\n**Repository:** Visit the GitHub repository for setup instructions and source code."
            : "This is the PLC Co-pilot, an AI assistant for automation tasks. To use me:\n\n1.  **Describe Logic:** Type a description of the automation task you want to perform in the prompt box.\n\n2.  **Generate:** Press Send, and I will generate the Structured Text code, variable declarations, and a simulation trace.\n\n3.  **Review & Edit:** The generated code appears in an editable canvas on the right. You can modify it as needed.\n\n4.  **Download:** Use the download button to save your code as a `.st` file.";
        
        addMessage('system-info', helpText);
    }

    // --- 💾 HISTORY & THEME ---
    function addMessage(type, content) {
        // Sanitize content with fallback if DOMPurify is not available
        const sanitizedContent = (typeof DOMPurify !== 'undefined') 
            ? DOMPurify.sanitize(content)
            : content.replace(/</g, '&lt;').replace(/>/g, '&gt;'); // Basic HTML escaping
            
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

    function loadTheme() {
        const theme = localStorage.getItem('plcTheme');
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        }
    }
    
    // --- 🛠️ UTILITIES ---
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
        setLoading(true, isDemoMode ? "Generating demo response..." : "Contacting AI Orchestrator...");
        updateValidationIndicator(null);

        try {
            if (isDemoMode) {
                // Demo mode - show sample responses
                const demoResponse = generateDemoResponse(userInput);
                setLoading(true, "AI is performing self-correction review...");
                setTimeout(() => {
                    populateOutputs(demoResponse);
                    updateValidationIndicator(true);
                    setLoading(false);
                }, 1500);
            } else {
                // Production mode - actual API call
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
            }
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

    function generateDemoResponse(userInput) {
        // Demo response generator for GitHub Pages
        const lowerInput = userInput.toLowerCase();
        
        if (lowerInput.includes('start') && lowerInput.includes('stop')) {
            return {
                explanation: "🔧 Demo Mode: Generated a basic start-stop motor control circuit. This is a sample response to demonstrate the UI functionality. For actual AI-powered code generation, please run the application locally with the backend services.",
                structured_text: `PROGRAM StartStopMotor
VAR
    StartButton : BOOL := FALSE;
    StopButton : BOOL := FALSE;
    MotorContactor : BOOL := FALSE;
    MotorRunning : BOOL := FALSE;
END_VAR

// Start-Stop Motor Logic
IF StartButton AND NOT StopButton THEN
    MotorContactor := TRUE;
END_IF;

IF StopButton THEN
    MotorContactor := FALSE;
END_IF;

MotorRunning := MotorContactor;

END_PROGRAM`,
                required_variables: `StartButton : BOOL := FALSE;
StopButton : BOOL := FALSE;
MotorContactor : BOOL := FALSE;
MotorRunning : BOOL := FALSE;`,
                simulation_trace: `Step 1: Initial state - All variables FALSE
Step 2: StartButton pressed (TRUE) - MotorContactor becomes TRUE
Step 3: MotorRunning becomes TRUE (motor starts)
Step 4: StopButton pressed (TRUE) - MotorContactor becomes FALSE
Step 5: MotorRunning becomes FALSE (motor stops)`,
                verification_notes: "Demo verification: Basic start-stop logic implemented with proper variable declarations and IEC 61131-3 syntax compliance."
            };
        } else if (lowerInput.includes('timer')) {
            return {
                explanation: "🔧 Demo Mode: Generated a basic timer example. This is a sample response to demonstrate the UI functionality.",
                structured_text: `PROGRAM TimerExample
VAR
    TimerInput : BOOL := FALSE;
    Timer1 : TON;
    TimerOutput : BOOL := FALSE;
    PT_Value : TIME := T#5S;
END_VAR

// Timer Logic
Timer1(IN := TimerInput, PT := PT_Value);
TimerOutput := Timer1.Q;

END_PROGRAM`,
                required_variables: `TimerInput : BOOL := FALSE;
Timer1 : TON;
TimerOutput : BOOL := FALSE;
PT_Value : TIME := T#5S;`,
                simulation_trace: `Step 1: TimerInput = FALSE, Timer not running
Step 2: TimerInput = TRUE, Timer starts counting
Step 3: After 5 seconds, TimerOutput = TRUE
Step 4: TimerInput = FALSE, Timer resets`,
                verification_notes: "Demo verification: Timer implementation follows IEC 61131-3 standards with proper TON function block usage."
            };
        } else {
            return {
                explanation: "🔧 Demo Mode: This is a sample response showing the PLC Co-pilot interface. For actual AI-powered code generation with advanced logic synthesis, please run the full application locally with backend services. Try keywords like 'start stop motor' or 'timer' for different demo examples.",
                structured_text: `PROGRAM DemoProgram
VAR
    Input1 : BOOL := FALSE;
    Output1 : BOOL := FALSE;
END_VAR

// Basic Example Logic
Output1 := Input1;

END_PROGRAM`,
                required_variables: `Input1 : BOOL := FALSE;
Output1 : BOOL := FALSE;`,
                simulation_trace: `Step 1: Input1 = FALSE, Output1 = FALSE
Step 2: Input1 = TRUE, Output1 = TRUE`,
                verification_notes: "Demo verification: Basic input-output mapping demonstrates fundamental PLC programming structure."
            };
        }
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

