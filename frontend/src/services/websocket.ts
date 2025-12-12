import type { WebSocketMessage } from '../types/task.types';

class WebSocketManager {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<(data: WebSocketMessage) => void>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;

  connect(listId: number, token: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `ws://host.docker.internal:8000/ws/${listId}?token=${token}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log(`WebSocket connected to list ${listId}`);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.notifyListeners(listId.toString(), message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(listId, token);
    };
  }

  private attemptReconnect(listId: number, token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => {
        this.connect(listId, token);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  subscribe(listId: string, callback: (data: WebSocketMessage) => void) {
    if (!this.listeners.has(listId)) {
      this.listeners.set(listId, new Set());
    }
    this.listeners.get(listId)!.add(callback);
  }

  unsubscribe(listId: string, callback: (data: WebSocketMessage) => void) {
    const callbacks = this.listeners.get(listId);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.listeners.delete(listId);
      }
    }
  }

  private notifyListeners(listId: string, message: WebSocketMessage) {
    const callbacks = this.listeners.get(listId);
    if (callbacks) {
      callbacks.forEach((callback) => callback(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsManager = new WebSocketManager();