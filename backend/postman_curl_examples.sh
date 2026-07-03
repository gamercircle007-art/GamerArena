#!/usr/bin/env bash
# Paythan API — copy/paste into Postman (Import → Raw Text) or run in terminal
# Base URL
BASE="http://localhost:8000/api/v1"

# 1. Health check
curl -X GET "$BASE/../health"

# 2. Signup — request WhatsApp OTP
curl -X POST "$BASE/auth/signup/request-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "username": "janedoe",
    "email": "jane@example.com",
    "phone_number": "+919876543210"
  }'

# 3. Signup — verify OTP + set password (replace OTP from server logs in local dev)
curl -X POST "$BASE/auth/signup/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp": "123456",
    "password": "SecurePass1"
  }'

# 4. Login — request OTP (replace phone with registered number)
curl -X POST "$BASE/auth/login/request-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210"
  }'

# 5. Login — verify OTP (replace OTP from server logs in local dev)
curl -X POST "$BASE/auth/login/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp": "123456"
  }'

# 6. Login — username + password
curl -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "janedoe",
    "password": "SecurePass1"
  }'

# 7. Get current user (replace ACCESS_TOKEN)
curl -X GET "$BASE/auth/me" \
  -H "Authorization: Bearer ACCESS_TOKEN"

# 8. Refresh token (replace REFRESH_TOKEN)
curl -X POST "$BASE/auth/refresh-token" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REFRESH_TOKEN"}'

# 9. Logout (replace tokens)
curl -X POST "$BASE/auth/logout" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REFRESH_TOKEN"}'