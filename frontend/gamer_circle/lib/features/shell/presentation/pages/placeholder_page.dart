import 'package:flutter/material.dart';
import 'package:gamer_circle/features/shell/presentation/widgets/authenticated_scaffold.dart';

class PlaceholderPage extends StatelessWidget {
  final String title;
  final IconData icon;
  final String message;

  const PlaceholderPage({
    super.key,
    required this.title,
    required this.icon,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return AuthenticatedScaffold(
      appBar: AppBar(
        title: Text(title),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1A1A2E),
        elevation: 0,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 56, color: const Color(0xFF7B2FF7)),
            const SizedBox(height: 16),
            Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Color(0xFF1A1A2E),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: const TextStyle(color: Color(0xFF888888)),
            ),
          ],
        ),
      ),
    );
  }
}