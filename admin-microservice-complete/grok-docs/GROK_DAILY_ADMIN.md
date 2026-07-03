# ADMIN MICROSERVICE — DAILY SESSION PROMPT
# Paste this every day at the start of a Grok session.
# ═══════════════════════════════════════════════════════

You are building a **separate React + FastAPI admin microservice** for GameConnect.
NOT the Flutter app. NOT the main FastAPI backend. This is admin-microservice/.

## Context Files in This Project
- `GROK_FIRST_SESSION_ADMIN.md` — full spec: DB models, permissions, all API endpoints, all React pages, folder structure
- `PROGRESS_ADMIN.md` — task checklist (AM-B01, AM-F01, AM-P01... format)

## Do This Now
```bash
# Find your next task:
cat PROGRESS_ADMIN.md | grep "^\- \[ \]" | head -5

# Check what exists:
find . -type f \( -name "*.py" -o -name "*.tsx" -o -name "*.ts" \) | grep -v node_modules | grep -v __pycache__ | sort
```
Build first unchecked `[ ]` task → mark `[x] DONE YYYY-MM-DD` → continue.

## Stack Reminder
- Backend: FastAPI async port 8001 (NOT port 8000 — that's main app)
- Frontend: React 18 + TypeScript + Vite port 3001
- Styling: Tailwind CSS + shadcn/ui (Radix UI)
- Charts: Recharts
- Tables: TanStack Table v8
- Data fetching: TanStack Query v5
- State: Zustand
- Forms: React Hook Form + Zod

## Rules (always)
- TypeScript: no `any`. All types in src/types/index.ts.
- Permissions: every action wrapped in `hasPermission()` check.
- Mutations: always `queryClient.invalidateQueries()` on success + toast.
- Activity log: every admin write action calls activity_service.log_action().
- FastAPI: async/await + Depends() for db, admin_user, permission checks.
- New DB model: alembic revision --autogenerate → alembic upgrade head.
- Show COMPLETE file code. No truncation. Confirm saved. Then next task.

## Run Commands
```bash
# Backend:
cd admin-microservice/backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --port 8001 --reload

# Frontend:
cd admin-microservice/frontend
npm install
npm run dev      # http://localhost:3001

# Or Docker:
docker compose up --build
```

## If Context Lost Mid-Session
"Re-read GROK_FIRST_SESSION_ADMIN.md. We were on task [AM-XXX]. Continue."

Start now → check progress → build next task.
