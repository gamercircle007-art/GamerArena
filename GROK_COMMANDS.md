# GROK QUICK COMMANDS — Copy-Paste Any Time
# Keep this open in a tab. Grab whatever you need.

---

## START OF SESSION (paste this every day)
```
Read GROK_FIRST_SESSION.md for full project context.
Read PROGRESS.md and find the first unchecked [ ] task.
Build it completely, then continue to the next.
Show complete file code for everything you create.
```

---

## IF GROK FORGETS CONTEXT MID-SESSION
```
Re-read GROK_FIRST_SESSION.md.
We were building task [P1-DB01]. Continue from there.
Tech stack: FastAPI async + SQLAlchemy 2.0 + Flutter Riverpod. No deviations.
```

---

## TO BUILD A SPECIFIC TASK
```
Build task P1-BK01: booking_service.py with Redis SETNX lock.
Use the exact pattern from GROK_FIRST_SESSION.md under "SLOT BOOKING — CRITICAL PATTERN".
```

---

## TO CHECK WHAT EXISTS
```bash
find . -name "*.py" | grep -v __pycache__ | sort
find . -name "*.dart" | grep -v build | sort
cat PROGRESS.md
cat backend/app/models/*.py
```

---

## TO RUN MIGRATIONS
```bash
cd backend
alembic revision --autogenerate -m "add_post_comment_tables"
alembic upgrade head
alembic history    # see all migrations
alembic current    # see current version
```

---

## TO RUN BACKEND
```bash
cd backend
uvicorn app.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

---

## TO ADD PYTHON PACKAGE
```
Add [package] to requirements.txt and run pip install [package].
Update any imports needed.
```

---

## TO ADD FLUTTER PACKAGE
```
Add [package] to pubspec.yaml dependencies section, then run flutter pub get.
```

---

## TO RUN FLUTTER
```bash
cd frontend/parlour_app
flutter pub get
flutter run
flutter run -d chrome  # web
```

---

## IF SOMETHING IS BROKEN
```
Show me the full error. Read the relevant files.
Fix the issue without changing the tech stack or architecture.
Run the fix, confirm it works, then continue.
```

---

## TO COMMIT PROGRESS
```bash
git add .
git commit -m "feat(P1-BK01): add booking service with Redis lock"
```

---

## TO MARK TASKS DONE IN PROGRESS.MD
```
In PROGRESS.md, mark these tasks done with today's date:
- [x] P1-DB01 DONE 2025-01-20
- [x] P1-T01 DONE 2025-01-20
Update the SESSION LOG table at the bottom.
```

---

## END OF SESSION
```
We're done for today.
Update PROGRESS.md:
1. Mark completed tasks as [x] with today's date
2. Add a row to the SESSION LOG table
3. Show me the updated PROGRESS.md so I can save it
```
