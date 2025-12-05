import { useEffect } from 'react';
import { wsManager } from '../services/websocket';
import type { WebSocketMessage } from '../types/task.types';
import { useAuth } from './useAuth';
import { useTasks } from './useTasks';

export const useWebSocket = (listId: number | null) => {
  const { token } = useAuth();
  const { loadTasks, currentList } = useTasks();

  useEffect(() => {
    if (!listId || !token) return;

    const handleMessage = (message: WebSocketMessage) => {
      console.log('WebSocket message received:', message);
      
      // Reload tasks when changes occur
      if (['task_added', 'task_updated', 'task_deleted'].includes(message.action)) {
        loadTasks();
      }
    };

    wsManager.connect(listId, token);
    wsManager.subscribe(listId.toString(), handleMessage);

    return () => {
      wsManager.unsubscribe(listId.toString(), handleMessage);
      wsManager.disconnect();
    };
  }, [listId, token, currentList, loadTasks]);
};