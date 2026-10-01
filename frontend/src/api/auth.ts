import { apiClient } from './client';
import { User, TokenResponse } from '../types/auth';

export const login = async (data: any): Promise<TokenResponse> => {
  const res = await apiClient.post('/api/auth/login', data);
  return res.data;
};
export const register = async (data: any): Promise<TokenResponse> => {
  const res = await apiClient.post('/api/auth/register', data);
  return res.data;
};
export const getMe = async (): Promise<User> => {
  const res = await apiClient.get('/api/auth/me');
  return res.data;
};
