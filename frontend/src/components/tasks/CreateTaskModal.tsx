import React, { useState, useEffect } from 'react';
import { X, Loader2, Calendar, Clock } from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import type { Task } from '../../types/task.types';
import AIAutocomplete from './AIAutocomplete';

interface CreateTaskModalProps {
  onClose: () => void;
  editTask?: Task | null;
}

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ onClose, editTask }) => {
  const { createTask, updateTask } = useTasks();
  const [formData, setFormData] = useState({
    task_title: '',
    task_details: '',
    due_date: '',
    start_time: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (editTask) {
      setFormData({
        task_title: editTask.task_title,
        task_details: editTask.task_details || '',
        due_date: editTask.due_date || '',
        start_time: editTask.start_time || '',
      });
    }
  }, [editTask]);

  const handleSubmit = async () => {
    if (!formData.task_title.trim()) {
      setError('Task title is required');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      if (editTask) {
        await updateTask(editTask.id, {
          task_title: formData.task_title.trim(),
          task_details: formData.task_details.trim(),
          due_date: formData.due_date || null,
          start_time: formData.start_time || null,
          is_completed: editTask.is_completed,
          is_starred: editTask.is_starred,
        });
      } else {
        await createTask({
          task_title: formData.task_title.trim(),
          task_details: formData.task_details.trim() || undefined,
          due_date: formData.due_date || undefined,
          start_time: formData.start_time || undefined,
        });
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save task');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {editTask ? 'Edit Task' : 'Create New Task'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-4 space-y-4" onKeyDown={handleKeyDown}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Task Title *
            </label>
            <input
              type="text"
              value={formData.task_title}
              onChange={(e) => setFormData({ ...formData, task_title: e.target.value })}
              placeholder="e.g., Complete project proposal"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              autoFocus
            />
            <AIAutocomplete
                value={formData.task_title}
                onSelect={(suggestion) => setFormData({ ...formData, task_title: suggestion })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.task_details}
              onChange={(e) => setFormData({ ...formData, task_details: e.target.value })}
              placeholder="Add any additional details..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Due Date
              </label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 inline mr-1" />
                Start Time
              </label>
              <input
                type="time"
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              />
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {editTask ? 'Saving...' : 'Creating...'}
                </>
              ) : (
                editTask ? 'Save Changes' : 'Create Task'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateTaskModal;