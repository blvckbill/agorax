import type { LoginResponse, RegisterResponse, User } from '../types/auth.types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiService {
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
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    return this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(
    email: string,
    password: string,
    first_name: string,
    last_name: string
  ): Promise<RegisterResponse> {
    return this.request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, first_name, last_name }),
    });
  }

  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('No token found');

    // Decode JWT to get user ID (simple base64 decode of payload)
    const payload = JSON.parse(atob(token.split('.')[1]));
    const userId = payload.sub;

    return this.request<User>(`/auth/${userId}`);
  }
}

export const api = new ApiService(API_BASE_URL);