import { EventEmitter } from 'events';

export enum AGUIEventType {
  // Lifecycle events
  RUN_STARTED = 'RUN_STARTED',
  RUN_FINISHED = 'RUN_FINISHED',

  // Message events
  TEXT_MESSAGE_START = 'TEXT_MESSAGE_START',
  TEXT_MESSAGE_CONTENT = 'TEXT_MESSAGE_CONTENT',
  TEXT_MESSAGE_END = 'TEXT_MESSAGE_END',

  // Tool events
  TOOL_CALL_START = 'TOOL_CALL_START',
  TOOL_CALL_RESULT = 'TOOL_CALL_RESULT',
  TOOL_CALL_END = 'TOOL_CALL_END',

  // State events
  STATE_SNAPSHOT = 'STATE_SNAPSHOT',
  STATE_DELTA = 'STATE_DELTA',

  // Error events
  ERROR = 'ERROR',

  // Custom events for legal domain
  EVIDENCE_PROCESSED = 'EVIDENCE_PROCESSED',
  CASE_LAW_FOUND = 'CASE_LAW_FOUND',
  DOCUMENT_ANALYZED = 'DOCUMENT_ANALYZED'
}

export interface AGUIMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
}

export interface AGUIToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
}

export interface AGUIState {
  currentCase?: {
    id: string;
    name: string;
    files: string[];
    tags: string[];
  };
  activeAgents: string[];
  processingQueue: string[];
  sessionContext: Record<string, any>;
}

export class AGUIClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: any[] = [];
  private isConnected = false;
  private threadId: string;
  private baseUrl: string;

  constructor(baseUrl: string = 'ws://localhost:10200') {
    super();
    this.baseUrl = baseUrl;
    this.threadId = this.generateThreadId();
  }

  private generateThreadId(): string {
    return `thread_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async connect(threadId?: string): Promise<void> {
    if (threadId) {
      this.threadId = threadId;
    }

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.baseUrl}/ws/${this.threadId}`);

        this.ws.onopen = () => {
          console.log('AG-UI WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.flushMessageQueue();
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('AG-UI WebSocket error:', error);
          this.emit(AGUIEventType.ERROR, { error });
        };

        this.ws.onclose = () => {
          console.log('AG-UI WebSocket closed');
          this.isConnected = false;
          this.stopHeartbeat();
          this.attemptReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(data: string): void {
    try {
      const event = JSON.parse(data);
      console.log('AG-UI Event received:', event.type, event);

      // Emit the raw event
      this.emit(event.type, event.data);

      // Handle specific event types
      switch (event.type) {
        case AGUIEventType.TEXT_MESSAGE_CONTENT:
          this.emit('message', {
            type: 'assistant',
            content: event.data.content,
            partial: true
          });
          break;

        case AGUIEventType.TOOL_CALL_START:
          this.emit('toolStart', event.data);
          break;

        case AGUIEventType.STATE_SNAPSHOT:
          this.emit('stateUpdate', event.data);
          break;

        case AGUIEventType.ERROR:
          this.emit('error', event.data);
          break;
      }
    } catch (error) {
      console.error('Failed to parse AG-UI message:', error);
    }
  }

  async sendMessage(content: string, context?: any): Promise<void> {
    const message = {
      id: `msg_${Date.now()}`,
      type: 'user_message',
      content,
      context,
      timestamp: new Date().toISOString()
    };

    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.messageQueue.push(message);
    }
  }

  async executeAction(action: string, payload: any): Promise<void> {
    const request = {
      id: `req_${Date.now()}`,
      type: 'action',
      action,
      payload,
      timestamp: new Date().toISOString()
    };

    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(request));
    } else {
      this.messageQueue.push(request);
    }
  }

  // Specific methods for legal evidence features
  async uploadFile(file: File, metadata?: any): Promise<void> {
    const fileData = await this.fileToBase64(file);

    await this.executeAction('file_upload', {
      fileName: file.name,
      fileType: file.type,
      fileSize: file.size,
      fileData,
      metadata
    });
  }

  async analyzeDocument(fileId: string, analysisType: string): Promise<void> {
    await this.executeAction('analyze_document', {
      fileId,
      analysisType,
      options: {
        extractPolicies: true,
        generateSummary: true,
        identifyKeyPoints: true
      }
    });
  }

  async searchWCAT(query: string, filters?: any): Promise<void> {
    await this.executeAction('search_wcat', {
      query,
      filters,
      limit: 20
    });
  }

  async exportCase(caseId: string, format: 'zip' | 'pdf' | 'csv'): Promise<void> {
    await this.executeAction('export_case', {
      caseId,
      format,
      includeAnalysis: true
    });
  }

  // Helper methods
  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emit('connectionFailed', {
        message: 'Max reconnection attempts reached'
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      this.connect(this.threadId);
    }, delay);
  }

  disconnect(): void {
    this.isConnected = false;
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  getThreadId(): string {
    return this.threadId;
  }

  isActive(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}