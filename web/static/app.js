// API Base URL
const API_BASE = '';

// WebSocket connection
let ws = null;
let reconnectInterval = null;

// Connect to WebSocket
function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect
        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                connectWebSocket();
            }, 5000);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(message) {
    if (message.type === 'status_update') {
        updateProcessingStatus(message.data);
    } else if (message.type === 'processing_complete') {
        showStatus('uploadStatus', 
            `✓ Processing complete for ${message.document_id}!`, 
            'success'
        );
        loadDocuments();
    }
}

// Update processing status display
function updateProcessingStatus(statusData) {
    for (const [docId, status] of Object.entries(statusData)) {
        const statusElement = document.getElementById('uploadStatus');
        if (statusElement && statusElement.style.display !== 'none') {
            const stage = status.stage.charAt(0).toUpperCase() + status.stage.slice(1);
            const progress = Math.round((status.progress / status.total) * 100);
            showStatus('uploadStatus', 
                `${stage}... ${progress}% (${status.progress}/${status.total})`, 
                'info'
            );
        }
    }
}

// Utility Functions
function showLoading(show = true) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function showStatus(elementId, message, type = 'info') {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
}

function showResult(elementId, content, type = 'info') {
    const element = document.getElementById(elementId);
    element.innerHTML = content;
    element.className = `result-box ${type}`;
    element.style.display = 'block';
}

function clearResult(elementId) {
    const element = document.getElementById(elementId);
    element.style.display = 'none';
}

// Generate random document ID
function generateDocId() {
    return 'doc-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Upload PDF
async function uploadPDF() {
    const fileInput = document.getElementById('pdfFile');
    const docIdInput = document.getElementById('documentId');
    
    const file = fileInput.files[0];
    if (!file) {
        showStatus('uploadStatus', 'Please select a PDF file', 'error');
        return;
    }
    
    let docId = docIdInput.value.trim();
    if (!docId) {
        docId = generateDocId();
        docIdInput.value = docId;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_id', docId);
    
    try {
        showLoading(true);
        showStatus('uploadStatus', 'Uploading PDF...', 'info');
        
        // Upload
        const uploadResponse = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            throw new Error('Upload failed');
        }
        
        const uploadResult = await uploadResponse.json();
        showStatus('uploadStatus', `✓ Uploaded: ${uploadResult.num_pages} pages`, 'success');
        
        // Process
        showStatus('uploadStatus', 'Processing PDF...', 'info');
        const processResponse = await fetch(`${API_BASE}/api/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ document_id: docId })
        });
        
        if (!processResponse.ok) {
            throw new Error('Processing failed');
        }
        
        const processResult = await processResponse.json();
        showStatus('uploadStatus', 
            `✓ Processed successfully! ${processResult.num_pages} pages, ${processResult.num_chunks} chunks`, 
            'success'
        );
        
        // Reload document list
        await loadDocuments();
        
        // Clear inputs
        fileInput.value = '';
        docIdInput.value = '';
        
    } catch (error) {
        console.error('Error:', error);
        showStatus('uploadStatus', `Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Load Documents
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/api/documents`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load documents');
        }
        
        const listElement = document.getElementById('documentList');
        const querySelect = document.getElementById('queryDocId');
        const summarySelect = document.getElementById('summaryDocId');
        const extractSelect = document.getElementById('extractDocId');
        
        if (data.documents.length === 0) {
            listElement.innerHTML = '<p style="color: var(--text-secondary);">No documents uploaded yet.</p>';
            return;
        }
        
        // Update document list
        listElement.innerHTML = data.documents.map(doc => {
            const statusClass = doc.processed ? 'processed' : doc.status === 'error' ? 'error' : 'uploaded';
            const statusText = doc.processed ? 'Processed' : doc.status;
            
            return `
                <div class="document-item">
                    <h3>${doc.document_id}</h3>
                    <div class="document-info">
                        <span>📄 ${doc.num_pages} pages</span>
                        <span>💾 ${(doc.file_size / 1024 / 1024).toFixed(2)} MB</span>
                        ${doc.num_chunks ? `<span>📦 ${doc.num_chunks} chunks</span>` : ''}
                        <span class="document-status ${statusClass}">${statusText}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        // Update select dropdowns (only processed documents)
        const processedDocs = data.documents.filter(doc => doc.processed);
        const options = processedDocs.map(doc => 
            `<option value="${doc.document_id}">${doc.document_id} (${doc.num_pages} pages)</option>`
        ).join('');
        
        querySelect.innerHTML = '<option value="">Select a document...</option>' + options;
        summarySelect.innerHTML = '<option value="">Select a document...</option>' + options;
        extractSelect.innerHTML = '<option value="">Select a document...</option>' + options;
        
    } catch (error) {
        console.error('Error loading documents:', error);
        const listElement = document.getElementById('documentList');
        listElement.innerHTML = `<p style="color: var(--error-color);">Error: ${error.message}</p>`;
    }
}

// Query PDF
async function queryPDF() {
    const docId = document.getElementById('queryDocId').value;
    const query = document.getElementById('queryInput').value.trim();
    
    if (!docId) {
        showResult('queryResult', 'Please select a document', 'error');
        return;
    }
    
    if (!query) {
        showResult('queryResult', 'Please enter a question', 'error');
        return;
    }
    
    try {
        showLoading(true);
        clearResult('queryResult');
        
        const startTime = Date.now();
        
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                document_id: docId,
                query: query
            })
        });
        
        const data = await response.json();
        const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);
        
        if (!data.success) {
            throw new Error(data.error || 'Query failed');
        }
        
        let resultHTML = `<strong>Question:</strong> ${data.query}<br><br>`;
        resultHTML += `<strong>Answer:</strong> (Response time: ${responseTime}s)<br>${data.answer}`;
        
        if (data.sources && data.sources.length > 0) {
            resultHTML += '<div class="sources"><h4>📚 Sources:</h4>';
            data.sources.forEach((source, idx) => {
                resultHTML += `
                    <div class="source-item">
                        <strong>Page ${source.page_number}:</strong><br>
                        ${source.content_preview}
                    </div>
                `;
            });
            resultHTML += '</div>';
        }
        
        showResult('queryResult', resultHTML, 'success');
        
        // Add to chat history if in chat mode
        if (document.getElementById('chatHistory').classList.contains('active')) {
            addToChatHistory('user', query);
            addToChatHistory('assistant', data.answer);
        }
        
    } catch (error) {
        console.error('Error:', error);
        showResult('queryResult', `Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Chat mode functionality
function startChatMode() {
    const chatHistory = document.getElementById('chatHistory');
    chatHistory.classList.add('active');
    chatHistory.innerHTML = '<p><strong>💬 Chat Mode Active</strong></p><hr>';
}

function addToChatHistory(role, message) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const label = role === 'user' ? '👤 You' : '🤖 Assistant';
    messageDiv.innerHTML = `<strong>${label}:</strong>${message}`;
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Summarize PDF
async function summarizePDF() {
    const docId = document.getElementById('summaryDocId').value;
    const summaryType = document.getElementById('summaryType').value;
    
    if (!docId) {
        showResult('summaryResult', 'Please select a document', 'error');
        return;
    }
    
    try {
        showLoading(true);
        clearResult('summaryResult');
        
        const response = await fetch(`${API_BASE}/api/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                document_id: docId,
                summary_type: summaryType
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Summarization failed');
        }
        
        const typeLabel = summaryType.charAt(0).toUpperCase() + summaryType.slice(1);
        let resultHTML = `<strong>${typeLabel} Summary:</strong><br><br>`;
        resultHTML += data.summary.replace(/\n/g, '<br>');
        
        showResult('summaryResult', resultHTML, 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showResult('summaryResult', `Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Extract Information
async function extractInfo() {
    const docId = document.getElementById('extractDocId').value;
    const extractType = document.getElementById('extractType').value;
    
    if (!docId) {
        showResult('extractResult', 'Please select a document', 'error');
        return;
    }
    
    try {
        showLoading(true);
        clearResult('extractResult');
        
        const formData = new FormData();
        formData.append('document_id', docId);
        formData.append('extraction_type', extractType);
        
        const response = await fetch(`${API_BASE}/api/extract`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Extraction failed');
        }
        
        const typeLabel = extractType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        let resultHTML = `<strong>${typeLabel}:</strong><br><br>`;
        resultHTML += data.extracted_info.replace(/\n/g, '<br>');
        
        showResult('extractResult', resultHTML, 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showResult('extractResult', `Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Parallel query execution for multiple questions
async function batchQuery(documentId, questions) {
    const promises = questions.map(question => 
        fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                document_id: documentId,
                query: question
            })
        }).then(r => r.json())
    );
    
    return Promise.all(promises);
}

// Load documents on page load
window.addEventListener('DOMContentLoaded', () => {
    // Connect WebSocket
    connectWebSocket();
    
    // Load documents
    loadDocuments();
    
    // Add enter key support for query
    document.getElementById('queryInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            queryPDF();
        }
    });
    
    // Periodic status check for documents being processed
    setInterval(() => {
        const docs = pdf_processor?.metadata || {};
        for (const docId in docs) {
            if (docs[docId].status === 'processing') {
                checkProcessingStatus(docId);
            }
        }
    }, 2000);
});

// Check processing status
async function checkProcessingStatus(documentId) {
    try {
        const response = await fetch(`${API_BASE}/api/status/${documentId}`);
        const data = await response.json();
        
        if (data.success && data.status) {
            updateProcessingStatus({[documentId]: data.status});
        }
    } catch (error) {
        console.error('Error checking status:', error);
    }
}
