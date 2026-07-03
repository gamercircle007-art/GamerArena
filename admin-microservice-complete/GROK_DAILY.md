# GROK — ADMIN MS DAILY SESSION
# Paste at start of every session.
# ────────────────────────────────────────────

You are building the GameConnect admin microservice.
Tech: React 18 + TypeScript + Vite + TailwindCSS + TanStack Query + Recharts

## Do This Now
```bash
cat PROGRESS_ADMIN.md | grep "^\- \[ \]" | head -5
```
Find first `[ ]` task → build it completely → mark `[x]` with date → next.

## Rules
- No `any` types. Proper interfaces from src/types/index.ts.
- useQuery for all data fetching. useMutation for actions.
- usePermissions() to guard every action button.
- Every table: loading skeleton + empty state + error state.
- Every destructive action: ConfirmModal first.
- Pattern reference: UsersPage.tsx (complete, working, use same structure)
- Roles/perms reference: src/utils/permissions.ts

## Run
```bash
cd frontend && npm run dev     # localhost:3000
npm run build                  # check for TypeScript errors
```

Start → `cat PROGRESS_ADMIN.md` → build next unchecked task.
