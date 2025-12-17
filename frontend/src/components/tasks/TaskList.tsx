import React, { useState, useMemo } from 'react';
import { Plus, Loader2, ListTodo, Trash2 } from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { useWebSocket } from '../../hooks/useWebSocket';
import TaskItem from './TaskItem';
import CreateTaskModal from './CreateTaskModal';
import CollaboratorsBadge from './CollaboratorsBadge';
import ActivityFeed from './ActivityFeed';
import type { Task } from '../../types/task.types';

const TaskList: React.FC = () => {
  const { 
    currentList, 
    tasks, 
    isLoading, 
    deleteList,
    selectedFilter,
    setFilter
  } = useTasks();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  // Enable real-time updates for current list
  useWebSocket(currentList?.id || null);

  // 🧠 SORTING & FILTERING LOGIC
  const displayedTasks = useMemo(() => {
    const filtered = [...tasks];

    // 1. "All" Tab: 
    //    - Hides completed tasks (they go to the Completed tab)
    //    - Sorts by NEWEST FIRST (Descending ID: 3, 2, 1...)
    if (selectedFilter === 'all') {
      return filtered
        .filter(t => !t.is_completed)
        .sort((a, b) => b.id - a.id); 
    }

    // 2. "Completed" Tab: 
    //    - Shows only completed tasks
    //    - Sorts by RECENTLY UPDATED (Most recently finished at top)
    if (selectedFilter === 'completed') {
      return filtered
        .filter(t => t.is_completed)
        .sort((a, b) => {
          const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
          const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
          return dateB - dateA; 
        });
    }

    // 3. "Starred" Tab: 
    //    - Shows only starred tasks
    //    - Sorts by RECENTLY UPDATED (Most recently starred/modified at top)
    if (selectedFilter === 'starred') {
      return filtered
        .filter(t => t.is_starred)
        .sort((a, b) => {
          const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
          const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
          return dateB - dateA;
        });
    }

    return filtered;
  }, [tasks, selectedFilter]);

  // 🗑️ HANDLE LIST DELETION
  const handleDeleteList = async () => {
    if (!currentList) return;
    
    const isConfirmed = window.confirm(
      `Are you sure you want to delete "${currentList.title}"?\n\nThis will PERMANENTLY delete all ${tasks.length} tasks in this list.`
    );

    if (isConfirmed) {
      try {
        await deleteList(currentList.id);
        // Context handles redirect after deletion
      } catch (error) {
        console.error("Failed to delete list", error);
        alert("Failed to delete list. Please try again.");
      }
    }
  };

  if (!currentList) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <ListTodo className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 text-lg">Select a list to view tasks</p>
          <p className="text-gray-400 text-sm mt-1">or create a new list to get started</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex-1 flex flex-col bg-gray-50 h-full overflow-hidden">
        
        {/* --- HEADER --- */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            {/* Title & Delete Button */}
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">{currentList.title}</h1>
                <button 
                  onClick={handleDeleteList}
                  className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded hover:bg-red-50"
                  title="Delete this list"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'}
              </p>
            </div>
            
            {/* Top Right Actions */}
            <div className="flex items-center gap-3">
              <CollaboratorsBadge />
              <ActivityFeed />
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                <Plus className="w-4 h-4" />
                Add Task
              </button>
            </div>
          </div>
        </div>

        {/* --- TABS --- */}
        <div className="px-6 pt-4 bg-white border-b border-gray-200 flex-shrink-0 flex gap-6">
            <button
              onClick={() => setFilter('all')}
              className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
                selectedFilter === 'all' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              All Tasks
            </button>
            <button
              onClick={() => setFilter('completed')}
              className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
                selectedFilter === 'completed' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Completed
            </button>
            <button
              onClick={() => setFilter('starred')}
              className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
                selectedFilter === 'starred' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Starred
            </button>
        </div>

        {/* --- TASK LIST CONTENT --- */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : displayedTasks.length === 0 ? (
            <div className="text-center py-12">
              <ListTodo className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500">
                {selectedFilter === 'all' ? "No active tasks" : `No ${selectedFilter} tasks found`}
              </p>
              {selectedFilter === 'all' && (
                <p className="text-sm text-gray-400 mt-1">Click "Add Task" to create one</p>
              )}
            </div>
          ) : (
            <div className="space-y-3 max-w-4xl">
              {displayedTasks.map((task) => (
                <TaskItem
                  key={task.id}
                  task={task}
                  onEdit={(task) => {
                    setEditingTask(task);
                    setShowCreateModal(true);
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* --- CREATE/EDIT MODAL --- */}
      {showCreateModal && (
        <CreateTaskModal
          onClose={() => {
            setShowCreateModal(false);
            setEditingTask(null);
          }}
          editTask={editingTask}
          listTitle={currentList.title} 
        />
      )}
    </>
  );
};

export default TaskList;