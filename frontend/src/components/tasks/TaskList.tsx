import React, { useState } from 'react';
import { Plus, Loader2, ListTodo } from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { useWebSocket } from '../../hooks/useWebSocket';
import TaskItem from './TaskItem';
import CreateTaskModal from './CreateTaskModal';
import TaskFilters from './TaskFilters';
import type { Task } from '../../types/task.types';
import CollaboratorsBadge from './CollaboratorsBadge';
import ActivityFeed from './ActivityFeed';

const TaskList: React.FC = () => {
  const { currentList, tasks, isLoading } = useTasks();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  // Enable real-time updates for current list
  useWebSocket(currentList?.id || null);

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
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-3">
            <div>
            <h1 className="text-2xl font-bold text-gray-900">{currentList.title}</h1>
            <p className="text-sm text-gray-500 mt-1">
                {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'}
            </p>
            </div>
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

        {/* Filters */}
        <div className="px-6 py-4 bg-white border-b border-gray-200">
          <TaskFilters />
        </div>

        {/* Tasks */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12">
              <ListTodo className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500">No tasks yet</p>
              <p className="text-sm text-gray-400 mt-1">Click "Add Task" to create your first task</p>
            </div>
          ) : (
            <div className="space-y-3 max-w-4xl">
              {tasks.map((task) => (
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