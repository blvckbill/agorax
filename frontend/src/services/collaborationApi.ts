import type { User } from '../types/auth.types';
import type {
    InviteResponse,
    RemoveUserResponse
} from '../types/task.types';

const API_BASE_URL = 'http://localhost:8000';

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

  async inviteUser(listId: number, inviteeId: number, role: string): Promise<InviteResponse> {
    return this.request(`/tasks/${listId}/invite-user?invitee_id=${inviteeId}&role=${role}`, {
      method: 'POST',
    });
  }

  async removeUser(listId: number, userId: number): Promise<RemoveUserResponse> {
    return this.request(`/tasks/${listId}/remove-user?user_id=${userId}`, {
      method: 'POST',
    });
  }

  // Search users by email (you may need to add this endpoint to your backend)
  async searchUsers(query: string): Promise<User[]> {
    // For now, this is a placeholder - you'll need to implement user search in backend
    return this.request<User[]>(`/auth/search?q=${encodeURIComponent(query)}`);
  }
}

export const collaborationApi = new CollaborationApiService(API_BASE_URL);