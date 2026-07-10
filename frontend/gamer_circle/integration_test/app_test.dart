import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:gamer_circle/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('App launches and shows home', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Adjust these finders based on your actual home screen widgets
    expect(find.textContaining('HOME'), findsWidgets); // or search for a parlor card, etc.

    // Example: test location flow would require mocking location or using devtools override
  });
}
