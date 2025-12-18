import React, { useState } from 'react';
import { Check, Star, Trash2, Edit2, Calendar, Clock } from 'lucide-react';
import type { Task } from '../../types/task.types';
import { useTasks } from '../../hooks/useTasks';

interface TaskItemProps {
  task: Task;
  onEdit: (task: Task) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, onEdit }) => {
  const { toggleTaskComplete, toggleTaskStarred, deleteTask } = useTasks();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      setIsDeleting(true);
      try {
        await deleteTask(task.id);
      } catch (error) {
        console.error('Failed to delete task:', error);
        setIsDeleting(false);
      }
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatTime = (timeStr: string | null) => {
    if (!timeStr) return null;
    return timeStr.substring(0, 5); // HH:MM format
  };

  return (
    <div
      className={`group bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition ${
        task.is_completed ? 'opacity-60' : ''
      } ${isDeleting ? 'opacity-50 pointer-events-none' : ''}`}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <button
          onClick={() => toggleTaskComplete(task.id)}
          className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition ${
            task.is_completed
              ? 'bg-blue-600 border-blue-600'
              : 'border-gray-300 hover:border-blue-600'
          }`}
        >
          {task.is_completed && <Check className="w-3 h-3 text-white" />}
        </button>

        {/* Task Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3
              className={`text-sm font-medium text-gray-900 ${
                task.is_completed ? 'line-through text-gray-500' : ''
              }`}
            >
              {task.task_title}
            </h3>

            {/* Star Button */}
            <button
              onClick={() => toggleTaskStarred(task.id)}
              className="flex-shrink-0"
            >
              <Star
                className={`w-4 h-4 transition ${
                  task.is_starred
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-400 hover:text-yellow-400'
                }`}
              />
            </button>
          </div>

          {task.task_details && (
            <p className="text-sm text-gray-600 mt-1">{task.task_details}</p>
          )}

          {/* Date and Time */}
          {(task.due_date || task.start_time) && (
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              {task.due_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(task.due_date)}
                </div>
              )}
              {task.start_time && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTime(task.start_time)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
          <button
            onClick={() => onEdit(task)}
            className="p-1.5 hover:bg-gray-100 rounded transition"
          >
            <Edit2 className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={handleDelete}
            className="p-1.5 hover:bg-red-100 rounded transition"
          >
            <Trash2 className="w-4 h-4 text-red-600" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default TaskItem;