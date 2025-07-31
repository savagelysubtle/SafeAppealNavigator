import React, { useState, useEffect, useRef } from 'react';
import { useAppContext } from '../../contexts/AppContext';
import { useAGUI } from '../../hooks/useAGUI';
import LoadingSpinner from '../ui/LoadingSpinner';

const UserIcon: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
    <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
  </svg>
);

const AiIcon: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
    <path fillRule="evenodd" d="M8.22 5.222a.75.75 0 011.06 0l1.25 1.25a.75.75 0 010 1.061l-1.25 1.25a.75.75 0 11-1.06-1.06l.69-.69-.69-.69a.75.75 0 010-1.06zM11.78 14.778a.75.75 0 01-1.06 0l-1.25-1.25a.75.75 0 010-1.061l1.25-1.25a.75.75 0 111.06 1.06l-.69.69.69.69a.75.75 0 010 1.06z" clipRule="evenodd" />
  </svg>
);

const ChatAgentPanelPage: React.FC = () => {
  const {
    files,
    wcatCases,
    selectedFileIdsForContext,
    selectedWcatCaseIdsForContext,
    setIsLoading: setAppIsLoading,
    setError,
    addAuditLogEntry
  } = useAppContext();

  const {
    sendMessage,
    messages,
    isProcessing,
    isConnected,
    connect,
    currentAgentActivity,
    toolCalls,
    clearMessages
  } = useAGUI({
    autoConnect: true,
    onError: (error) => {
      console.error('AG-UI Error:', error);
      setError('Connection error: ' + error.message);
    }
  });

  const [userInput, setUserInput] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Connect on mount if not already connected
  useEffect(() => {
    if (!isConnected) {
      connect();
    }
  }, [isConnected, connect]);

  // Sync loading state with app context
  useEffect(() => {
    setAppIsLoading(isProcessing);
  }, [isProcessing, setAppIsLoading]);

  const handleSendMessage = async () => {
    if (!userInput.trim() || !isConnected || isProcessing) return;

    const messageText = userInput.trim();
    setUserInput('');

    // Prepare context for the backend
    const context = {
      selectedFiles: selectedFileIdsForContext,
      selectedWcatCases: selectedWcatCaseIdsForContext,
      includeWCAT: selectedWcatCaseIdsForContext.length > 0,
      includePolicies: true,
      threadId: 'legal-chat-' + Date.now()
    };

    try {
      await sendMessage(messageText, context);

      // Add audit log entry
      addAuditLogEntry(
        'Chat Message Sent',
        `Message: "${messageText.substring(0, 100)}${messageText.length > 100 ? '...' : ''}"`,
        'info'
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message: ' + (error as Error).message);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    clearMessages();
    addAuditLogEntry(
      'Chat Cleared',
      'Chat history cleared by user',
      'info'
    );
  };

  const selectedFiles = files.filter(f => selectedFileIdsForContext.includes(f.id));
  const selectedWcatCases = wcatCases.filter(c => selectedWcatCaseIdsForContext.includes(c.id));

  return (
    <div className="flex h-full bg-background text-textPrimary">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">{/* Simplified without sidebar for now */}

        {/* Header */}
        <div className="border-b border-border bg-cardBackground p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold">AI Legal Assistant</h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-textSecondary">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {currentAgentActivity && (
                <span className="text-sm text-blue-500 flex items-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">{currentAgentActivity}</span>
                </span>
              )}
              <button
                onClick={handleClearChat}
                className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                disabled={isProcessing}
              >
                Clear Chat
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-textSecondary py-8">
              <AiIcon />
              <p className="mt-2">Start a conversation with your AI legal assistant</p>
              <p className="text-sm mt-1">
                Select files or WCAT cases in the sidebar to provide context
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start space-x-3 ${
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.type === 'assistant' && (
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white">
                    <AiIcon />
                  </div>
                )}

                <div
                  className={`max-w-3xl p-3 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white ml-12'
                      : 'bg-cardBackground border border-border'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    {message.content}
                    {message.metadata?.partial && (
                      <span className="inline-block w-2 h-4 bg-current opacity-75 animate-pulse ml-1" />
                    )}
                  </div>
                </div>

                {message.type === 'user' && (
                  <div className="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center text-white">
                    <UserIcon />
                  </div>
                )}
              </div>
            ))
          )}

          {/* Tool Call Indicators */}
          {toolCalls.filter(tc => tc.status === 'running').map(toolCall => (
            <div key={toolCall.id} className="flex items-center space-x-2 text-sm text-blue-500">
              <LoadingSpinner size="sm" />
              <span>Running: {toolCall.name}</span>
            </div>
          ))}

          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-border bg-cardBackground p-4">
          <div className="flex space-x-3">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                isConnected
                  ? "Ask about your legal case, documents, or WCAT precedents..."
                  : "Connecting to AI assistant..."
              }
              className="flex-1 resize-none border border-border rounded-lg p-3 bg-background text-textPrimary placeholder-textSecondary focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              disabled={!isConnected || isProcessing}
            />
            <button
              onClick={handleSendMessage}
              disabled={!userInput.trim() || !isConnected || isProcessing}
              className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primaryHover disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? <LoadingSpinner size="sm" /> : 'Send'}
            </button>
          </div>

          {/* Context Summary */}
          {(selectedFiles.length > 0 || selectedWcatCases.length > 0) && (
            <div className="mt-3 text-sm text-textSecondary">
              Context: {selectedFiles.length} files, {selectedWcatCases.length} WCAT cases
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatAgentPanelPage;
