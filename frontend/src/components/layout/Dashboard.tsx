import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { TaskProvider } from '../../contexts/TaskContext';
import ListSidebar from '../tasks/ListSidebar';
import TaskList from '../tasks/TaskList';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <TaskProvider>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Header */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <h1 className="text-xl font-bold text-gray-900">📋 Task Manager</h1>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-700">
                  {user?.first_name} {user?.last_name}
                </span>
                <button
                  onClick={logout}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          <ListSidebar />
          <TaskList />
        </div>
      </div>
    </TaskProvider>
  );
};

export default Dashboard;