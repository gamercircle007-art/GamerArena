import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:gamer_circle/main.dart' as app;
import 'package:gamer_circle/features/shell/presentation/widgets/main_shell_scaffold.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Profile tab and navbar icon exist and are navigable', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 5));

    // Check for bottom navbar with PROFILE
    expect(find.byType(MainShellScaffold), findsOneWidget);
    expect(find.text('PROFILE'), findsOneWidget);  // from the added icon

    // Tap PROFILE
    await tester.tap(find.text('PROFILE'));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Should navigate to profile screen
    expect(find.textContaining('My Profile'), findsWidgets);
    expect(find.text('Edit Profile'), findsWidgets);
  });
}
