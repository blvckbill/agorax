import React, { useState } from 'react';
import { X, Loader2, UserPlus } from 'lucide-react';
import { collaborationApi } from '../../services/collaborationApi';

interface InviteUserModalProps {
  listId: number;
  onClose: () => void;
}

const InviteUserModal: React.FC<InviteUserModalProps> = ({ listId, onClose }) => {
  const [inviteeId, setInviteeId] = useState('');
  const [role, setRole] = useState<'editor' | 'viewer'>('editor');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleInvite = async () => {
    if (!inviteeId.trim()) {
      setError('User ID is required');
      return;
    }

    const userId = parseInt(inviteeId.trim());
    if (isNaN(userId)) {
      setError('Invalid user ID');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      await collaborationApi.inviteUser(listId, userId, role);
      setSuccess(`User invited as ${role} successfully!`);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invite user');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleInvite();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Invite Collaborator</h2>
          </div>
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
              User ID *
            </label>
            <input
              type="number"
              value={inviteeId}
              onChange={(e) => setInviteeId(e.target.value)}
              placeholder="Enter user ID to invite"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              autoFocus
            />
            <p className="text-xs text-gray-500 mt-1">
              💡 Tip: You can find user IDs from your organization directory
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Role *
            </label>
            <div className="space-y-2">
              <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition">
                <input
                  type="radio"
                  name="role"
                  value="editor"
                  checked={role === 'editor'}
                  onChange={(e) => setRole(e.target.value as 'editor')}
                  className="w-4 h-4 text-blue-600"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">Editor</div>
                  <div className="text-xs text-gray-500">Can add, edit, and delete tasks</div>
                </div>
              </label>
              
              <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition">
                <input
                  type="radio"
                  name="role"
                  value="viewer"
                  checked={role === 'viewer'}
                  onChange={(e) => setRole(e.target.value as 'viewer')}
                  className="w-4 h-4 text-blue-600"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">Viewer</div>
                  <div className="text-xs text-gray-500">Can only view tasks (read-only)</div>
                </div>
              </label>
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg flex items-center gap-2">
              <span>❌</span>
              {error}
            </div>
          )}

          {success && (
            <div className="text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg flex items-center gap-2">
              <span>✅</span>
              {success}
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
              onClick={handleInvite}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Inviting...
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Send Invite
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteUserModal;