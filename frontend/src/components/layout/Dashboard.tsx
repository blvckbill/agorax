import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { TaskProvider } from '../../contexts/TaskContext';
import ListSidebar from '../tasks/ListSidebar';
import TaskList from '../tasks/TaskList';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <TaskProvider>
      <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
        <nav className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <h1 className="text-xl font-bold text-gray-900">💠 Agorax</h1>
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

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          <aside className="w-64 flex-shrink-0 overflow-y-auto border-r border-gray-200 bg-white">
            <ListSidebar />
          </aside>
          <main className="flex-1 overflow-y-auto">
             <TaskList />
          </main>

        </div>
      </div>
    </TaskProvider>
  );
};

export default Dashboard;