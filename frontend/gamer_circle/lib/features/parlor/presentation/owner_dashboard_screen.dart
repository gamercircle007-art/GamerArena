import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

class OwnerDashboardScreen extends ConsumerStatefulWidget {
  const OwnerDashboardScreen({super.key});

  @override
  ConsumerState<OwnerDashboardScreen> createState() => _OwnerDashboardScreenState();
}

class _OwnerDashboardScreenState extends ConsumerState<OwnerDashboardScreen> {
  Map<String, dynamic>? _analytics;

  @override
  void initState() {
    super.initState();
    Future.microtask(() async {
      final data = await ref.read(socialApiProvider).fetchAnalytics();
      setState(() => _analytics = data);
    });
  }

  @override
  Widget build(BuildContext context) {
    final a = _analytics;
    return Scaffold(
      appBar: AppBar(title: const Text('Owner Dashboard')),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton.small(
            heroTag: 'post',
            onPressed: () => context.push('/create-post'),
            child: const Icon(Icons.post_add),
          ),
          const SizedBox(height: 8),
          FloatingActionButton(
            heroTag: 'tournament',
            onPressed: () => context.push('/create-tournament'),
            child: const Icon(Icons.add),
          ),
        ],
      ),
      body: a == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Row(
                  children: [
                    _StatCard('Followers', '${a['follower_count']}'),
                    _StatCard('Posts', '${a['total_posts']}'),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _StatCard('Upcoming', '${a['upcoming_tournaments_count']}'),
                    _StatCard('Bookings/mo', '${a['total_bookings_this_month']}'),
                  ],
                ),
                const SizedBox(height: 24),
                const Text('Bookings by tournament', style: TextStyle(fontWeight: FontWeight.bold)),
                ...(a['bookings_by_tournament'] as List<dynamic>? ?? []).map(
                  (item) => ListTile(
                    title: Text(item['title'] as String),
                    trailing: Text('${item['bookings_count']}'),
                  ),
                ),
              ],
            ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text(value, style: Theme.of(context).textTheme.headlineSmall),
              Text(label),
            ],
          ),
        ),
      ),
    );
  }
}