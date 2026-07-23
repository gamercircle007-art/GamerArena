export const environment = {
  production: true,
  /** Main FastAPI on Render (same backend as Flutter). Includes /api/v1. */
  apiUrl: 'https://gamer-circle-api.onrender.com/api/v1',
  /** Never mask live API failures with mock data in production. */
  useMockFallback: false,
};
