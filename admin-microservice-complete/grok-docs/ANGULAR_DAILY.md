# GROK — ANGULAR ADMIN DAILY SESSION
# Paste at start of EVERY Grok session (after first session).
# ─────────────────────────────────────────────────────────────

You are building the GameConnect Angular 21 admin panel.
Backend API: http://localhost:8000/v1

## Context Files
- `GROK_ANGULAR_CONTEXT.md` — full stack, routing, design system, coding rules
- `PROGRESS_ANGULAR.md` — task checklist (find first [ ] task and build it)
- `API_REFERENCE.md` — backend endpoints (generated from STEP1_SCAN_BACKEND.md)

## Do This Now
```bash
cat PROGRESS_ANGULAR.md | grep "^\- \[ \]" | head -5
```
Find first unchecked `[ ]` → read relevant existing files → build it completely.

## Angular 21 Rules (always follow)
- Standalone components only. No NgModule.
- `inject()` for DI. Signals for state. `@if/@for/@switch` template syntax.
- ngx-datatable for tables. ng2-charts for charts.
- SweetAlert2 for confirm dialogs. ngx-toastr for notifications.
- Bootstrap 5 + ngx-bootstrap for UI. No other CSS frameworks.
- OnPush change detection on all components.
- takeUntilDestroyed() in all subscriptions.

## Commands
```bash
ng serve --port 4200          # run dev server
ng generate component feature/name --standalone  # new component
ng build --configuration=production  # production build
```

## If Grok loses context
```
Re-read GROK_ANGULAR_CONTEXT.md. We were building task [TASK-ID]. Continue.
```

Start → `cat PROGRESS_ANGULAR.md` → build next `[ ]` task.
