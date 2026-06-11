let agents = [];
let currentAgentId = null;
let currentSessionId = null;
let currentInvocationId = null;
let isStreaming = false;

const agentsListEl = document.getElementById('agents-list');
const chatHeaderEl = document.getElementById('chat-header');
const messagesWindowEl = document.getElementById('messages-window');
const welcomeScreenEl = document.getElementById('welcome-screen');
const messagesListEl = document.getElementById('messages-list');
const chatFooterEl = document.getElementById('chat-footer');
const inputFormEl = document.getElementById('input-form');
const userInputEl = document.getElementById('user-input');
const streamIndicatorsEl = document.getElementById('stream-indicators');
const indicatorTextEl = document.getElementById('indicator-text');
const quickCardsEl = document.getElementById('quick-cards');

// Load Available Agents
async function loadAgents() {
    try {
        const res = await fetch('/api/agents');
        agents = await res.json();
        renderAgentsList();
    } catch (err) {
        console.error("Failed to load agents", err);
        agentsListEl.innerHTML = `<div class="error-msg"><i class="fa-solid fa-triangle-exclamation"></i> Error loading agents.</div>`;
    }
}

function renderAgentsList() {
    if (agents.length === 0) {
        agentsListEl.innerHTML = `<div class="no-agents">No agents found. Make sure app.py is in the app subfolders.</div>`;
        return;
    }

    agentsListEl.innerHTML = agents.map(agent => `
        <div class="agent-item" id="agent-${agent.id}" onclick="selectAgent('${agent.id}')">
            <span class="agent-item-name">${agent.name}</span>
            <span class="agent-item-desc">${agent.description}</span>
        </div>
    `).join('');
}

// Select Agent
async function selectAgent(agentId) {
    if (isStreaming) return;
    
    // Update active state in sidebar
    document.querySelectorAll('.agent-item').forEach(el => el.classList.remove('active'));
    document.getElementById(`agent-${agentId}`).classList.add('active');

    currentAgentId = agentId;
    currentSessionId = null;
    currentInvocationId = null;
    
    const agent = agents.find(a => a.id === agentId);
    
    // Update Header
    chatHeaderEl.innerHTML = `
        <div class="header-active">
            <div class="header-title-row">
                <span class="header-agent-name">${agent.name}</span>
                <span class="header-agent-badge">Local Agent</span>
            </div>
            <span class="header-agent-desc">${agent.description}</span>
        </div>
    `;

    // Reset Chat Window
    messagesListEl.innerHTML = '';
    messagesListEl.style.display = 'none';
    welcomeScreenEl.style.display = 'flex';
    chatFooterEl.style.display = 'block';
    
    // Load Quick Prompt Cards based on agent type
    renderQuickCards(agentId);
}

// Quick Starter prompts
function renderQuickCards(agentId) {
    let prompts = [];
    if (agentId.includes('staffing')) {
        prompts = [
            { title: "Find Consultants", prompt: "Who is available for a Java project in Paris?", icon: "fa-search" },
            { title: "Sourcing Pipeline", prompt: "I have a new urgent need for a Senior Magento Developer for an E-commerce client in Paris.", icon: "fa-briefcase" }
        ];
    } else if (agentId.includes('knowledge')) {
        prompts = [
            { title: "Build Graph", prompt: "Extract a knowledge graph from this context: Alice works at Google. Google is based in Mountain View.", icon: "fa-network-wired" },
            { title: "Generate Graph Image", prompt: "Can you visualize a knowledge graph with 3 entities: Julien (Software Engineer), Antigravity (AI Agent), Google (Developer)?", icon: "fa-image" }
        ];
    } else if (agentId.includes('pricing')) {
        prompts = [
            { title: "Calculate Margin", prompt: "Calculate project profitability for a Consultant with Gross Salary 45000, 3 years experience, client Google, location Paris.", icon: "fa-calculator" },
            { title: "Ask Benchmarks", prompt: "What are the market benchmarks for a Senior embedded developer in Paris?", icon: "fa-chart-line" }
        ];
    } else if (agentId.includes('image')) {
        prompts = [
            { title: "Generate Image", prompt: "Generate a beautiful glassmorphism style UI mockup for a coding workspace application.", icon: "fa-palette" },
            { title: "Upscale Request", prompt: "Upscale the latest generated image to 4K", icon: "fa-maximize" }
        ];
    } else {
        prompts = [
            { title: "Hello Agent", prompt: "Hello! What tools and capabilities do you have?", icon: "fa-hand-wave" },
            { title: "Run Analysis", prompt: "Perform a quick analysis of the current environment state.", icon: "fa-chart-simple" }
        ];
    }

    quickCardsEl.innerHTML = prompts.map(p => `
        <div class="quick-card" onclick="submitPrompt('${p.prompt.replace(/'/g, "\\'")}')">
            <span class="quick-card-icon"><i class="fa-solid ${p.icon}"></i></span>
            <span class="quick-card-title">${p.title}</span>
            <span class="quick-card-prompt">"${p.prompt}"</span>
        </div>
    `).join('');
}

function submitPrompt(promptText) {
    userInputEl.value = promptText;
    sendMessage();
}

// Session Creation helper
async function ensureSession() {
    if (!currentSessionId) {
        const res = await fetch(`/api/agents/${currentAgentId}/sessions`, { method: 'POST' });
        const data = await res.json();
        currentSessionId = data.sessionId;
    }
}

// Append message bubble to UI
function appendMessage(author, text, type = 'agent', options = {}) {
    welcomeScreenEl.style.display = 'none';
    messagesListEl.style.display = 'flex';

    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${type}`;
    if (options.id) wrapper.id = `msg-${options.id}`;

    // Meta details (Avatar + Name)
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    
    const icon = document.createElement('div');
    icon.className = 'message-author-icon';
    icon.innerHTML = type === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    
    const nameSpan = document.createElement('span');
    nameSpan.className = 'message-author-name';
    nameSpan.innerText = author;
    
    meta.appendChild(icon);
    meta.appendChild(nameSpan);
    wrapper.appendChild(meta);

    // Message Body
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Parse formatting (Markdown-like and Image URLs)
    content.innerHTML = formatMessageText(text);
    wrapper.appendChild(content);

    messagesListEl.appendChild(wrapper);
    scrollToBottom();
    return content;
}

function formatMessageText(text) {
    if (!text) return '';
    
    // Escape HTML tags to prevent XSS except formatting
    let formatted = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Simple markdown tables parsing
    if (formatted.includes('|')) {
        const lines = formatted.split('\n');
        let inTable = false;
        let tableHtml = '<table>';
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('|') && line.endsWith('|')) {
                if (!inTable) {
                    inTable = true;
                    const headers = line.split('|').slice(1, -1).map(h => `<th>${h.trim()}</th>`).join('');
                    tableHtml += `<thead><tr>${headers}</tr></thead><tbody>`;
                    // skip next line if it is separator (e.g. |---|---|)
                    if (i + 1 < lines.length && lines[i+1].includes('-')) i++;
                } else {
                    const cells = line.split('|').slice(1, -1).map(c => `<td>${c.trim()}</td>`).join('');
                    tableHtml += `<tr>${cells}</tr>`;
                }
            } else {
                if (inTable) {
                    inTable = false;
                    tableHtml += '</tbody></table>';
                    lines[i] = tableHtml + '\n' + lines[i];
                    tableHtml = '<table>';
                }
            }
        }
        if (inTable) {
            tableHtml += '</tbody></table>';
            formatted = lines.join('\n') + '\n' + tableHtml;
        } else {
            formatted = lines.join('\n');
        }
    }

    // Embed local WebP/PNG artifacts in-line
    // If the text references knowledge_graph.webp or similar local files, replace it with an image tag
    const imgRegex = /([a-zA-Z0-9_\-]+\.(webp|png|jpg|gif))/gi;
    formatted = formatted.replace(imgRegex, (match) => {
        // Exclude standard extensions if they are just part of the conversation text
        if (text.toLowerCase().includes('visualiz') || text.toLowerCase().includes('image') || text.toLowerCase().includes('graph')) {
            return `<br><img class="message-artifact-img" src="/api/artifacts/${match}" alt="${match}"><br>`;
        }
        return match;
    });

    // bold text (**text**)
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // code blocks (```code```)
    formatted = formatted.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
    
    // inline code (`code`)
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // carriage returns
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
}

function scrollToBottom() {
    messagesWindowEl.scrollTop = messagesWindowEl.scrollHeight;
}

// User submit message
async function sendMessage(e) {
    if (e) e.preventDefault();
    if (isStreaming) return;

    const text = userInputEl.value.trim();
    if (!text) return;

    userInputEl.value = '';
    
    appendMessage('You', text, 'user');
    isStreaming = true;
    
    // Show loading
    streamIndicatorsEl.style.display = 'flex';
    indicatorTextEl.innerText = 'Agent is thinking...';
    
    await ensureSession();
    
    // Create new agent message wrapper to stream content into
    const agentName = agents.find(a => a.id === currentAgentId).name;
    const contentBubble = appendMessage(agentName, '', 'agent');
    
    try {
        await streamResponse(text, contentBubble);
    } catch (err) {
        console.error("Stream error", err);
        contentBubble.innerHTML = `<span class="error"><i class="fa-solid fa-triangle-exclamation"></i> Communication error.</span>`;
    } finally {
        isStreaming = false;
        streamIndicatorsEl.style.display = 'none';
    }
}

// Handle streaming response using Fetch body reader
async function streamResponse(text, contentBubble, hitlData = null) {
    const bodyArgs = {
        sessionId: currentSessionId,
        invocationId: currentInvocationId
    };
    
    if (hitlData) {
        bodyArgs.confirmed = hitlData.confirmed;
        bodyArgs.funcCallId = hitlData.funcCallId;
        bodyArgs.payload = hitlData.payload;
    } else {
        bodyArgs.message = text;
    }
    
    const response = await fetch(`/api/chat/stream/${currentAgentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bodyArgs)
    });

    if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let accumulatedText = '';
    let thoughtsHtml = '';
    let activeThoughtsPanel = null;
    let thoughtsBody = null;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep remainder

        for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
                const dataJson = JSON.parse(line.slice(6));
                
                // Track invocation id to allow resumption
                if (dataJson.invocationId) {
                    currentInvocationId = dataJson.invocationId;
                }
                
                // If it is an error event
                if (dataJson.error) {
                    contentBubble.innerHTML = `<span class="error"><i class="fa-solid fa-circle-exclamation"></i> Error: ${dataJson.error}</span>`;
                    return;
                }

                // If this is a tool execution call, show a badge in thoughts
                if (dataJson.functionCalls && dataJson.functionCalls.length > 0) {
                    if (!activeThoughtsPanel) {
                        activeThoughtsPanel = createThoughtsPanel(contentBubble);
                        thoughtsBody = activeThoughtsPanel.querySelector('.thoughts-body');
                    }
                    dataJson.functionCalls.forEach(call => {
                        const callEl = document.createElement('div');
                        callEl.className = 'tool-call-badge';
                        callEl.innerHTML = `<i class="fa-solid fa-gear fa-spin"></i> Executing tool <strong>${call.name}</strong>`;
                        thoughtsBody.appendChild(callEl);
                        indicatorTextEl.innerText = `Calling ${call.name}...`;
                    });
                    scrollToBottom();
                }

                // If this is a tool response, update badge status in thoughts
                if (dataJson.functionResponses && dataJson.functionResponses.length > 0) {
                    if (thoughtsBody) {
                        dataJson.functionResponses.forEach(resp => {
                            // find active badge and mark success
                            const badges = thoughtsBody.querySelectorAll('.tool-call-badge');
                            badges.forEach(badge => {
                                if (badge.innerText.includes(resp.name)) {
                                    badge.innerHTML = `<i class="fa-solid fa-circle-check" style="color:var(--success)"></i> Executed tool <strong>${resp.name}</strong>`;
                                }
                            });
                        });
                    }
                }

                // Streaming text parts
                if (dataJson.text) {
                    accumulatedText += dataJson.text;
                    contentBubble.innerHTML = formatMessageText(accumulatedText);
                    
                    // Append thoughts panel to the bottom if it was initialized
                    if (activeThoughtsPanel) {
                        contentBubble.appendChild(activeThoughtsPanel);
                    }
                    scrollToBottom();
                }

                // Handling HITL confirmation requests (Interactive block)
                if (dataJson.confirmations) {
                    const funcCallId = Object.keys(dataJson.confirmations)[0];
                    const confirmation = dataJson.confirmations[funcCallId];
                    renderHitlIntervention(contentBubble, funcCallId, confirmation);
                    return; // Pause UI and wait for button action
                }
            }
        }
    }
}

// Collapsible Thoughts Panel Helper
function createThoughtsPanel(container) {
    const panel = document.createElement('div');
    panel.className = 'thoughts-panel';
    
    const header = document.createElement('div');
    header.className = 'thoughts-header';
    header.innerHTML = `
        <span><i class="fa-solid fa-microchip-ai" style="margin-right:8px;"></i> Thinking Process</span>
        <span class="thoughts-icon"><i class="fa-solid fa-chevron-right"></i></span>
    `;
    
    const body = document.createElement('div');
    body.className = 'thoughts-body';
    
    header.onclick = () => {
        panel.classList.toggle('open');
    };
    
    panel.appendChild(header);
    panel.appendChild(body);
    container.appendChild(panel);
    return panel;
}

// Render HITL approvals
function renderHitlIntervention(container, funcCallId, confirmation) {
    const panel = document.createElement('div');
    panel.className = 'hitl-panel';
    
    panel.innerHTML = `
        <div class="hitl-header">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <span>Human-In-The-Loop Confirmation Needed</span>
        </div>
        <div class="hitl-hint">
            <strong>Action Details:</strong> ${confirmation.hint || "The agent requires confirmation before proceeding."}
        </div>
        <div class="hitl-actions">
            <button class="hitl-btn approve" onclick="respondToHitl(true, '${funcCallId}', this)">Approve Action</button>
            <button class="hitl-btn abort" onclick="respondToHitl(false, '${funcCallId}', this)">Abort</button>
            <div class="hitl-correction-form">
                <input type="text" class="hitl-correction-input" id="correction-${funcCallId}" placeholder="Provide correction or feedback instead...">
                <button class="hitl-btn approve" style="background-color: var(--primary)" onclick="submitHitlCorrection('${funcCallId}', this)">Send Correction</button>
            </div>
        </div>
    `;
    
    container.appendChild(panel);
    scrollToBottom();
}

async function respondToHitl(confirmed, funcCallId, buttonEl) {
    const panel = buttonEl.closest('.hitl-panel');
    const bubble = panel.parentElement;
    
    // Disable inputs
    panel.innerHTML = `<div class="loading-spinner-container" style="padding:10px;"><div class="spinner"></div> Sending decision...</div>`;
    
    isStreaming = true;
    streamIndicatorsEl.style.display = 'flex';
    indicatorTextEl.innerText = confirmed ? 'Resuming task...' : 'Aborting task...';
    
    try {
        await streamResponse('', bubble, {
            confirmed: confirmed,
            funcCallId: funcCallId,
            payload: ""
        });
    } catch (err) {
        console.error(err);
        bubble.innerHTML += `<div class="error"><i class="fa-solid fa-circle-exclamation"></i> Response failed.</div>`;
    } finally {
        isStreaming = false;
        streamIndicatorsEl.style.display = 'none';
    }
}

async function submitHitlCorrection(funcCallId, buttonEl) {
    const inputEl = document.getElementById(`correction-${funcCallId}`);
    const correctionText = inputEl.value.trim();
    if (!correctionText) return;
    
    const panel = buttonEl.closest('.hitl-panel');
    const bubble = panel.parentElement;
    
    panel.innerHTML = `<div class="loading-spinner-container" style="padding:10px;"><div class="spinner"></div> Sending correction...</div>`;
    
    isStreaming = true;
    streamIndicatorsEl.style.display = 'flex';
    indicatorTextEl.innerText = 'Submitting correction...';
    
    try {
        await streamResponse('', bubble, {
            confirmed: false,
            funcCallId: funcCallId,
            payload: correctionText
        });
    } catch (err) {
        console.error(err);
        bubble.innerHTML += `<div class="error"><i class="fa-solid fa-circle-exclamation"></i> Response failed.</div>`;
    } finally {
        isStreaming = false;
        streamIndicatorsEl.style.display = 'none';
    }
}

// Bind Events
inputFormEl.onsubmit = sendMessage;

// Initialize
loadAgents();
