export const environment = {
  production: false,
  /** Local main FastAPI (not the mock admin microservice). Includes /api/v1. */
  apiUrl: 'http://localhost:8000/api/v1',
  /** Dev convenience: fall back to mocks if main API is down. */
  useMockFallback: true,
};
