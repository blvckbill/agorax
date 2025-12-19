import type { User } from '../types/auth.types'; // Assuming you have this, or use the one defined above
import type {
  InviteResponse,
  RemoveUserResponse,
  ListMember
} from '../types/task.types';

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE_URL = `${apiUrl}/api/v1`;

class CollaborationApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = localStorage.getItem('token');

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Fetch all members of a specific list
  async getMembers(listId: number): Promise<ListMember[]> {
    return this.request<ListMember[]>(`/tasks/${listId}/members`);
  }

  // Invite a user (Changed to use POST body)
  async inviteUser(listId: number, inviteeId: number, role: string): Promise<InviteResponse> {
    return this.request<InviteResponse>(`/tasks/${listId}/invite`, {
      method: 'POST',
      body: JSON.stringify({ invitee_id: inviteeId, role }),
    });
  }

  async removeUser(listId: number, userId: number): Promise<RemoveUserResponse> {
    return this.request<RemoveUserResponse>(`/tasks/${listId}/remove-user?user_id=${userId}`, {
      method: 'POST',
    });
  }

  // Search users by email (Needs a backend endpoint like /users/search?q=...)
  async searchUsers(query: string): Promise<User[]> {
    return this.request<User[]>(`/users/search?q=${encodeURIComponent(query)}`);
  }
}

export const collaborationApi = new CollaborationApiService(API_BASE_URL);