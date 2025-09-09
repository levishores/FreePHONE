class CTIApp {
    constructor() {
        this.ws = null;
        this.calls = new Map();
        this.parkOrbits = new Map();
        this.conferences = new Map();
        this.currentCallUuid = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.initializeApp();
    }
    
    initializeApp() {
        this.initializeWebSocket();
        this.initializeDragAndDrop();
        this.setupEventListeners();
        this.initializeParkOrbits();
        this.initializeConferenceRooms();
        this.updateStatistics();
    }
    
    initializeWebSocket() {
        const wsUrl = 'ws://localhost:8000/ws'; // Backend WebSocket URL
        
        console.log('Connecting to WebSocket...');
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
            this.reconnectAttempts = 0;
            
            // Request initial data
            this.sendWebSocketMessage({
                type: 'get_active_calls'
            });
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.initializeWebSocket(), 5000);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.className = 'status-indicator connected';
            statusElement.querySelector('.status-text').textContent = 'Connected';
        } else {
            statusElement.className = 'status-indicator disconnected';
            statusElement.querySelector('.status-text').textContent = 'Disconnected';
        }
    }
    
    handleWebSocketMessage(message) {
        console.log('Received message:', message);
        
        switch (message.type) {
            case 'call_created':
                this.addCall(message.data);
                break;
            case 'call_answered':
                this.updateCall(message.data);
                break;
            case 'call_ended':
                this.removeCall(message.data.uuid);
                break;
            case 'call_parked':
                this.updateCall(message.data);
                this.updateParkOrbit(message.data.park_orbit, true, message.data.uuid);
                break;
            case 'conference_member_add':
                this.handleConferenceMemberAdd(message.data);
                break;
            case 'conference_member_del':
                this.handleConferenceMemberDel(message.data);
                break;
            case 'active_calls':
                this.loadActiveCalls(message.data);
                break;
            case 'transfer_result':
            case 'park_result':
            case 'hangup_result':
                this.handleActionResult(message.data);
                break;
            case 'error':
                this.handleError(message.data);
                break;
        }
        
        this.updateStatistics();
    }
    
    loadActiveCalls(calls) {
        this.calls.clear();
        calls.forEach(call => {
            this.calls.set(call.uuid, call);
        });
        this.renderCalls();
    }
    
    addCall(callData) {
        this.calls.set(callData.uuid, callData);
        this.renderCalls();
        this.showNotification(`New ${callData.direction} call: ${callData.caller_id_name || callData.caller_id_number}`);
    }
    
    updateCall(callData) {
        if (this.calls.has(callData.uuid)) {
            this.calls.set(callData.uuid, { ...this.calls.get(callData.uuid), ...callData });
            this.renderCalls();
        }
    }
    
    removeCall(callUuid) {
        this.calls.delete(callUuid);
        this.renderCalls();
        
        // Clear park orbit if call was parked
        this.parkOrbits.forEach((orbit, orbitNumber) => {
            if (orbit.callUuid === callUuid) {
                this.updateParkOrbit(orbitNumber, false);
            }
        });
    }
    
    renderCalls() {
        const container = document.getElementById('call-visualizer');
        
        if (this.calls.size === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📞</div>
                    <p>No active calls</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        this.calls.forEach((call) => {
            const callElement = this.createCallElement(call);
            container.appendChild(callElement);
        });
    }
    
    createCallElement(call) {
        const div = document.createElement('div');
        div.className = `call-item ${call.state.toLowerCase()}`;
        div.draggable = true;
        div.dataset.callUuid = call.uuid;
        
        const duration = call.answered_at ? this.formatDuration(new Date() - new Date(call.answered_at)) : '';
        const createdTime = new Date(call.created_at).toLocaleTimeString();
        
        div.innerHTML = `
            <div class="call-info">
                <div class="call-details">
                    <h4>${call.caller_id_name || call.caller_id_number}</h4>
                    <p>${call.direction} • ${call.destination_number}</p>
                    <p>State: ${call.state}${duration ? ` • ${duration}` : ''}</p>
                    <div class="call-meta">${createdTime}${call.extension_number ? ` • Ext: ${call.extension_number}` : ''}</div>
                </div>
                <div class="call-actions">
                    <button class="btn btn-transfer" onclick="app.showTransferModal('${call.uuid}')">Transfer</button>
                    <button class="btn btn-park" onclick="app.showParkModal('${call.uuid}')">Park</button>
                    <button class="btn btn-hangup" onclick="app.confirmHangup('${call.uuid}')">Hangup</button>
                </div>
            </div>
        `;
        
        return div;
    }
    
    formatDuration(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
        }
        return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
    
    initializeDragAndDrop() {
        document.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('call-item')) {
                e.target.classList.add('dragging');
                e.dataTransfer.setData('text/plain', e.target.dataset.callUuid);
                e.dataTransfer.effectAllowed = 'move';
            }
        });
        
        document.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('call-item')) {
                e.target.classList.remove('dragging');
            }
        });
        
        // Park orbit drop zones
        document.addEventListener('dragover', (e) => {
            if (e.target.closest('.park-orbit')) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                e.target.closest('.park-orbit').classList.add('drop-zone');
            }
        });
        
        document.addEventListener('dragleave', (e) => {
            if (e.target.closest('.park-orbit')) {
                e.target.closest('.park-orbit').classList.remove('drop-zone');
            }
        });
        
        document.addEventListener('drop', (e) => {
            const parkOrbit = e.target.closest('.park-orbit');
            if (parkOrbit) {
                e.preventDefault();
                parkOrbit.classList.remove('drop-zone');
                
                const callUuid = e.dataTransfer.getData('text/plain');
                const orbitNumber = parkOrbit.dataset.orbitNumber;
                
                if (!parkOrbit.classList.contains('occupied')) {
                    this.parkCallToOrbit(callUuid, orbitNumber);
                }
            }
        });
    }
    
    setupEventListeners() {
        // Refresh calls button
        document.getElementById('refresh-calls').addEventListener('click', () => {
            this.sendWebSocketMessage({ type: 'get_active_calls' });
        });
        
        // Modal event listeners
        this.setupModalEventListeners();
        
        // Context menu
        this.setupContextMenu();
    }
    
    setupModalEventListeners() {
        // Transfer modal
        document.getElementById('confirm-transfer').addEventListener('click', () => {
            const destination = document.getElementById('transfer-destination').value;
            if (destination && this.currentCallUuid) {
                this.transferCall(this.currentCallUuid, destination);
                this.hideModal('transfer-modal');
            }
        });
        
        document.getElementById('cancel-transfer').addEventListener('click', () => {
            this.hideModal('transfer-modal');
        });
        
        // Park modal
        document.getElementById('confirm-park').addEventListener('click', () => {
            const orbit = document.getElementById('park-orbit').value;
            if (orbit && this.currentCallUuid) {
                this.parkCallToOrbit(this.currentCallUuid, orbit);
                this.hideModal('park-modal');
            }
        });
        
        document.getElementById('cancel-park').addEventListener('click', () => {
            this.hideModal('park-modal');
        });
        
        // Close modal buttons
        document.querySelectorAll('.modal-close').forEach(button => {
            button.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal.id);
            });
        });
        
        // Close modal on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });
    }
    
    setupContextMenu() {
        document.addEventListener('contextmenu', (e) => {
            const callItem = e.target.closest('.call-item');
            if (callItem) {
                e.preventDefault();
                this.showContextMenu(e.clientX, e.clientY, callItem.dataset.callUuid);
            }
        });
        
        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
        
        document.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                const callUuid = document.getElementById('context-menu').dataset.callUuid;
                
                switch (action) {
                    case 'transfer':
                        this.showTransferModal(callUuid);
                        break;
                    case 'park':
                        this.showParkModal(callUuid);
                        break;
                    case 'hangup':
                        this.confirmHangup(callUuid);
                        break;
                }
                
                this.hideContextMenu();
            });
        });
    }
    
    showContextMenu(x, y, callUuid) {
        const contextMenu = document.getElementById('context-menu');
        contextMenu.dataset.callUuid = callUuid;
        contextMenu.style.left = `${x}px`;
        contextMenu.style.top = `${y}px`;
        contextMenu.classList.remove('hidden');
    }
    
    hideContextMenu() {
        document.getElementById('context-menu').classList.add('hidden');
    }
    
    showModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
        this.currentCallUuid = null;
        
        // Clear form fields
        if (modalId === 'transfer-modal') {
            document.getElementById('transfer-destination').value = '';
        } else if (modalId === 'park-modal') {
            document.getElementById('park-orbit').value = '';
        }
    }
    
    showTransferModal(callUuid) {
        this.currentCallUuid = callUuid;
        this.showModal('transfer-modal');
        document.getElementById('transfer-destination').focus();
    }
    
    showParkModal(callUuid) {
        this.currentCallUuid = callUuid;
        this.showModal('park-modal');
        document.getElementById('park-orbit').focus();
    }
    
    initializeParkOrbits() {
        const container = document.getElementById('park-visualizer');
        
        // Create park orbits 701-710
        for (let i = 701; i <= 710; i++) {
            const orbitElement = document.createElement('div');
            orbitElement.className = 'park-orbit';
            orbitElement.dataset.orbitNumber = i;
            orbitElement.innerHTML = `
                <div class="orbit-info">
                    <div class="orbit-number">${i}</div>
                    <div class="orbit-status">Available</div>
                </div>
            `;
            
            container.appendChild(orbitElement);
            this.parkOrbits.set(i.toString(), { number: i, occupied: false, callUuid: null });
        }
    }
    
    initializeConferenceRooms() {
        const container = document.getElementById('conference-visualizer');
        
        // Create some default conference rooms
        const rooms = ['3001', '3002', '3003'];
        
        rooms.forEach(roomNumber => {
            const roomElement = document.createElement('div');
            roomElement.className = 'conference-room';
            roomElement.innerHTML = `
                <div class="conference-header">
                    <div class="conference-name">Room ${roomNumber}</div>
                    <span class="participant-count">0</span>
                </div>
                <div class="participants"></div>
            `;
            
            container.appendChild(roomElement);
            this.conferences.set(roomNumber, { number: roomNumber, participants: [] });
        });
    }
    
    updateParkOrbit(orbitNumber, occupied, callUuid = null) {
        const orbit = this.parkOrbits.get(orbitNumber);
        if (orbit) {
            orbit.occupied = occupied;
            orbit.callUuid = callUuid;
            
            const element = document.querySelector(`[data-orbit-number="${orbitNumber}"]`);
            if (element) {
                element.className = occupied ? 'park-orbit occupied' : 'park-orbit';
                const status = element.querySelector('.orbit-status');
                status.textContent = occupied ? 'Occupied' : 'Available';
                
                // Add call info if occupied
                let callInfo = element.querySelector('.orbit-call-info');
                if (occupied && callUuid) {
                    const call = this.calls.get(callUuid);
                    if (call && !callInfo) {
                        callInfo = document.createElement('div');
                        callInfo.className = 'orbit-call-info';
                        element.querySelector('.orbit-info').appendChild(callInfo);
                    }
                    if (callInfo && call) {
                        callInfo.textContent = `${call.caller_id_name || call.caller_id_number}`;
                    }
                } else if (callInfo) {
                    callInfo.remove();
                }
            }
        }
    }
    
    handleConferenceMemberAdd(data) {
        const conference = this.conferences.get(data.conference_name);
        if (conference) {
            conference.participants.push({
                id: data.member_id,
                number: data.caller_id_number
            });
            this.renderConference(data.conference_name);
        }
    }
    
    handleConferenceMemberDel(data) {
        const conference = this.conferences.get(data.conference_name);
        if (conference) {
            conference.participants = conference.participants.filter(p => p.id !== data.member_id);
            this.renderConference(data.conference_name);
        }
    }
    
    renderConference(roomNumber) {
        const conference = this.conferences.get(roomNumber);
        const element = document.querySelector(`[data-room="${roomNumber}"]`);
        
        if (conference && element) {
            const participantCount = element.querySelector('.participant-count');
            const participantsContainer = element.querySelector('.participants');
            
            participantCount.textContent = conference.participants.length;
            
            if (conference.participants.length > 0) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
            
            participantsContainer.innerHTML = '';
            conference.participants.forEach(participant => {
                const participantElement = document.createElement('div');
                participantElement.className = 'participant';
                participantElement.innerHTML = `
                    <span class="participant-status"></span>
                    ${participant.number}
                `;
                participantsContainer.appendChild(participantElement);
            });
        }
    }
    
    updateStatistics() {
        const totalCalls = this.calls.size;
        const activeCalls = Array.from(this.calls.values()).filter(call => call.state === 'ACTIVE').length;
        const parkedCalls = Array.from(this.calls.values()).filter(call => call.state === 'PARKED').length;
        const conferenceParticipants = Array.from(this.conferences.values()).reduce((sum, conf) => sum + conf.participants.length, 0);
        
        document.getElementById('total-calls').textContent = totalCalls;
        document.getElementById('active-calls').textContent = activeCalls;
        document.getElementById('parked-calls').textContent = parkedCalls;
        document.getElementById('conference-participants').textContent = conferenceParticipants;
    }
    
    // Call control methods
    transferCall(callUuid, destination) {
        this.sendWebSocketMessage({
            type: 'transfer_call',
            data: { uuid: callUuid, destination }
        });
    }
    
    parkCallToOrbit(callUuid, orbitNumber) {
        this.sendWebSocketMessage({
            type: 'park_call',
            data: { uuid: callUuid, orbit: orbitNumber }
        });
    }
    
    async confirmHangup(callUuid) {
        const call = this.calls.get(callUuid);
        const callerInfo = call ? (call.caller_id_name || call.caller_id_number) : callUuid;
        
        if (window.electronAPI) {
            const result = await window.electronAPI.showMessageBox({
                type: 'question',
                buttons: ['Cancel', 'Hangup'],
                defaultId: 0,
                title: 'Confirm Hangup',
                message: `Are you sure you want to hangup the call with ${callerInfo}?`
            });
            
            if (result.response === 1) {
                this.hangupCall(callUuid);
            }
        } else {
            if (confirm(`Are you sure you want to hangup the call with ${callerInfo}?`)) {
                this.hangupCall(callUuid);
            }
        }
    }
    
    hangupCall(callUuid) {
        this.sendWebSocketMessage({
            type: 'hangup_call',
            data: { uuid: callUuid }
        });
    }
    
    handleActionResult(data) {
        if (data.success) {
            this.showNotification('Action completed successfully', 'success');
        } else {
            this.showNotification('Action failed: ' + (data.error || 'Unknown error'), 'error');
        }
    }
    
    handleError(data) {
        this.showNotification('Error: ' + data.message, 'error');
        console.error('WebSocket error:', data);
    }
    
    showNotification(message, type = 'info') {
        // Create a simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#3498db'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 3000;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    sendWebSocketMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, message not sent:', message);
            this.showNotification('Not connected to server', 'error');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CTIApp();
});

// Global functions for inline event handlers
window.app = null;
