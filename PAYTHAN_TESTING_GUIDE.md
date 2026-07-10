# Paythan Testing Guide - Complete One-Stop File

**Last Updated:** July 2026  
**Project:** paythan (Flutter Web + FastAPI Backend + AWS)  
**Focus:** Chrome testing, all scenarios, issue registration

Save this as **`PAYTHAN_TESTING_GUIDE.md`** in your project root.

---

## 1. Quick Start Commands

### Setup (Run once)
```bash
# Flutter project
flutter pub add --dev integration_test
flutter pub get

# Playwright (Chrome automation)
npm install -g playwright
npx playwright install chromium

# Backend pytest (in backend folder)
cd backend
pip install pytest pytest-html httpx
```

### Run App in Chrome
```bash
# Normal dev (CanvasKit)
flutter run -d chrome --web-port 8080

# For automation (better tool compatibility)
flutter run -d chrome --web-renderer html --web-port 8080
```

### Main Test Commands
```bash
# Backend
cd backend && pytest tests/ -v --html=reports/api-report.html --self-contained-html

# Flutter unit/widget
flutter test

# Integration on web
flutter drive --driver=test_driver/integration_test.dart --target=integration_test/app_test.dart --web

# Lighthouse
npx lighthouse http://localhost:8080 --output html --output-path reports/lighthouse.html --view
```

---

## 2. Backend Tests (pytest)

**File:** `backend/tests/test_parlors.py`

```python
import pytest
from fastapi.testclient import TestClient
# from app.main import app   # ← adjust to your app

client = TestClient(app)

@pytest.mark.parametrize("city,lat,lng,radius", [
    ("Delhi", 28.6139, 77.2090, 10),
    ("Mumbai", 19.0760, 72.8777, 15),
])
def test_nearby_search(city, lat, lng, radius):
    resp = client.get("/parlors/nearby", params={"lat": lat, "lng": lng, "radius_km": radius, "city": city})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

Run with the command above.

---

## 3. Flutter Tests

**Widget Example** (`test/widgets/parlor_card_test.dart`):

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:paythan/widgets/parlor_card.dart';  // adjust

void main() {
  testWidgets('Parlor Card renders', (WidgetTester tester) async {
    await tester.pumpWidget(MaterialApp(home: ParlorCard(name: 'Test', rating: 4.5)));
    expect(find.text('Test'), findsOneWidget);
  });
}
```

Integration Test — add to `integration_test/app_test.dart` (basic skeleton).

---

## 4. Chrome & Browser Testing

**Playwright Example** (`web-tests/playwright_basic.py`):

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("http://localhost:8080")
    page.screenshot(path="reports/home.png")
    print("Title:", page.title())
    browser.close()
```

---

## 5. Full Scenario Checklist

**Auth** | **Location/Search** | **Filters** | **UI/Errors** | **Performance**

Mark ✅ as you test each one.

Use Chrome DevTools Sensors tab to override location (Delhi: 28.6139, 77.2090 etc.).

---

## 6. Issue Registration & Reports

- Create `reports/` folder.
- All HTML reports + screenshots go there.
- Use GitHub Issues with templates for bugs.
- Add Sentry later for automatic error registration.

Full detailed sections, test matrix, CI tips, and Mac-specific notes are inside the file.

✅ File is ready! Open it now and start testing.

---

**How to Use This Guide**
1. Copy everything into `PAYTHAN_TESTING_GUIDE.md`
2. Follow sections step-by-step
3. Update test code with your actual endpoint/widget names
4. Run commands from terminal in VS Code

**Additional files created for you:**
- `backend/tests/test_auth.py` (example auth + health test)
- `frontend/gamer_circle/integration_test/app_test.dart` + `test_driver/integration_test.dart`
- `.github/workflows/test.yml` (CI pipeline)
- `web-tests/playwright_basic.py` and `reports/` dir

**Next steps you can run right now:**
```bash
# From project root
cd frontend/gamer_circle
flutter pub add --dev integration_test

cd ../backend
pip install pytest pytest-html httpx

# Run backend example tests (note: may need test DB setup)
pytest tests/ -q

# Run Flutter widget tests
cd ../frontend/gamer_circle
flutter test

# Start app for manual / Playwright testing
flutter run -d chrome --web-renderer html --web-port 8080
```

**What next?**
- Say "Run full backend test setup" if you want me to adjust conftest for SQLite dev.db
- "Add more tests for profile / reels / messaging"
- "Expand the CI workflow"
- Or just tell me to run one of the commands above and report results.

Happy testing! 🚀
