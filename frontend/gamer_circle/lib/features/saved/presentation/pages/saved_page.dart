import 'package:flutter/material.dart';
import 'package:gamer_circle/features/shell/presentation/widgets/authenticated_scaffold.dart';

class SavedPage extends StatelessWidget {
  const SavedPage({super.key});

  @override
  Widget build(BuildContext context) {
    return AuthenticatedScaffold(
      appBar: AppBar(
        title: const Text('Saved'),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF1A1A2E),
        elevation: 0,
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.bookmark_outline, size: 56, color: Color(0xFF7B2FF7)),
            SizedBox(height: 16),
            Text(
              'No saved items yet',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Color(0xFF1A1A2E),
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Sessions and posts you save will appear here',
              style: TextStyle(color: Color(0xFF888888)),
            ),
          ],
        ),
      ),
    );
  }
}