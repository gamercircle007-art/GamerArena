import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Legacy placeholder feed page (not used by primary `/feed` route).
/// Kept for parity with older nav tests; routes to real shell destinations.
class FeedPage extends StatelessWidget {
  const FeedPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gamer Feed')),
      body: const Center(
        child: Text(
          'Enterprise Social Feed\n(Implement with Riverpod + Clean Arch)',
          textAlign: TextAlign.center,
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 0,
        onTap: (i) {
          switch (i) {
            case 0:
              context.go('/feed');
            case 1:
              context.go('/communities');
            case 2:
              context.go('/profile');
          }
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Feed'),
          BottomNavigationBarItem(icon: Icon(Icons.group), label: 'Circles'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
