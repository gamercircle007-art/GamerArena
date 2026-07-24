import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

class CommunitiesScreen extends ConsumerStatefulWidget {
  const CommunitiesScreen({super.key});

  @override
  ConsumerState<CommunitiesScreen> createState() => _CommunitiesScreenState();
}

class _CommunitiesScreenState extends ConsumerState<CommunitiesScreen> {
  List<String> _following = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final parlors = await ref.read(socialApiProvider).fetchFollowing();
      setState(() => _following = parlors.map((p) => p.name).toList());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Communities')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _following.isEmpty
              ? const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text(
                      'Follow gaming parlors from Discover to build your community feed.',
                      textAlign: TextAlign.center,
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text(
                      'Parlors you follow',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    ..._following.map(
                      (name) => Card(
                        child: ListTile(
                          leading: const Icon(Icons.groups, color: AppColors.primary),
                          title: Text(name),
                          subtitle: const Text('Member'),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }
}