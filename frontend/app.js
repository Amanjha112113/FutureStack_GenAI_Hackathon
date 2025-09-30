const { Room, RoomEvent, DataPacket_Kind } = livekit;

const connectButton = document.getElementById('connect-button');
const buttonIcon = document.getElementById('button-icon');
const nameInput = document.getElementById('name-input');
const statusIndicator = document.getElementById('status-indicator');
const chatWindow = document.getElementById('chat-window');

// ⚠️ IMPORTANT: Replace this with your LiveKit URL
const livekitUrl = 'wss://voice-wsaezqto.livekit.cloud';

// ⚠️ IMPORTANT: Replace this with your Render backend URL
const backendUrl = 'https://your-backend-name.onrender.com';

let room;
let isConnected = false;
let decoder = new TextDecoder();

async function getToken(identity, roomName) {
    const response = await fetch(`${backendUrl}/token?identity=${identity}&room_name=${roomName}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(`Failed to get token: ${error.detail}`);
    }
    const data = await response.json();
    return data.token;
}

connectButton.onclick = async () => {
    if (isConnected) {
        await room.disconnect();
    } else {
        const identity = nameInput.value;
        if (!identity) {
            alert('Please enter your name.');
            return;
        }

        updateStatus(true, 'Connecting...');

        try {
            const roomName = `agent-call-${Date.now()}`;
            const token = await getToken(identity, roomName);

            room = new Room();
            room.on(RoomEvent.Connected, onConnected);
            room.on(RoomEvent.Disconnected, onDisconnected);
            room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);
            room.on(RoomEvent.DataReceived, handleDataReceived);

            await room.connect(livekitUrl, token);

        } catch (e) {
            console.error(e);
            alert(`Failed to connect: ${e.message}`);
            onDisconnected();
        }
    }
};

// ... (The rest of the functions: onConnected, onDisconnected, etc. are the same as before)

function onConnected() {
    isConnected = true;
    updateStatus(true, 'Connected');
    buttonIcon.textContent = '🛑';
    connectButton.classList.add('disconnect');
    room.localParticipant.setMicrophoneEnabled(true);
}

function onDisconnected() {
    isConnected = false;
    updateStatus(false, 'Disconnected');
    buttonIcon.textContent = '📞';
    connectButton.classList.remove('disconnect');
}

function handleTrackSubscribed(track) {
    if (track.kind === 'audio') {
        track.attach();
    }
}

function handleDataReceived(payload) {
    const data = JSON.parse(decoder.decode(payload));
    addMessage(data.text, data.is_user ? 'user' : 'agent', data.name);
}

function updateStatus(connected, text = 'Disconnected') {
    statusIndicator.style.backgroundColor = connected ? '#34c759' : '#bbb';
    if(connected && text !== 'Disconnected') statusIndicator.textContent = text;
}

function addMessage(text, role, name) {
    if (!text.trim()) return;
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    messageDiv.innerHTML = `<strong>${name}</strong>: ${text}`;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}