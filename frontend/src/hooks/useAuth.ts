import { useState } from 'react';
import { authApi } from '@/services/authApi';
import { 
  LoginCredentials, 
  RegisterData,
  OtpVerification,
  PasswordReset 
} from '@/types/auth.types';

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const register = async (data: RegisterData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.register(data);
      return response;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const verifyEmail = async (data: OtpVerification) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.verifyEmail(data);
      return response;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const resendOtp = async (email: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.resendOtp(email);
      return response;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.login(credentials);
      authApi.setToken(response.token);
      return response;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const forgotPassword = async (email: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.forgotPassword({ email });
      return response;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (data: PasswordReset) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.resetPassword(data);
      return response;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authApi.clearToken();
  };

  return {
    register,
    verifyEmail,
    resendOtp,
    login,
    forgotPassword,
    resetPassword,
    logout,
    loading,
    error,
  };
}