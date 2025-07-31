import React, { useState } from 'react';
import { useAGUI } from '../hooks/useAGUI';

export default function Chat() {
  const { sendMessage, messages, isProcessing, isConnected, connect } = useAGUI({
    autoConnect: true
  });
  const [input, setInput] = useState('');

  // Connect on mount
  React.useEffect(() => {
    if (!isConnected) {
      connect();
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.type}`}>
            <strong>{msg.type}:</strong> {msg.content}
          </div>
        ))}
        {isProcessing && <div className="typing-indicator">AI is thinking...</div>}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
          disabled={!isConnected || isProcessing}
        />
        <button onClick={handleSend} disabled={!isConnected || isProcessing}>
          Send
        </button>
      </div>
    </div>
  );
}