import React from 'react';
import { CheckSquare, Star, List } from 'lucide-react';
import type { TaskFilter } from '../../types/task.types';
import { useTasks } from '../../hooks/useTasks';

const TaskFilters: React.FC = () => {
  const { selectedFilter, setFilter } = useTasks();

  const filters: { value: TaskFilter; label: string; icon: React.ReactNode }[] = [
    { value: 'all', label: 'All Tasks', icon: <List className="w-4 h-4" /> },
    { value: 'completed', label: 'Completed', icon: <CheckSquare className="w-4 h-4" /> },
    { value: 'starred', label: 'Starred', icon: <Star className="w-4 h-4" /> },
  ];

  return (
    <div className="flex gap-2 mb-4">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => setFilter(filter.value)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            selectedFilter === filter.value
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {filter.icon}
          {filter.label}
        </button>
      ))}
    </div>
  );
};

export default TaskFilters;