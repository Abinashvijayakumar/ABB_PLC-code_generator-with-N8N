document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chatMessages');
    const promptInput = document.getElementById('promptInput');
    const sendPromptBtn = document.getElementById('sendPrompt');
    const codeOutput = document.getElementById('codeOutput');
    const formatSelector = document.getElementById('formatSelector');
    
    // Default program templates
    const defaultPrograms = {
        st: {
            temperature: `PROGRAM TemperatureControl
VAR
    Temperature : REAL;
    Setpoint : REAL := 25.0;
    HeatingOutput : BOOL;
    CoolingOutput : BOOL;
    Hysteresis : REAL := 1.0;
END_VAR

(* Temperature control logic *)
IF Temperature < (Setpoint - Hysteresis) THEN
    HeatingOutput := TRUE;
    CoolingOutput := FALSE;
ELSIF Temperature > (Setpoint + Hysteresis) THEN
    HeatingOutput := FALSE;
    CoolingOutput := TRUE;
ELSE
    HeatingOutput := FALSE;
    CoolingOutput := FALSE;
END_IF;
END_PROGRAM`,
            motor: `PROGRAM MotorControl
VAR
    StartButton : BOOL;
    StopButton : BOOL;
    MotorRunning : BOOL;
    EmergencyStop : BOOL;
    MotorSpeed : REAL := 0.0;
    MaxSpeed : REAL := 100.0;
END_VAR

(* Motor control logic *)
IF EmergencyStop THEN
    MotorRunning := FALSE;
    MotorSpeed := 0.0;
ELSIF StartButton AND NOT StopButton THEN
    MotorRunning := TRUE;
    IF MotorSpeed < MaxSpeed THEN
        MotorSpeed := MotorSpeed + 5.0;
    END_IF;
ELSIF StopButton OR NOT StartButton THEN
    MotorRunning := FALSE;
    MotorSpeed := 0.0;
END_IF;
END_PROGRAM`,
            counter: `PROGRAM CounterExample
VAR
    CounterInput : BOOL;
    ResetButton : BOOL;
    CountValue : INT := 0;
    MaxCount : INT := 100;
    CounterPulse : R_TRIG;
END_VAR

(* Counter logic with rising edge detection *)
CounterPulse(CLK := CounterInput);

IF ResetButton THEN
    CountValue := 0;
ELSIF CounterPulse.Q AND CountValue < MaxCount THEN
    CountValue := CountValue + 1;
END_IF;
END_PROGRAM`
        },
        ladder: {
            temperature: `[LADDER DIAGRAM: Temperature Control]
|                                                                  |
|--[Temperature < (Setpoint - Hysteresis)]--+--( HeatingOutput )---|
|                                          |
|--[Temperature > (Setpoint + Hysteresis)]--+--( CoolingOutput )---|
|                                                                  |`,
            motor: `[LADDER DIAGRAM: Motor Control]
|                                                                  |
|--[StartButton]--+--[/StopButton]--+--[/EmergencyStop]--( MotorRunning )--|
|                                                                  |
|--[EmergencyStop]--+--(/MotorRunning)--|
|                                                                  |
|--[MotorRunning]--+--[MotorSpeed < MaxSpeed]--+--( MotorSpeed + 5.0 )--|
|                                                                  |`,
            counter: `[LADDER DIAGRAM: Counter Example]
|                                                                  |
|--[CounterInput]--+--[ONS]--+--[CountValue < MaxCount]--( CountValue + 1 )--|
|                                                                  |
|--[ResetButton]--+--( CountValue := 0 )--|
|                                                                  |`
        }
    };
    
    // Current default program
    let currentDefaultProgram = 'temperature';
    
    // Sample structured text code for demonstration
    const sampleStructuredText = defaultPrograms.st.temperature;

    // Sample ladder logic for demonstration
    const sampleLadderLogic = defaultPrograms.ladder.temperature;

    // Function to update the output title based on selected format
    function updateOutputTitle(format) {
        const outputTitle = document.getElementById('outputTitle');
        switch(format) {
            case 'ladder':
                outputTitle.textContent = 'Generated Ladder Logic Program';
                break;
            default:
                outputTitle.textContent = 'Generated Structured Text';
        }
    }

    // Event Listeners
    sendPromptBtn.addEventListener('click', sendPrompt);
    promptInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendPrompt();
        }
    });
    
    // Default program selection
    const programButtons = document.querySelectorAll('.program-btn');
    programButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            programButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update current default program
            currentDefaultProgram = this.getAttribute('data-program');
            
            // Update code output based on selected format and program
            updateCodeOutput(formatSelector.value);
            
            // Show notification
            showNotification(`Default program changed to ${this.textContent}`, 'info');
        });
    });

    // Format selector change event
    formatSelector.addEventListener('change', function() {
        updateCodeOutput(formatSelector.value);
        updateOutputTitle(formatSelector.value);
    });

    // Copy button functionality
    document.querySelector('.output-section .section-controls button:nth-child(2)').addEventListener('click', function() {
        copyToClipboard(codeOutput.textContent);
        showNotification('Code copied to clipboard!', 'success');
    });

    // Download button functionality
    document.querySelector('.output-section .section-controls button:nth-child(3)').addEventListener('click', function() {
        downloadCode();
    });

    // Validate button functionality
    document.querySelector('.output-section .section-controls button:nth-child(4)').addEventListener('click', function() {
        validateCode();
    });

    // Debug button functionality
    document.querySelector('.output-controls button:nth-child(1)').addEventListener('click', function() {
        debugCode();
    });

    // Simulate button functionality
    document.querySelector('.output-controls button:nth-child(3)').addEventListener('click', function() {
        simulateCode();
    });

    // File upload functionality
    document.querySelector('.section-controls button:nth-child(2)').addEventListener('click', function() {
        // Trigger file input click
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.txt,.st,.xml';
        fileInput.click();
        
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    promptInput.value = e.target.result;
                };
                reader.readAsText(file);
                showNotification(`File "${file.name}" loaded successfully!`, 'success');
            }
        });
    });

    // Clear prompt functionality
    document.querySelector('.section-controls button:nth-child(1)').addEventListener('click', function() {
        promptInput.value = '';
        showNotification('Prompt cleared!', 'info');
    });

    // Functions
    function sendPrompt() {
        const prompt = promptInput.value.trim();
        if (prompt === '') return;

        // Add user message to chat
        addMessage('user', prompt);
        
        // Clear input
        promptInput.value = '';
        
        // Simulate AI processing
        showTypingIndicator();
        
        // Analyze prompt for keywords to determine which default program to use
        const promptLower = prompt.toLowerCase();
        let programType = currentDefaultProgram;
        let responseMessage = '';
        
        // Simple keyword matching to select appropriate program
        if (promptLower.includes('temperature') || promptLower.includes('heat') || promptLower.includes('cooling')) {
            programType = 'temperature';
            responseMessage = 'I\'ve generated a temperature control program based on your requirements. This program handles heating and cooling based on temperature setpoints and hysteresis.';
        } else if (promptLower.includes('motor') || promptLower.includes('start') || promptLower.includes('stop') || promptLower.includes('speed')) {
            programType = 'motor';
            responseMessage = 'I\'ve created a motor control program that includes start/stop functionality, emergency stop, and speed control features.';
        } else if (promptLower.includes('count') || promptLower.includes('counter') || promptLower.includes('increment')) {
            programType = 'counter';
            responseMessage = 'I\'ve generated a counter program with rising edge detection that counts pulses and includes a reset function.';
        } else {
            // Default response if no specific keywords are found
            responseMessage = `I've generated a ${currentDefaultProgram} control program based on your requirements. You can view, copy, or download it from the panel on the right.`;
        }
        
        // Update current program if it was changed based on the prompt
        if (programType !== currentDefaultProgram) {
            currentDefaultProgram = programType;
            
            // Update active button
            document.querySelectorAll('.program-btn').forEach(btn => {
                if (btn.getAttribute('data-program') === programType) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }
        
        // Simulate response after a delay (in a real app, this would be an API call)
        setTimeout(() => {
            removeTypingIndicator();
            
            // Add AI response
            addMessage('assistant', responseMessage);
            
            // Add a follow-up message with usage instructions
            setTimeout(() => {
                addMessage('assistant', 'You can switch between Structured Text and Ladder Logic formats using the selector above the code. Feel free to ask if you need any modifications to the program.');
            }, 1000);
            
            // Update code output
            updateCodeOutput(formatSelector.value);
        }, 1500);
    }

    function addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        
        const messageP = document.createElement('p');
        messageP.textContent = content;
        
        messageDiv.appendChild(messageP);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'assistant-message typing-indicator';
        typingDiv.innerHTML = '<p><span>.</span><span>.</span><span>.</span></p>';
        typingDiv.id = 'typingIndicator';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    function updateCodeOutput(format) {
        let code;
        
        switch(format) {
            case 'ladder':
                code = defaultPrograms.ladder[currentDefaultProgram];
                break;
            default:
                code = defaultPrograms.st[currentDefaultProgram];
        }
        
        // Update code display with syntax highlighting
        codeOutput.textContent = code;
        
        // Update program info section
        updateProgramInfo(format, currentDefaultProgram);
        
        // In a real implementation, you would use a library like Prism.js or highlight.js for syntax highlighting
    }
    
    function updateProgramInfo(format, programType) {
        const programTypeElement = document.getElementById('programType');
        const programFormatElement = document.getElementById('programFormat');
        
        // Update program type display
        let programTypeName = '';
        switch(programType) {
            case 'temperature':
                programTypeName = 'Temperature Control';
                break;
            case 'motor':
                programTypeName = 'Motor Control';
                break;
            case 'counter':
                programTypeName = 'Counter';
                break;
            default:
                programTypeName = 'Temperature Control';
        }
        
        // Update format display
        let formatName = format === 'ladder' ? 'Ladder Logic' : 'Structured Text';
        
        programTypeElement.textContent = `Program Type: ${programTypeName}`;
        programFormatElement.textContent = `Format: ${formatName}`;
    }

    function copyToClipboard(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }

    function downloadCode() {
        const format = formatSelector.value;
        let fileFormats;
        
        // Define available file formats based on the selected code type
        if (format === 'ladder') {
            fileFormats = [
                { extension: 'lad', name: 'Ladder Logic (.lad)' },
                { extension: 'xml', name: 'XML Format (.xml)' },
                { extension: 'l5x', name: 'L5X Format (.l5x)' },
                { extension: 'txt', name: 'Text Format (.txt)' }
            ];
        } else { // Structured Text
            fileFormats = [
                { extension: 'st', name: 'Structured Text (.st)' },
                { extension: 'xml', name: 'XML Format (.xml)' },
                { extension: 'txt', name: 'Text Format (.txt)' },
                { extension: 'scl', name: 'SCL Format (.scl)' }
            ];
        }
        
        // Create and show the file format selection dialog
        showFileFormatDialog(fileFormats, function(selectedFormat) {
            if (!selectedFormat) return; // User canceled
            
            const blob = new Blob([codeOutput.textContent], {type: 'text/plain'});
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `plc_program.${selectedFormat.extension}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification(`Code downloaded as plc_program.${selectedFormat.extension}`, 'success');
        });
    }
    
    function showFileFormatDialog(formats, callback) {
        // Create dialog overlay
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';
        
        // Create dialog container
        const dialog = document.createElement('div');
        dialog.className = 'dialog';
        
        // Create dialog header
        const header = document.createElement('div');
        header.className = 'dialog-header';
        header.innerHTML = '<h3>Select File Format</h3>';
        
        // Create dialog content
        const content = document.createElement('div');
        content.className = 'dialog-content';
        
        // Create format options
        formats.forEach(format => {
            const option = document.createElement('div');
            option.className = 'format-option';
            option.textContent = format.name;
            option.addEventListener('click', function() {
                document.body.removeChild(overlay);
                callback(format);
            });
            content.appendChild(option);
        });
        
        // Create dialog footer with cancel button
        const footer = document.createElement('div');
        footer.className = 'dialog-footer';
        
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-secondary';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.addEventListener('click', function() {
            document.body.removeChild(overlay);
            callback(null);
        });
        
        footer.appendChild(cancelBtn);
        
        // Assemble dialog
        dialog.appendChild(header);
        dialog.appendChild(content);
        dialog.appendChild(footer);
        overlay.appendChild(dialog);
        
        // Add to body
        document.body.appendChild(overlay);
    }
    }

    function validateCode() {
        // Simulate code validation
        showNotification('Code validation successful! No errors found.', 'success');
        
        // In a real implementation, this would send the code to a backend service for validation
    }

    function debugCode() {
        // Simulate debugging process
        showNotification('Debug mode activated. Analyzing code...', 'info');
        
        // In a real implementation, this would integrate with a PLC debugging tool
    }

    function simulateCode() {
        // Simulate code execution
        showNotification('Simulation started. Running PLC code...', 'info');
        
        // In a real implementation, this would integrate with a PLC simulation environment
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to body
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Add notification styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 1000;
        }
        
        .notification.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .notification.success {
            background-color: var(--success-color);
        }
        
        .notification.error {
            background-color: var(--error-color);
        }
        
        .notification.info {
            background-color: var(--primary-color);
        }
        
        .notification.warning {
            background-color: var(--warning-color);
        }
        
        .typing-indicator p {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background: #fff;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: bounce 1.5s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) {
            animation-delay: 0s;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes bounce {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-5px);
            }
        }
    `;
    document.head.appendChild(style);

    // Add event listener for upload PLC button
    document.getElementById('uploadPLCBtn').addEventListener('click', function() {
        // Create a file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.st,.lad,.xml,.l5x,.scl,.txt';
        
        // Trigger click on the file input
        fileInput.click();
        
        // Handle file selection
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Update code output with file content
                    codeOutput.textContent = e.target.result;
                    
                    // Determine format based on file extension
                    const extension = file.name.split('.').pop().toLowerCase();
                    let format = 'st'; // Default to structured text
                    
                    if (['lad', 'l5x'].includes(extension)) {
                        format = 'ladder';
                        formatSelector.value = 'ladder';
                    } else {
                        formatSelector.value = 'st';
                    }
                    
                    // Update output title and program info
                    updateOutputTitle(format);
                    updateProgramInfo(format, 'custom');
                    document.getElementById('programType').textContent = `Program Type: Uploaded (${file.name})`;
                    
                    showNotification(`Uploaded ${file.name} successfully`, 'success');
                };
                
                reader.readAsText(file);
            }
        });
    });
    
    // Add event listener for debug button
    document.getElementById('debugBtn').addEventListener('click', debugCode);
    
    // Initialize with structured text format
    updateCodeOutput('st');
    updateOutputTitle('st');
});