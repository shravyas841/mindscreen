import { apiClient } from './client';
import { User, TokenResponse } from '../types/auth';
import { AUTH_ENDPOINTS } from './routes';

export const login = async (data: any): Promise<TokenResponse> => {
  const res = await apiClient.post(AUTH_ENDPOINTS.login, data);
  return res.data;
};
export const register = async (data: any): Promise<TokenResponse> => {
  const res = await apiClient.post(AUTH_ENDPOINTS.register, data);
  return res.data;
};
export const getMe = async (): Promise<User> => {
  const res = await apiClient.get(AUTH_ENDPOINTS.me);
  return res.data;
};
