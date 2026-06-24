# Paythan Backend

Modular monolith FastAPI backend with enterprise authentication, domain-driven design, and microservice-ready structure.

## Architecture

```
app/
├── core/              # config.py, security.py, dependencies.py, logging.py
├── domains/
│   ├── auth/          # Signup, login, JWT, OTP providers
│   │   ├── providers/ # Swappable OTP + OAuth stubs
│   │   └── services/  # signup, login, token, otp_store
│   └── user/          # User profiles
├── db/                # SQLAlchemy async session
└── main.py            # FastAPI app (auth router mounted here)
```

---

## Authentication Setup

Paythan uses a **two-flow** authentication system:

| Flow | Steps | Result |
|------|-------|--------|
| **Signup** | Name + Email + Phone → WhatsApp OTP → OTP + Password | Account created + JWT |
| **Login** | Phone + Password | JWT access + refresh tokens |

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/signup/request-otp` | No | Send WhatsApp OTP |
| POST | `/api/v1/auth/signup/verify-otp` | No | Verify OTP, set password, create account |
| POST | `/api/v1/auth/login` | No | Phone + password login |
| POST | `/api/v1/auth/refresh-token` | No | Rotate refresh token |
| GET | `/api/v1/auth/me` | Yes | Current user profile |
| POST | `/api/v1/auth/logout` | Yes | Revoke refresh token |

Interactive docs: http://localhost:8000/docs

---

## Complete Signup & Login Flow (curl)

### Prerequisites

```bash
cp .env.example .env
# Set JWT_SECRET_KEY (32+ chars):
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up -d
docker compose exec backend alembic upgrade head
```

### Signup

```bash
# Step 1 — Request WhatsApp OTP
curl -X POST http://localhost:8000/api/v1/auth/signup/request-otp \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone_number": "+919876543210"
  }'

# Response: {"message":"OTP sent to your WhatsApp number...","success":true}

# Step 2 — Verify OTP and set password (creates account + returns tokens)
curl -X POST http://localhost:8000/api/v1/auth/signup/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp": "123456",
    "password": "SecurePass1"
  }'

# Response: {"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer",...}
```

**Local dev without Twilio:** OTP is logged to the backend console:
```bash
docker compose logs -f backend | grep whatsapp_otp_dev_mode
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "password": "SecurePass1"
  }'
```

### Authenticated Requests

```bash
# Get profile
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# Refresh tokens
curl -X POST http://localhost:8000/api/v1/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

## Twilio WhatsApp Sandbox Setup

1. **Create account** at [twilio.com](https://www.twilio.com/)
2. **Console** → Messaging → Try it out → Send a WhatsApp message
3. **Join sandbox** — send the join code from your WhatsApp to `+1 415 523 8886`
4. **Copy credentials** from the Twilio Console dashboard:
   - Account SID → `TWILIO_ACCOUNT_SID`
   - Auth Token → `TWILIO_AUTH_TOKEN`
5. **Configure `.env`:**
   ```env
   OTP_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```
6. **Restart** backend: `docker compose restart backend`
7. **Test** with the same phone number you used to join the sandbox

---

## Environment Variables

All variables are documented in `.env.example`. Key groups:

### Required

| Variable | Where to get it |
|----------|-----------------|
| `JWT_SECRET_KEY` | Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis connection (`redis://host:6379/0`) |

### JWT

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |

### OTP & Security

| Variable | Default | Description |
|----------|---------|-------------|
| `OTP_EXPIRE_MINUTES` | 10 | OTP validity |
| `OTP_RATE_LIMIT_COUNT` | 5 | Max OTP requests per window |
| `OTP_RATE_LIMIT_WINDOW_MINUTES` | 10 | Rate limit window |
| `LOGIN_MAX_ATTEMPTS` | 5 | Failed logins before lockout |
| `LOGIN_LOCKOUT_MINUTES` | 15 | Lockout duration |
| `ARGON2_TIME_COST` | 3 | Argon2 iterations |
| `ARGON2_MEMORY_COST` | 65536 | Argon2 memory (KB) |

### Twilio

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio Console → Account Info |
| `TWILIO_AUTH_TOKEN` | Twilio Console → Account Info |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` (sandbox) |

### Future Auth (scaffolded)

| Variable | Purpose |
|----------|---------|
| `AUTH_METHODS` | Enabled methods: `whatsapp_otp,password,google,...` |
| `GOOGLE_OAUTH_ENABLED` | Enable Google Sign In |
| `GOOGLE_CLIENT_ID` | Google Cloud Console → OAuth credentials |
| `EMAIL_OTP_ENABLED` | Enable email OTP alternative |
| `TWILIO_SMS_FROM` | SMS OTP fallback number |

---

## Security Best Practices

| Practice | Implementation |
|----------|----------------|
| Password hashing | Argon2 via passlib (memory-hard, GPU-resistant) |
| OTP storage | Redis with TTL, single-use, rate limited |
| JWT access tokens | Short-lived (30 min), stateless verification |
| JWT refresh tokens | Long-lived with `jti` in Redis, rotated on refresh |
| Brute-force protection | Redis lockout after 5 failed logins |
| SQL injection | SQLAlchemy parameterized queries only |
| User enumeration | Generic error: "Invalid phone number or password" |
| Secrets | Environment variables only, never in code |
| HTTP headers | CORS, X-Frame-Options, HSTS (prod), no-store cache |
| Logging | Structured events — passwords/OTPs never logged |
| Input validation | Pydantic v2 strict schemas on all endpoints |

**Production checklist:**
- Set `APP_ENV=prod`, `DEBUG=false`, `LOG_JSON=true`
- Store secrets in AWS Secrets Manager
- Rotate `JWT_SECRET_KEY` periodically
- Use Twilio production WhatsApp number (not sandbox)
- Enable HTTPS via ALB/API Gateway

---

## User Model

```python
# app/domains/user/models.py
id              # UUID primary key
full_name       # → API field: name
email           # Unique, indexed
phone           # → API field: phone_number, E.164, unique
hashed_password # Argon2 hash (never plaintext)
is_active       # Account enabled
is_verified     # OTP verified during signup
email_verified  # Set true on signup
phone_verified  # Set true on signup
created_at      # Auto timestamp
updated_at      # Auto timestamp
```

---

## Extending Authentication

### Add Email OTP

1. Implement `EmailOTPProvider.send_otp()` in `providers/email_otp.py`
2. Register: already in `providers/__init__.py` as `email`
3. Set `OTP_PROVIDER=email`, `EMAIL_OTP_ENABLED=true`, configure `EMAIL_*`
4. Add channel param to signup request schema (optional)

### Add SMS OTP Fallback

1. Implement `TwilioSmsProvider.send_otp()` in `providers/sms_otp.py`
2. Set `OTP_PROVIDER=twilio_sms`, `TWILIO_SMS_FROM=+1...`
3. Add fallback logic in `SignupService` if WhatsApp delivery fails

### Add Google Sign In

1. **Google Cloud Console** → Create OAuth 2.0 credentials
2. Set env vars:
   ```env
   GOOGLE_OAUTH_ENABLED=true
   GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxx
   AUTH_METHODS=whatsapp_otp,password,google
   ```
3. Implement `GoogleOAuthProvider.verify_id_token()` in `providers/oauth/google.py`
4. Add route in `auth/router.py`:
   ```python
   @router.post("/oauth/google", response_model=TokenResponse)
   async def google_login(body: GoogleTokenRequest, ...):
       # 1. Verify id_token via GoogleOAuthProvider
       # 2. Find or create user by email
       # 3. Issue JWT via TokenService.issue_tokens()
   ```
5. **Client app**: use your platform's Google Sign-In SDK, send `id_token` to backend
6. **Recommended**: add `user_identities` table linking `provider` + `provider_user_id` → `user.id`

### Add Apple Sign In

Same pattern as Google using `providers/oauth/` — verify Apple identity token with Apple's JWKS.

### Provider Architecture

```
SignupService
    └── get_otp_provider(settings)  ← factory in providers/__init__.py
            ├── TwilioWhatsAppProvider  (production)
            ├── TwilioSmsProvider       (stub)
            └── EmailOTPProvider        (stub)

AuthService (future OAuth)
    └── GoogleOAuthProvider.verify_id_token()
    └── AppleOAuthProvider.verify_id_token()
```

---

## Local Setup

```bash
cd backend
poetry install
cp .env.example .env
docker compose -f ../docker-compose.yml up postgres redis -d
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

## Testing

```bash
poetry run pytest -v
poetry run pytest tests/test_auth_schemas.py tests/test_security.py -v
```

## Adding a New Domain

```bash
mkdir -p app/domains/payments
# Add router, service, repository, schemas, models
# Register in app/main.py:
app.include_router(payments_router, prefix=settings.api_v1_prefix)
```

## Production Deployment (AWS ECS)

1. `docker build --target production -t paythan-backend .`
2. Push to ECR, deploy on ECS Fargate
3. RDS PostgreSQL + ElastiCache Redis + Secrets Manager
4. Run migrations as ECS one-off task before deploy

See `../infra/terraform/` and `../paythan-docs/` for detailed guides.