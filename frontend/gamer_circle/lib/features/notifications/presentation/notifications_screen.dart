import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/notification_badge_provider.dart';
import 'package:gamer_circle/shared/models/notification.dart';
import 'package:intl/intl.dart';

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  List<AppNotification> _items = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final items = await ref.read(socialApiProvider).fetchNotifications();
    setState(() => _items = items);
    ref.read(unreadNotificationCountProvider.notifier).reset();
  }

  void _openNotification(AppNotification n) {
    ref.read(socialApiProvider).markRead(n.id);
    final data = n.data;
    if (data == null) return;
    final tournamentId = data['tournament_id'] as String?;
    final postId = data['post_id'] as String?;
    final parlorId = data['parlor_id'] as String?;
    if (tournamentId != null) {
      context.push('/tournaments/$tournamentId');
    } else if (postId != null) {
      context.push('/posts/$postId/comments');
    } else if (parlorId != null) {
      context.push('/parlors/$parlorId');
    }
  }

  String _group(AppNotification n) {
    final now = DateTime.now();
    final d = DateTime(n.createdAt.year, n.createdAt.month, n.createdAt.day);
    final today = DateTime(now.year, now.month, now.day);
    if (d == today) return 'Today';
    if (d == today.subtract(const Duration(days: 1))) return 'Yesterday';
    return 'Older';
  }

  @override
  Widget build(BuildContext context) {
    final groups = <String, List<AppNotification>>{};
    for (final n in _items) {
      groups.putIfAbsent(_group(n), () => []).add(n);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: ListView(
        children: groups.entries.expand((entry) sync* {
          yield Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text(entry.key, style: const TextStyle(fontWeight: FontWeight.bold)),
          );
          for (final n in entry.value) {
            yield Dismissible(
              key: ValueKey(n.id),
              direction: DismissDirection.endToStart,
              onDismissed: (_) => ref.read(socialApiProvider).markRead(n.id),
              child: ListTile(
                leading: Icon(_iconFor(n.type)),
                title: Text(n.title),
                subtitle: Text(n.body),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(DateFormat('h:mm a').format(n.createdAt),
                        style: const TextStyle(fontSize: 12)),
                    if (!n.isRead)
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                      ),
                  ],
                ),
                onTap: () => _openNotification(n),
              ),
            );
          }
        }).toList(),
      ),
    );
  }

  IconData _iconFor(String type) {
    switch (type) {
      case 'booking_confirmed':
        return Icons.event_available;
      case 'new_post':
        return Icons.article;
      default:
        return Icons.notifications;
    }
  }
}