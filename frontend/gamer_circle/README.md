# GamerCircle

**Enterprise-grade Flutter application** for a gaming social platform.

This project uses a **Feature-first + Clean Architecture** structure designed to scale as the app grows large.

## Project Structure

```
lib/
├── app/                  # App-level configuration
│   ├── config/           # Environment, flavors
│   ├── di/               # Dependency injection
│   ├── router/           # GoRouter navigation
│   └── theme/            # App-wide theming
├── core/                 # Shared business logic & utilities
│   ├── constants/
│   ├── errors/           # Failures & Exceptions
│   ├── network/          # Dio + interceptors
│   ├── usecases/         # Base UseCase
│   ├── utils/
│   └── widgets/          # Reusable UI components
├── features/             # Independent vertical slices (modules)
│   ├── auth/
│   │   ├── data/
│   │   ├── domain/
│   │   └── presentation/
│   ├── feed/
│   ├── circles/          # Core "Circle" social feature
│   └── profile/
└── main.dart             # Entry points (main_dev.dart for dev)
```

### Why this structure?
- **Separation of concerns**: Data / Domain / Presentation clearly separated per feature.
- **Scalability**: New teams/features can work in isolation.
- **Testability**: Easy to unit test usecases, repositories.
- **Enterprise ready**: DI, routing, theming, networking all centralized.

## Getting Started

```bash
flutter pub get
dart run build_runner build --delete-conflicting-outputs   # For codegen (freezed, riverpod)
flutter run
```

## Architecture Notes

- **State Management**: Riverpod (with code generation)
- **Navigation**: go_router
- **Networking**: Dio
- **Models**: Freezed + json_serializable
- **Architecture**: Clean Architecture (per feature)

## Next Steps Recommendations

1. Add real API endpoints in `core/network`
2. Implement authentication flow
3. Add more features (games, chat, notifications)
4. Set up CI/CD, flavors (dev/prod)
5. Add localization, analytics, crash reporting

This structure is designed for a product that "will go big".
