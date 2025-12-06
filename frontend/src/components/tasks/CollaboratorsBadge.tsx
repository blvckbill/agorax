import React, { useState } from 'react';
import { Users } from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import MembersModal from './MembersModal';

const CollaboratorsBadge: React.FC = () => {
  const { currentList } = useTasks();
  const [showMembers, setShowMembers] = useState(false);

  if (!currentList) return null;

  return (
    <>
      <button
        onClick={() => setShowMembers(true)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition text-sm"
      >
        <Users className="w-4 h-4 text-gray-600" />
        <span className="text-gray-700 font-medium">Collaborators</span>
      </button>

      {showMembers && (
        <MembersModal
          listId={currentList.id}
          userRole={currentList.user_role}
          onClose={() => setShowMembers(false)}
        />
      )}
    </>
  );
};

export default CollaboratorsBadge;