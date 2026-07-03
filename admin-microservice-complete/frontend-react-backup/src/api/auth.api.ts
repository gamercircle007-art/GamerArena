import { apiClient } from './client';
import { devApi, USE_MOCK } from '../mocks/devData';
import type { AuthResponse } from '../types';

export interface SignupRequestPayload {
  name: string;
  username: string;
  email: string;
  phone_number: string;
}

export const authApi = {
  sendOtp: (phone: string) =>
    USE_MOCK ? devApi.sendOtp() : apiClient.post('/auth/login/request-otp', { phone_number: phone }),
  verifyOtp: (phone: string, otp: string) =>
    USE_MOCK ? devApi.verifyOtp(phone, otp) : apiClient.post<AuthResponse>('/auth/login/verify-otp', { phone_number: phone, otp }),
  signupRequestOtp: (payload: SignupRequestPayload) =>
    USE_MOCK ? devApi.sendOtp() : apiClient.post('/auth/signup/request-otp', payload),
  signupVerifyOtp: (phone: string, otp: string, password: string) =>
    USE_MOCK ? devApi.verifyOtp(phone, otp) : apiClient.post<AuthResponse>('/auth/signup/verify-otp', { phone_number: phone, otp, password }),
  loginGoogle: (id_token: string) => apiClient.post<AuthResponse>('/auth/google', { id_token }),
  refresh: (refresh_token: string) => USE_MOCK
    ? Promise.resolve({ data: { access_token: 'dev-mock-access-token' } })
    : apiClient.post<{ access_token: string }>('/auth/refresh', { refresh_token }),
  logout: () => USE_MOCK ? devApi.noop() : apiClient.post('/auth/logout'),
  devLogin: (role?: AuthResponse['user']['role']) => devApi.devLogin(role),
};