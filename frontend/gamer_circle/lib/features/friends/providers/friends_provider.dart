import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/shared/models/friendship.dart';

class FriendRequestsNotifier extends AsyncNotifier<List<FriendRequest>> {
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  Future<List<FriendRequest>> build() async {
    ref.onDispose(() => _wsSub?.cancel());
    _listenWs();
    return ref.read(friendsRepositoryProvider).getIncomingRequests();
  }

  void _listenWs() {
    _wsSub = WsService.instance.events.listen((event) {
      final type = event['type'] as String?;
      if (type == 'friend_request') {
        ref.invalidateSelf();
      } else if (type == 'friend_accepted') {
        ref.invalidate(friendsProvider);
      }
    });
  }

  Future<void> accept(String id) async {
    await ref.read(friendsRepositoryProvider).acceptRequest(id);
    state = AsyncData(
      (state.valueOrNull ?? []).where((r) => r.id != id).toList(),
    );
    ref.invalidate(friendsProvider);
  }

  Future<void> decline(String id) async {
    await ref.read(friendsRepositoryProvider).declineRequest(id);
    state = AsyncData(
      (state.valueOrNull ?? []).where((r) => r.id != id).toList(),
    );
  }
}

final friendRequestsProvider =
    AsyncNotifierProvider<FriendRequestsNotifier, List<FriendRequest>>(
  FriendRequestsNotifier.new,
);

class FriendsNotifier extends AsyncNotifier<List<Friendship>> {
  @override
  Future<List<Friendship>> build() async {
    return ref.read(friendsRepositoryProvider).getFriends();
  }

  Future<void> unfriend(String userId) async {
    await ref.read(friendsRepositoryProvider).unfriend(userId);
    state = AsyncData(
      (state.valueOrNull ?? []).where((f) => f.user.id != userId).toList(),
    );
  }
}

final friendsProvider =
    AsyncNotifierProvider<FriendsNotifier, List<Friendship>>(
  FriendsNotifier.new,
);

final friendSuggestionsProvider = FutureProvider<List<FriendSuggestion>>((ref) {
  return ref.read(friendsRepositoryProvider).getSuggestions();
});

final pendingRequestsCountProvider = Provider<int>((ref) {
  return ref.watch(friendRequestsProvider).valueOrNull?.length ?? 0;
});