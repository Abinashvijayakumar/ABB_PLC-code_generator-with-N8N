document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Element References ---
    const sendPromptBtn = document.getElementById('sendPrompt');
    const enhancePromptBtn = document.getElementById('enhancePromptBtn');
    const optimizeCodeBtn = document.getElementById('optimizeCodeBtn');
    const promptInput = document.getElementById('promptInput');
    const chatMessages = document.getElementById('chatMessages');
    const downloadBtn = document.getElementById('downloadBtn');

    // Output Blocks
    const placeholderText = document.getElementById('placeholder-text');
    const variablesBlock = document.getElementById('variables-block');
    const codeBlock = document.getElementById('code-block');
    const optimizationBlock = document.getElementById('optimization-block');
    const verificationBlock = document.getElementById('verification-block');
    const simulationBlock = document.getElementById('simulation-block');

    // Output Content Elements
    const variablesOutput = document.getElementById('variables-output');
    const stCodeOutput = document.getElementById('st-code-output');
    const optimizationOutput = document.getElementById('optimization-output');
    const verificationOutput = document.getElementById('verification-output');
    const simulationOutput = document.getElementById('simulation-output');
    
    // --- Gemini API Configuration ---
    // Leave apiKey as "" to use the environment's proxy.
    // Fill in only if you are running this outside a configured environment.
    const GEMINI_API_KEY = "";
    const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${GEMINI_API_KEY}`;


    // --- Event Listeners ---
    sendPromptBtn.addEventListener('click', handleSendPrompt);
    enhancePromptBtn.addEventListener('click', handleEnhancePrompt);
    optimizeCodeBtn.addEventListener('click', handleOptimizeCode);
    promptInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendPrompt();
        }
    });
    downloadBtn.addEventListener('click', downloadCode);

    // --- Core Gemini API Call Function ---
    async function callGeminiAPI(prompt) {
        const payload = {
            contents: [{ parts: [{ text: prompt }] }]
        };
        const response = await fetch(GEMINI_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            throw new Error(`API call failed. Status: ${response.status}`);
        }
        const result = await response.json();
        return result.candidates?.[0]?.content?.parts?.[0]?.text || "";
    }

    // --- ✨ New Gemini Feature: Enhance Prompt ---
    async function handleEnhancePrompt() {
        const userPrompt = promptInput.value.trim();
        if (!userPrompt) {
            alert("Please enter a prompt to enhance.");
            return;
        }

        const enhanceMasterPrompt = `You are a PLC programming expert. A user has provided a potentially vague instruction. Rewrite it to be clear, specific, and detailed for a code generation AI. Include specific variable names and conditions. Respond only with the improved prompt.

Original prompt: "${userPrompt}"`;
        
        addMessageToChat('system', '✨ Enhancing prompt...');
        promptInput.disabled = true;
        sendPromptBtn.disabled = true;
        
        try {
            const enhancedPrompt = await callGeminiAPI(enhanceMasterPrompt);
            promptInput.value = enhancedPrompt;
            addMessageToChat('system', 'Prompt enhanced successfully.');
        } catch (error) {
            console.error("Enhance prompt error:", error);
            addMessageToChat('system', 'Error enhancing prompt.');
        } finally {
            promptInput.disabled = false;
            sendPromptBtn.disabled = false;
        }
    }

    // --- ✨ New Gemini Feature: Optimize Code ---
    async function handleOptimizeCode() {
        const currentCode = stCodeOutput.textContent;
        if (!currentCode || currentCode === '---') {
            alert("No code available to optimize.");
            return;
        }

        const optimizeMasterPrompt = `You are a PLC code optimization expert. Review the following IEC 61131-3 Structured Text code. Rewrite it to be more efficient, safe, or readable, and provide a brief explanation of your changes. Respond in a JSON format with two keys: "explanation" and "optimized_code".

Original code:
\`\`\`iecst
${currentCode}
\`\`\``;
        
        optimizationBlock.classList.remove('hidden');
        optimizationOutput.textContent = 'Optimizing code...';
        
        try {
            const responseText = await callGeminiAPI(optimizeMasterPrompt);
            const cleanedResponse = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
            const result = JSON.parse(cleanedResponse);
            optimizationOutput.textContent = `(* ${result.explanation} *)\n\n${result.optimized_code}`;
        } catch(error) {
            console.error("Optimize code error:", error);
            optimizationOutput.textContent = "Error optimizing code.";
        }
    }


    // --- Main Function (Connects to n8n) ---
    async function handleSendPrompt() {
        const userPrompt = promptInput.value.trim();
        if (!userPrompt) return;

        addMessageToChat('user', userPrompt);
        promptInput.value = '';
        showLoadingState();

        const n8nWebhookURL = "PASTE_YOUR_N8N_ACTIVE_PRODUCTION_URL_HERE"; 

        try {
            const response = await fetch(n8nWebhookURL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userPrompt }),
            });

            if (!response.ok) throw new Error(`Network response error. Status: ${response.status}`);
            
            const result = await response.json();
            
            removeTypingIndicator();

            if (result.clarification_questions) {
                 addMessageToChat('assistant', result.clarification_questions);
                 hideAllOutputBlocks();
            } else {
                addMessageToChat('assistant', result.explanation || "Generation complete. See the results on the right.");
                displayResults(result);
            }

        } catch (error) {
            console.error("Error calling n8n backend:", error);
            const errorMessage = "An error occurred while connecting to the backend.";
            removeTypingIndicator();
            addMessageToChat('assistant', errorMessage);
            displayError(errorMessage);
        }
    }

    // --- UI Helper Functions ---
    function showLoadingState() {
        addMessageToChat('assistant', '...', true);
        placeholderText.classList.remove('hidden');
        placeholderText.innerHTML = '<i class="fas fa-spinner fa-spin"></i><p>Generating and verifying code...</p>';
        hideAllOutputBlocks();
    }

    function displayResults(result) {
        placeholderText.classList.add('hidden');
        
        variablesBlock.classList.remove('hidden');
        variablesOutput.textContent = result.variables;

        codeBlock.classList.remove('hidden');
        stCodeOutput.textContent = result.st_code;

        verificationBlock.classList.remove('hidden');
        const vStatus = result.verification.matiec_status;
        const vMessage = result.verification.matiec_message;
        verificationOutput.innerHTML = `
            <div class="verification-status ${vStatus}">
                <i class="fas ${vStatus === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                <span>${vMessage}</span>
            </div>
        `;
        
        simulationBlock.classList.remove('hidden');
        simulationOutput.textContent = result.simulation;
        
        // Show the optimize button now that there is code
        optimizeCodeBtn.classList.remove('hidden');
    }
    
    function displayError(message) {
        placeholderText.classList.remove('hidden');
        placeholderText.innerHTML = `<i class="fas fa-exclamation-circle"></i><p>${message}</p>`;
        hideAllOutputBlocks();
    }

    function hideAllOutputBlocks() {
        variablesBlock.classList.add('hidden');
        codeBlock.classList.add('hidden');
        verificationBlock.classList.add('hidden');
        simulationBlock.classList.add('hidden');
        optimizationBlock.classList.add('hidden');
        optimizeCodeBtn.classList.add('hidden');
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
        if (typingIndicator) typingIndicator.remove();
    }
    
    function downloadCode() {
        if (stCodeOutput.textContent && stCodeOutput.textContent !== '---') {
            const fullCode = `${variablesOutput.textContent}\n\n${stCodeOutput.textContent}`;
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

