import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/friends/providers/friends_provider.dart';
import 'package:gamer_circle/shared/models/friendship.dart';

class FriendRequestsScreen extends ConsumerStatefulWidget {
  const FriendRequestsScreen({super.key});

  @override
  ConsumerState<FriendRequestsScreen> createState() => _FriendRequestsScreenState();
}

class _FriendRequestsScreenState extends ConsumerState<FriendRequestsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  List<FriendRequest> _sent = [];
  bool _loadingSent = true;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _loadSent();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _loadSent() async {
    try {
      _sent = await ref.read(friendsRepositoryProvider).getSentRequests();
    } finally {
      if (mounted) setState(() => _loadingSent = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final incoming = ref.watch(friendRequestsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Friend Requests'),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(text: 'Received'),
            Tab(text: 'Sent'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add_outlined),
            onPressed: () => context.push('/find-friends'),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabs,
        children: [
          incoming.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('Error: $e')),
            data: (requests) {
              if (requests.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('No pending friend requests'),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: () => context.push('/find-friends'),
                        child: const Text('Find Friends'),
                      ),
                    ],
                  ),
                );
              }
              return ListView.builder(
                itemCount: requests.length,
                itemBuilder: (_, i) {
                  final req = requests[i];
                  return ListTile(
                    leading: CircleAvatar(
                      child: Text((req.sender.name ?? '?')[0].toUpperCase()),
                    ),
                    title: Text(req.sender.name ?? req.sender.username ?? 'User'),
                    subtitle: req.sender.username != null
                        ? Text('@${req.sender.username}')
                        : null,
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextButton(
                          onPressed: () =>
                              ref.read(friendRequestsProvider.notifier).decline(req.id),
                          child: const Text('Decline'),
                        ),
                        FilledButton(
                          onPressed: () =>
                              ref.read(friendRequestsProvider.notifier).accept(req.id),
                          child: const Text('Accept'),
                        ),
                      ],
                    ),
                  );
                },
              );
            },
          ),
          _loadingSent
              ? const Center(child: CircularProgressIndicator())
              : _sent.isEmpty
                  ? const Center(child: Text('No sent requests'))
                  : ListView.builder(
                      itemCount: _sent.length,
                      itemBuilder: (_, i) {
                        final req = _sent[i];
                        return ListTile(
                          leading: CircleAvatar(
                            child: Text((req.sender.name ?? '?')[0].toUpperCase()),
                          ),
                          title: Text(req.sender.name ?? req.sender.username ?? 'User'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Chip(label: Text('Pending')),
                              TextButton(
                                onPressed: () async {
                                  await ref
                                      .read(friendsRepositoryProvider)
                                      .cancelRequest(req.id);
                                  await _loadSent();
                                },
                                child: const Text('Cancel'),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
        ],
      ),
    );
  }
}