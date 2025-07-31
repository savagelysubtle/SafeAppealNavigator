import { useState, useEffect, useCallback, useRef } from 'react';
import { AGUIClient, AGUIEventType, AGUIMessage, AGUIState, AGUIToolCall } from '../services/AGUIClient';

interface UseAGUIOptions {
  autoConnect?: boolean;
  threadId?: string;
  onError?: (error: any) => void;
}

interface AGUIHookState {
  messages: AGUIMessage[];
  toolCalls: AGUIToolCall[];
  state: AGUIState | null;
  isConnected: boolean;
  isProcessing: boolean;
  currentAgentActivity: string | null;
}

export function useAGUI(options: UseAGUIOptions = {}) {
  const [hookState, setHookState] = useState<AGUIHookState>({
    messages: [],
    toolCalls: [],
    state: null,
    isConnected: false,
    isProcessing: false,
    currentAgentActivity: null
  });

  const clientRef = useRef<AGUIClient | null>(null);
  const partialMessageRef = useRef<string>('');

  useEffect(() => {
    const client = new AGUIClient();
    clientRef.current = client;

    // Set up event listeners
    client.on(AGUIEventType.RUN_STARTED, () => {
      setHookState(prev => ({ ...prev, isProcessing: true }));
    });

    client.on(AGUIEventType.RUN_FINISHED, () => {
      setHookState(prev => ({ ...prev, isProcessing: false, currentAgentActivity: null }));
    });

    client.on(AGUIEventType.TEXT_MESSAGE_START, () => {
      partialMessageRef.current = '';
    });

    client.on(AGUIEventType.TEXT_MESSAGE_CONTENT, (data) => {
      partialMessageRef.current += data.content;

      // Update the last message or create a new one
      setHookState(prev => {
        const messages = [...prev.messages];
        const lastMessage = messages[messages.length - 1];

        if (lastMessage?.type === 'assistant' && lastMessage.metadata?.partial) {
          lastMessage.content = partialMessageRef.current;
        } else {
          messages.push({
            id: `msg_${Date.now()}`,
            type: 'assistant',
            content: partialMessageRef.current,
            metadata: { partial: true }
          });
        }

        return { ...prev, messages };
      });
    });

    client.on(AGUIEventType.TEXT_MESSAGE_END, () => {
      // Mark the message as complete
      setHookState(prev => {
        const messages = [...prev.messages];
        const lastMessage = messages[messages.length - 1];
        if (lastMessage?.metadata?.partial) {
          delete lastMessage.metadata.partial;
        }
        return { ...prev, messages };
      });
    });

    client.on(AGUIEventType.TOOL_CALL_START, (data) => {
      const toolCall: AGUIToolCall = {
        id: data.id,
        name: data.name,
        arguments: data.arguments,
        status: 'running'
      };

      setHookState(prev => ({
        ...prev,
        toolCalls: [...prev.toolCalls, toolCall],
        currentAgentActivity: `Running ${data.name}`
      }));
    });

    client.on(AGUIEventType.TOOL_CALL_END, (data) => {
      setHookState(prev => ({
        ...prev,
        toolCalls: prev.toolCalls.map(tc =>
          tc.id === data.id
            ? { ...tc, status: 'completed', result: data.result }
            : tc
        )
      }));
    });

    client.on(AGUIEventType.STATE_SNAPSHOT, (data) => {
      setHookState(prev => ({ ...prev, state: data }));
    });

    client.on(AGUIEventType.ERROR, (error) => {
      console.error('AG-UI Error:', error);
      if (options.onError) {
        options.onError(error);
      }
    });

    // Auto-connect if requested
    if (options.autoConnect) {
      client.connect(options.threadId).then(() => {
        setHookState(prev => ({ ...prev, isConnected: true }));
      });
    }

    return () => {
      client.disconnect();
    };
  }, []);

  const connect = useCallback(async (threadId?: string) => {
    if (clientRef.current) {
      await clientRef.current.connect(threadId || options.threadId);
      setHookState(prev => ({ ...prev, isConnected: true }));
    }
  }, [options.threadId]);

  const sendMessage = useCallback(async (content: string, context?: any) => {
    if (clientRef.current) {
      // Add user message to state
      const userMessage: AGUIMessage = {
        id: `msg_${Date.now()}`,
        type: 'user',
        content,
        metadata: context
      };

      setHookState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage]
      }));

      await clientRef.current.sendMessage(content, context);
    }
  }, []);

  const uploadFile = useCallback(async (file: File, metadata?: any) => {
    if (clientRef.current) {
      await clientRef.current.uploadFile(file, metadata);
    }
  }, []);

  const analyzeDocument = useCallback(async (fileId: string, analysisType: string) => {
    if (clientRef.current) {
      await clientRef.current.analyzeDocument(fileId, analysisType);
    }
  }, []);

  const searchWCAT = useCallback(async (query: string, filters?: any) => {
    if (clientRef.current) {
      await clientRef.current.searchWCAT(query, filters);
    }
  }, []);

  const exportCase = useCallback(async (caseId: string, format: 'zip' | 'pdf' | 'csv') => {
    if (clientRef.current) {
      await clientRef.current.exportCase(caseId, format);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setHookState(prev => ({ ...prev, messages: [] }));
  }, []);

  return {
    // State
    messages: hookState.messages,
    toolCalls: hookState.toolCalls,
    state: hookState.state,
    isConnected: hookState.isConnected,
    isProcessing: hookState.isProcessing,
    currentAgentActivity: hookState.currentAgentActivity,

    // Actions
    connect,
    sendMessage,
    uploadFile,
    analyzeDocument,
    searchWCAT,
    exportCase,
    clearMessages
  };
}