import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold text-gray-900">Task Manager</h1>
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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle2 className="w-8 h-8 text-green-600" />
            <h2 className="text-2xl font-bold text-gray-900">
              Welcome, {user?.first_name}! 🎉
            </h2>
          </div>
          <p className="text-gray-600 mb-6">
            Authentication is working! You're successfully logged in.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Next step:</strong> We'll add task management features (lists, tasks, real-time collaboration) in the next iteration.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;