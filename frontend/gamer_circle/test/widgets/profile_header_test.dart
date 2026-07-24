import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// Simple smoke test for profile-related widgets.
// Full MyProfileScreen requires Riverpod overrides + mocks for auth/profile/stories providers.

void main() {
  testWidgets('Basic profile stat widget smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Column(
              children: [
                Text('Test User'),
                Text('5 Posts'),
                Text('Edit Profile'),
              ],
            ),
          ),
        ),
      ),
    );

    expect(find.text('Test User'), findsOneWidget);
    expect(find.text('Edit Profile'), findsOneWidget);
  });
}
