// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react'; // Import useRef
import { wsManager } from '../services/websocket';
import type { WebSocketMessage } from '../types/task.types';
import { useAuth } from './useAuth';
import { useTasks } from './useTasks';

export const useWebSocket = (listId: number | null) => {
  const { token } = useAuth();
  const { loadTasks } = useTasks();

  const loadTasksRef = useRef(loadTasks);
  
  // Update the ref whenever loadTasks changes
  useEffect(() => {
    loadTasksRef.current = loadTasks;
  }, [loadTasks]);

  useEffect(() => {
    if (!listId || !token) return;

    const handleMessage = (message: WebSocketMessage) => {
      console.log(' WebSocket message received:', message);
      
      // Use the Ref to call the function
      if (['task_added', 'task_updated', 'task_deleted', 'user_added', 'user_removed'].includes(message.action)) {
        console.log(' Refreshing tasks due to real-time update...');
        loadTasksRef.current();
      }
    };

    console.log(`🔌 Connecting to WebSocket for List ${listId}...`);
    wsManager.connect(listId, token);
    wsManager.subscribe(listId.toString(), handleMessage);

    return () => {
      console.log(`🔌 Disconnecting WebSocket for List ${listId}`);
      wsManager.unsubscribe(listId.toString(), handleMessage);
      wsManager.disconnect();
    };
    //  REMOVED currentList from here!
  }, [listId, token]); 
};