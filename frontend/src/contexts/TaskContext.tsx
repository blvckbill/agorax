import React, { createContext, useState, useEffect, type ReactNode } from 'react';
import type { TodoList, Task, CreateListInput, CreateTaskInput, UpdateTaskInput, TaskFilter } from '../types/task.types';
import { taskApi } from '../services/taskApi';
import { useAuth } from '../hooks/useAuth';

interface TaskContextType {
  lists: TodoList[];
  currentList: TodoList | null;
  tasks: Task[];
  selectedFilter: TaskFilter;
  isLoading: boolean;
  error: string | null;
  
  // List operations
  loadLists: () => Promise<void>;
  selectList: (listId: number) => Promise<void>;
  createList: (data: CreateListInput) => Promise<void>;
  updateList: (listId: number, title: string) => Promise<void>;
  deleteList: (listId: number) => Promise<void>;
  
  // Task operations
  loadTasks: (filter?: TaskFilter) => Promise<void>;
  createTask: (data: CreateTaskInput) => Promise<void>;
  updateTask: (taskId: number, data: UpdateTaskInput) => Promise<void>;
  deleteTask: (taskId: number) => Promise<void>;
  toggleTaskComplete: (taskId: number) => Promise<void>;
  toggleTaskStarred: (taskId: number) => Promise<void>;
  
  // Filters
  setFilter: (filter: TaskFilter) => void;
}

// eslint-disable-next-line react-refresh/only-export-components
export const TaskContext = createContext<TaskContextType | undefined>(undefined);

export const TaskProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [lists, setLists] = useState<TodoList[]>([]);
  const [currentList, setCurrentList] = useState<TodoList | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<TaskFilter>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load all lists on mount
  useEffect(() => {
    if (user) {
      loadLists();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loadLists = async () => {
    if (!user) return;
    
    try {
      setIsLoading(true);
      const response = await taskApi.getAllLists(user.id);
      setLists(response.items);
      
      // Auto-select first list if available
      if (response.items.length > 0 && !currentList) {
        await selectList(response.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lists');
    } finally {
      setIsLoading(false);
    }
  };

  const selectList = async (listId: number) => {
    try {
      setIsLoading(true);
      const list = await taskApi.getList(listId);
      setCurrentList(list);
      await loadTasks('all');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load list');
    } finally {
      setIsLoading(false);
    }
  };

  const createList = async (data: CreateListInput) => {
    try {
      setIsLoading(true);
      const newList = await taskApi.createList(data);
      setLists([...lists, newList]);
      await selectList(newList.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create list');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateList = async (listId: number, title: string) => {
    try {
      const updatedList = await taskApi.updateList(listId, title);
      setLists(lists.map(l => l.id === listId ? updatedList : l));
      if (currentList?.id === listId) {
        setCurrentList(updatedList);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update list');
      throw err;
    }
  };

  const deleteList = async (listId: number) => {
    try {
      await taskApi.deleteList(listId);
      setLists(lists.filter(l => l.id !== listId));
      
      // Select another list if current was deleted
      if (currentList?.id === listId) {
        const remainingLists = lists.filter(l => l.id !== listId);
        if (remainingLists.length > 0) {
          await selectList(remainingLists[0].id);
        } else {
          setCurrentList(null);
          setTasks([]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete list');
      throw err;
    }
  };

  const loadTasks = async (filter: TaskFilter = 'all') => {
    if (!currentList) return;
    
    try {
      setIsLoading(true);
      let response;
      
      switch (filter) {
        case 'completed':
          response = await taskApi.getCompletedTasks(currentList.id);
          break;
        case 'starred':
          response = await taskApi.getStarredTasks();
          break;
        default:
          response = await taskApi.getTasks(currentList.id);
      }
      
      setTasks(response.items);
      setSelectedFilter(filter);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  };

  const createTask = async (data: CreateTaskInput) => {
    if (!currentList) return;
    
    try {
      const newTask = await taskApi.createTask(currentList.id, data);
      setTasks([newTask, ...tasks]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
      throw err;
    }
  };

  const updateTask = async (taskId: number, data: UpdateTaskInput) => {
    if (!currentList) return;
    
    try {
      const updatedTask = await taskApi.updateTask(currentList.id, taskId, data);
      setTasks(tasks.map(t => t.id === taskId ? updatedTask : t));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
      throw err;
    }
  };

  const deleteTask = async (taskId: number) => {
    if (!currentList) return;
    
    try {
      await taskApi.deleteTask(currentList.id, taskId);
      setTasks(tasks.filter(t => t.id !== taskId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
      throw err;
    }
  };

  const toggleTaskComplete = async (taskId: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task || !currentList) return;
    
    await updateTask(taskId, {
      ...task,
      is_completed: !task.is_completed,
    });
  };

  const toggleTaskStarred = async (taskId: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task || !currentList) return;
    
    await updateTask(taskId, {
      ...task,
      is_starred: !task.is_starred,
    });
  };

  const setFilter = (filter: TaskFilter) => {
    loadTasks(filter);
  };

  return (
    <TaskContext.Provider
      value={{
        lists,
        currentList,
        tasks,
        selectedFilter,
        isLoading,
        error,
        loadLists,
        selectList,
        createList,
        updateList,
        deleteList,
        loadTasks,
        createTask,
        updateTask,
        deleteTask,
        toggleTaskComplete,
        toggleTaskStarred,
        setFilter,
      }}
    >
      {children}
    </TaskContext.Provider>
  );
};