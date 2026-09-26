import assert from 'node:assert/strict';
import test from 'node:test';

import { AUTH_ENDPOINTS } from './routes.ts';

test('frontend authentication routes use the backend /api/auth prefix', () => {
  assert.equal(AUTH_ENDPOINTS.register, '/api/auth/register');
  assert.equal(AUTH_ENDPOINTS.login, '/api/auth/login');
  assert.equal(AUTH_ENDPOINTS.me, '/api/auth/me');
  assert.equal(AUTH_ENDPOINTS.refresh, '/api/auth/refresh');
});
