document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Element References ---
    const sendPromptBtn = document.getElementById('sendPrompt');
    const promptInput = document.getElementById('promptInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearPromptBtn = document.querySelector('button[title="Clear Prompt"]'); // Assuming this is the clear button
    const downloadBtn = document.getElementById('downloadBtn');

    // Output Elements
    const explanationOutput = document.getElementById('explanation-output');
    const variablesOutput = document.getElementById('variables-output');
    const stCodeOutput = document.getElementById('st-code-output');
    const verificationOutput = document.getElementById('verification-output');
    const simulationOutput = document.getElementById('simulation-output');

    // --- Event Listeners ---
    sendPromptBtn.addEventListener('click', handleSendPrompt);
    promptInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendPrompt();
        }
    });
    if(clearPromptBtn) {
        clearPromptBtn.addEventListener('click', () => {
            promptInput.value = '';
        });
    }
    if(downloadBtn) {
        downloadBtn.addEventListener('click', downloadCode);
    }
    

    // --- Main Function ---
    async function handleSendPrompt() {
        const userPrompt = promptInput.value.trim();
        if (!userPrompt) return;

        addMessageToChat('user', userPrompt);
        promptInput.value = '';
        showLoadingState();

        // --- IMPORTANT: REPLACE WITH YOUR N8N PRODUCTION URL ---
        const n8nWebhookURL = "PASTE_YOUR_N8N_ACTIVE_PRODUCTION_URL_HERE"; 

        try {
            const response = await fetch(n8nWebhookURL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userPrompt }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Network response was not ok. Status: ${response.status}. Body: ${errorText}`);
            }

            const result = await response.json();
            
            removeTypingIndicator();
            addMessageToChat('assistant', result.explanation || "Here is the generated code.");
            displayResults(result);

        } catch (error) {
            console.error("Error calling backend:", error);
            const errorMessage = "An error occurred while connecting to the AI backend. Please check the console for details and ensure the n8n webhook URL is correct.";
            removeTypingIndicator();
            addMessageToChat('assistant', errorMessage);
            displayError(errorMessage);
        }
    }

    // --- UI Helper Functions ---
    function showLoadingState() {
        addMessageToChat('assistant', '...', true); // Show typing indicator
        explanationOutput.textContent = 'AI is processing your request...';
        variablesOutput.textContent = 'Please wait...';
        stCodeOutput.textContent = '';
        verificationOutput.textContent = '';
        simulationOutput.textContent = '';
    }

    function displayResults(result) {
        if (result.status === "success") {
            explanationOutput.textContent = result.explanation;
            variablesOutput.textContent = result.variables;
            stCodeOutput.textContent = result.st_code;
            verificationOutput.textContent = result.verification;
            simulationOutput.textContent = result.simulation;
        } else {
            displayError(result.explanation || "An unknown error occurred.");
            stCodeOutput.textContent = result.st_code || "No raw output available."; // Show raw error output for debugging
        }
    }

    function displayError(message) {
        explanationOutput.textContent = message;
        variablesOutput.textContent = '---';
        stCodeOutput.textContent = '---';
        verificationOutput.textContent = '---';
        simulationOutput.textContent = '---';
    }

    function addMessageToChat(type, content, isTyping = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        
        if (isTyping) {
            messageDiv.id = 'typingIndicator';
            messageDiv.innerHTML = '<p><span>.</span><span>.</span><span>.</span></p>';
        } else {
            const messageP = document.createElement('p');
            messageP.textContent = content;
            messageDiv.appendChild(messageP);
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function downloadCode() {
        // We only download if there is actual code to download
        if (stCodeOutput.textContent && stCodeOutput.textContent !== '---' && !stCodeOutput.textContent.startsWith("No ST code")) {
            const fullCode = `(*\n    Explanation: ${explanationOutput.textContent}\n*)\n\n${variablesOutput.textContent}\n\n${stCodeOutput.textContent}`;
            const blob = new Blob([fullCode], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'generated_plc_code.st';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            alert("No valid code available to download.");
        }
    }
});
