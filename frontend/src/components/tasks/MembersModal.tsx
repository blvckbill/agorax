import React, { useState, useEffect, useCallback } from 'react';
import { X, UserPlus, Crown, Edit, Eye, Trash2, Shield, Loader2 } from 'lucide-react';
import { collaborationApi } from '../../services/collaborationApi';
import InviteUserModal from './InviteUserModal';
import type { ListMember } from '../../types/task.types';

interface MembersModalProps {
  listId: number;
  userRole: 'owner' | 'editor' | 'viewer';
  onClose: () => void;
}

const MembersModal: React.FC<MembersModalProps> = ({ listId, userRole, onClose }) => {
  const [members, setMembers] = useState<ListMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const fetchMembers = useCallback(async () => {
    try {
      const data = await collaborationApi.getMembers(listId);
      setMembers(data);
    } catch (error) {
      console.error('Failed to fetch members:', error);
    } finally {
      setIsLoading(false);
    }
  }, [listId]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const handleRemove = async (userId: number) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;

    setRemovingId(userId);
    try {
      await collaborationApi.removeUser(listId, userId);
      // Optimistic update or refetch
      setMembers(prev => prev.filter(m => m.user_id !== userId));
    } catch (error) {
      console.error('Failed to remove member:', error);
      alert('Failed to remove member');
    } finally {
      setRemovingId(null);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner': return <Crown className="w-4 h-4 text-purple-600" />;
      case 'editor': return <Edit className="w-4 h-4 text-blue-600" />;
      case 'viewer': return <Eye className="w-4 h-4 text-gray-600" />;
      default: return <Shield className="w-4 h-4 text-gray-600" />;
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

  const canManageMembers = (userRole || '').toLowerCase() === 'owner';

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">List Members</h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition">
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-4">
            {canManageMembers && (
              <button
                onClick={() => setShowInvite(true)}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 mb-4 border-2 border-dashed border-gray-300 text-gray-600 rounded-lg hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition"
              >
                <UserPlus className="w-5 h-5" />
                Invite New Member
              </button>
            )}

            {isLoading ? (
              <div className="flex justify-center p-8">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="space-y-2">
                {members.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                        {member.user.first_name[0]}{member.user.last_name[0]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900">
                          {member.user.first_name} {member.user.last_name}
                        </div>
                        <div className="text-sm text-gray-500 truncate">{member.user.email}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${getRoleBadge(member.role)}`}>
                        {getRoleIcon(member.role)}
                        <span className="capitalize">{member.role}</span>
                      </div>

                      {canManageMembers && member.role !== 'owner' && (
                        <button
                          onClick={() => handleRemove(member.user_id)}
                          disabled={removingId === member.user_id}
                          className="p-2 hover:bg-red-100 rounded-lg transition disabled:opacity-50"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-200">
            <button onClick={onClose} className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">
              Close
            </button>
          </div>
        </div>
      </div>

      {showInvite && (
        <InviteUserModal
          listId={listId}
          onClose={() => setShowInvite(false)}
          onInviteSuccess={() => {
            fetchMembers();
          }}
        />
      )}
    </>
  );
};

export default MembersModal;