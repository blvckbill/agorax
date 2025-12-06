import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, Plus, Edit, Trash, UserPlus, UserMinus } from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import type { ActivityEvent } from '../../types/collaboration.types';

const ActivityFeed: React.FC = () => {
  const { currentList } = useTasks();
  const [activities] = useState<ActivityEvent[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Listen to WebSocket messages and convert to activities
  useEffect(() => {
    // This would be connected to WebSocket messages
    // For now, showing structure
  }, [currentList]);

  const getActivityIcon = (action: string) => {
    switch (action) {
      case 'task_added':
        return <Plus className="w-4 h-4 text-green-600" />;
      case 'task_updated':
        return <Edit className="w-4 h-4 text-blue-600" />;
      case 'task_deleted':
        return <Trash className="w-4 h-4 text-red-600" />;
      case 'task_completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'user_added':
        return <UserPlus className="w-4 h-4 text-purple-600" />;
      case 'user_removed':
        return <UserMinus className="w-4 h-4 text-orange-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600" />;
    }
  };

  const getActivityText = (activity: ActivityEvent) => {
    switch (activity.action) {
      case 'task_added':
        return `added task "${activity.taskTitle}"`;
      case 'task_updated':
        return `updated task "${activity.taskTitle}"`;
      case 'task_deleted':
        return `deleted task "${activity.taskTitle}"`;
      case 'task_completed':
        return `completed task "${activity.taskTitle}"`;
      case 'user_added':
        return `invited a new member`;
      case 'user_removed':
        return `removed a member`;
      default:
        return 'performed an action';
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  if (!currentList) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition text-sm relative"
      >
        <Activity className="w-4 h-4 text-gray-600" />
        <span className="text-gray-700 font-medium">Activity</span>
        {activities.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {activities.length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="p-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Recent Activity</h3>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {activities.length === 0 ? (
              <div className="p-8 text-center">
                <Activity className="w-12 h-12 mx-auto text-gray-300 mb-2" />
                <p className="text-sm text-gray-500">No recent activity</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {activities.map((activity) => (
                  <div key={activity.id} className="p-3 hover:bg-gray-50">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                        {getActivityIcon(activity.action)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900">
                          <span className="font-medium">{activity.user}</span>{' '}
                          <span className="text-gray-600">{getActivityText(activity)}</span>
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTime(activity.timestamp)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default ActivityFeed;