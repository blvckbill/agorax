export interface TodoList {
  id: number;
  title: string;
  user_role: 'owner' | 'editor' | 'viewer';
}

export interface Task {
  id: number;
  list_id: number;
  task_title: string;
  task_details: string | null;
  due_date: string | null; // ISO date string
  start_time: string | null; // ISO time string
  is_completed: boolean;
  is_starred: boolean;
}

export interface CreateListInput {
  title: string;
}

export interface CreateTaskInput {
  task_title: string;
  task_details?: string;
  due_date?: string;
  start_time?: string;
}

export interface UpdateTaskInput {
  task_title?: string;
  task_details?: string | null;
  due_date?: string | null;
  start_time?: string | null;
  is_completed?: boolean;
  is_starred?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  itemsPerPage: number;
  page: number;
  total: number;
}

export interface InviteResponse {
  msg: string;
  member_id: number;
  role: string;
}

export interface RemoveUserResponse {
  msg: string;
  user_id: number;
  list_id: number;
}

export interface WebSocketMessage {
  action: 'task_added' | 'task_updated' | 'task_deleted' | 'list_title_update' | 'user_added' | 'user_removed';
  task?: Task;
  list?: TodoList;
  member?: { user_id: number; role: string };
}

export type TaskFilter = 'all' | 'completed' | 'starred';