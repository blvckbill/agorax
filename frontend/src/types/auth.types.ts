export interface User {
  id: number;
  email: string;
  token: string;
  is_verified: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface AuthResponse {
  detail: string;
  token: string;
}

export interface OtpVerification {
  email: string;
  otp_code: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  email: string;
  otp_code: string;
  new_password: string;
}