import type {
    TodoList,
    Task,
    CreateListInput,
    CreateTaskInput,
    UpdateTaskInput,
    PaginatedResponse,
    InviteResponse,
    RemoveUserResponse
} from '../types/task.types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class TaskApiService {
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

  // Lists
  async getAllLists(userId: number, page: number = 1): Promise<PaginatedResponse<TodoList>> {
    return this.request<PaginatedResponse<TodoList>>(
      `/tasks/${userId}/todolists?page=${page}&itemsPerPage=50`
    );
  }

  async getList(listId: number): Promise<TodoList> {
    return this.request<TodoList>(`/tasks/${listId}`);
  }

  async createList(data: CreateListInput): Promise<TodoList> {
    return this.request<TodoList>('/tasks/create-list', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateList(listId: number, title: string): Promise<TodoList> {
    return this.request<TodoList>(`/tasks/${listId}/update-list`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    });
  }

  async deleteList(listId: number): Promise<void> {
    await this.request(`/tasks/${listId}/delete-list`, {
      method: 'DELETE',
    });
  }

  // Tasks
  async getTasks(listId: number, page: number = 1): Promise<PaginatedResponse<Task>> {
    return this.request<PaginatedResponse<Task>>(
      `/tasks/${listId}/tasks?page=${page}&itemsPerPage=100`
    );
  }

  async getCompletedTasks(listId: number, page: number = 1): Promise<PaginatedResponse<Task>> {
    return this.request<PaginatedResponse<Task>>(
      `/tasks/${listId}/tasks-completed?page=${page}&itemsPerPage=100`
    );
  }

  async getStarredTasks(page: number = 1): Promise<PaginatedResponse<Task>> {
    return this.request<PaginatedResponse<Task>>(
      `/tasks/starred-tasks?page=${page}&itemsPerPage=100`
    );
  }

  async createTask(listId: number, data: CreateTaskInput): Promise<Task> {
    return this.request<Task>(`/tasks/${listId}/add-task`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTask(listId: number, taskId: number, data: UpdateTaskInput): Promise<Task> {
    return this.request<Task>(`/tasks/${listId}/${taskId}/update-task`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTask(listId: number, taskId: number): Promise<void> {
    await this.request(`/tasks/${listId}/${taskId}/delete-task`, {
      method: 'DELETE',
    });
  }

  // Collaboration
  async inviteUser(listId: number, inviteeId: number, role: string): Promise<InviteResponse> {
    return this.request(`/tasks/${listId}/invite-user`, {
      method: 'POST',
      body: JSON.stringify({ invitee_id: inviteeId, role }),
    });
  }

  async removeUser(listId: number, userId: number): Promise<RemoveUserResponse> {
    return this.request(`/tasks/${listId}/remove-user`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }
}

export const taskApi = new TaskApiService(API_BASE_URL);