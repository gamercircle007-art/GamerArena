import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/notification_badge_provider.dart';
import 'package:gamer_circle/features/friends/providers/friends_provider.dart';
import 'package:gamer_circle/shared/widgets/online_dot.dart';

/// Reusable top actions: online pulse, friend requests, notifications.
class SocialTopBarActions extends ConsumerWidget {
  const SocialTopBarActions({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifCount = ref.watch(unreadNotificationCountProvider);
    final friendReqCount = ref.watch(pendingRequestsCountProvider);

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Padding(
          padding: EdgeInsets.only(right: 4),
          child: OnlineDot(isOnline: true, size: OnlineDotSize.small),
        ),
        IconButton(
          icon: Badge(
            isLabelVisible: friendReqCount > 0,
            label: Text('$friendReqCount'),
            child: const Icon(Icons.person_add_outlined),
          ),
          onPressed: () => context.push('/friend-requests'),
        ),
        IconButton(
          icon: Badge(
            isLabelVisible: notifCount > 0,
            label: Text('$notifCount'),
            child: const Icon(Icons.notifications_outlined),
          ),
          onPressed: () => context.push('/notifications'),
        ),
      ],
    );
  }
}