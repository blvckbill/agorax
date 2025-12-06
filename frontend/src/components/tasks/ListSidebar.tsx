import React, { useState } from 'react';
import { Plus, List, Trash2} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import CreateListModal from './CreateListModal';

const canDelete = (role: string) => role === 'owner';

const ListSidebar: React.FC = () => {
  const { lists, currentList, selectList, deleteList } = useTasks();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleDelete = async (listId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this list?')) {
      try {
        await deleteList(listId);
      } catch (error) {
        console.error('Failed to delete list:', error);
      }
    }
  };

  const getRoleBadge = (role: string) => {
    const colors = {
      owner: 'bg-purple-100 text-purple-700',
      editor: 'bg-blue-100 text-blue-700',
      viewer: 'bg-gray-100 text-gray-700',
    };
    return colors[role as keyof typeof colors] || colors.viewer;
  };

  return (
    <>
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => setShowCreateModal(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <Plus className="w-4 h-4" />
            New List
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {lists.length === 0 ? (
            <div className="text-center py-8 px-4">
              <List className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <p className="text-sm text-gray-500">No lists yet</p>
              <p className="text-xs text-gray-400 mt-1">Create your first list to get started</p>
            </div>
          ) : (
            <div className="space-y-1">
              {lists.map((list) => (
                <div
                  key={list.id}
                  onClick={() => selectList(list.id)}
                  className={`group relative flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition ${
                    currentList?.id === list.id
                      ? 'bg-blue-50 text-blue-700'
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <List className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm font-medium truncate">{list.title}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <span className={`text-xs px-2 py-0.5 rounded ${getRoleBadge(list.user_role)}`}>
                      {list.user_role}
                    </span>
                    
                    {canDelete(list.user_role) && (
                        <button
                            onClick={(e) => handleDelete(list.id, e)}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition"
                        >
                            <Trash2 className="w-3 h-3 text-red-600" />
                        </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showCreateModal && (
        <CreateListModal onClose={() => setShowCreateModal(false)} />
      )}
    </>
  );
};

export default ListSidebar;