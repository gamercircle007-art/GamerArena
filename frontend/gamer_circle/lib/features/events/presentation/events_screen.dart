import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/social_api_paths.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';

class EventsScreen extends ConsumerStatefulWidget {
  const EventsScreen({super.key});

  @override
  ConsumerState<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends ConsumerState<EventsScreen> {
  List<dynamic> _events = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      var pos = ref.read(currentPositionProvider).valueOrNull;
      pos ??= await ref.read(currentPositionProvider.notifier).requestAndFetch();
      if (pos == null) {
        setState(() => _events = []);
        return;
      }
      final dio = ref.read(dioProvider);
      final res = await dio.get(
        SocialApiPaths.nearbyTournaments,
        queryParameters: {'lat': pos.latitude, 'lng': pos.longitude, 'radius': 20000},
      );
      setState(() => _events = res.data as List<dynamic>);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Events'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _events.isEmpty
              ? const Center(child: Text('No upcoming tournaments nearby'))
              : ListView.builder(
                  itemCount: _events.length,
                  itemBuilder: (context, i) {
                    final e = _events[i] as Map<String, dynamic>;
                    return ListTile(
                      leading: const Icon(Icons.event, color: AppColors.primary),
                      title: Text(e['title'] as String),
                      subtitle: Text(
                        '${e['parlor_name']} · ${(e['distance_meters'] as num).round()}m away',
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/tournaments/${e['id']}'),
                    );
                  },
                ),
    );
  }
}