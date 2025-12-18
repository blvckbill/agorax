import React, { useState, useEffect } from 'react';
import { X, Search, UserPlus, Loader2, AlertCircle } from 'lucide-react';
import { collaborationApi } from '../../services/collaborationApi';
import type { User } from '../../types/task.types';

interface InviteUserModalProps {
  listId: number;
  onClose: () => void;
  onInviteSuccess: () => void;
}

const InviteUserModal: React.FC<InviteUserModalProps> = ({ listId, onClose, onInviteSuccess }) => {
  // Search States
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Selection States
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [role, setRole] = useState<'editor' | 'viewer'>('editor');
  
  // Submission States
  const [isInviting, setIsInviting] = useState(false);
  const [error, setError] = useState('');

  // Debounce Search Logic
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (searchQuery.length >= 2) {
        setIsSearching(true);
        setError('');
        try {
          const results = await collaborationApi.searchUsers(searchQuery);
          setSearchResults(results);
        } catch (err) {
          console.error("Search failed", err);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
      }
    }, 500); // Wait 500ms after typing stops

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleInvite = async () => {
    if (!selectedUser) return;
    
    setIsInviting(true);
    setError('');

    try {
      await collaborationApi.inviteUser(listId, selectedUser.id, role);
      onInviteSuccess();
      onClose();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      console.error('Failed to invite user:', err);
      setError(err.message || 'Failed to send invitation. They might already be a member.');
    } finally {
      setIsInviting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Invite Collaborator</h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-4 space-y-6 overflow-y-auto">
          {/* Search Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Find User
            </label>
            {!selectedUser ? (
              <div className="relative">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  autoFocus
                />
                
                {/* Search Results Dropdown */}
                {(searchResults.length > 0 || isSearching) && searchQuery.length >= 2 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {isSearching ? (
                      <div className="p-3 text-center text-gray-500 text-sm flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" /> Searching...
                      </div>
                    ) : (
                      searchResults.map(user => (
                        <button
                          key={user.id}
                          onClick={() => {
                            setSelectedUser(user);
                            setSearchQuery(''); 
                            setSearchResults([]);
                          }}
                          className="w-full flex items-center gap-3 p-3 hover:bg-blue-50 transition text-left"
                        >
                          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">
                            {user.first_name[0]}{user.last_name[0]}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">{user.first_name} {user.last_name}</div>
                            <div className="text-xs text-gray-500">{user.email}</div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                )}
                
                {!isSearching && searchQuery.length >= 2 && searchResults.length === 0 && (
                   <p className="text-xs text-gray-500 mt-1">No users found.</p>
                )}
              </div>
            ) : (
              // Selected User Card
              <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                    {selectedUser.first_name[0]}{selectedUser.last_name[0]}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{selectedUser.first_name} {selectedUser.last_name}</div>
                    <div className="text-xs text-gray-600">{selectedUser.email}</div>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedUser(null)}
                  className="p-1 hover:bg-blue-200 rounded text-blue-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Role Selection (Your Enhanced UI) */}
          <div className={!selectedUser ? 'opacity-50 pointer-events-none' : ''}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Permission Level
            </label>
            <div className="space-y-3">
              <label className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition
                ${role === 'editor' ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-300 hover:bg-gray-50'}`}>
                <input
                  type="radio"
                  name="role"
                  value="editor"
                  checked={role === 'editor'}
                  onChange={() => setRole('editor')}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">Editor</div>
                  <div className="text-xs text-gray-500">Can add, edit, and delete tasks</div>
                </div>
              </label>

              <label className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition
                ${role === 'viewer' ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-300 hover:bg-gray-50'}`}>
                <input
                  type="radio"
                  name="role"
                  value="viewer"
                  checked={role === 'viewer'}
                  onChange={() => setRole('viewer')}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">Viewer</div>
                  <div className="text-xs text-gray-500">Read-only access to tasks</div>
                </div>
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-xl flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleInvite}
            disabled={!selectedUser || isInviting}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isInviting ? (
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
  );
};

export default InviteUserModal;