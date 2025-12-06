export interface ListMember {
  id: number;
  user_id: number;
  list_id: number;
  role: 'owner' | 'editor' | 'viewer';
  user?: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
}

export interface InviteUserInput {
  invitee_id: number;
  role: 'editor' | 'viewer';
}

export interface ActivityEvent {
  id: string;
  action: string;
  user: string;
  timestamp: Date;
  taskTitle?: string;
}