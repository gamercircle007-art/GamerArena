import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/friends/data/friends_repository.dart';
import 'package:gamer_circle/features/messaging/data/messaging_repository.dart';
import 'package:gamer_circle/features/snap_map/data/location_repository.dart';
import 'package:gamer_circle/features/stories/data/stories_repository.dart';

final messagingRepositoryProvider = Provider<MessagingRepository>((ref) {
  return MessagingRepository(ref.watch(dioProvider));
});

final friendsRepositoryProvider = Provider<FriendsRepository>((ref) {
  return FriendsRepository(ref.watch(dioProvider));
});

final storiesRepositoryProvider = Provider<StoriesRepository>((ref) {
  return StoriesRepository(ref.watch(dioProvider));
});

final locationRepositoryProvider = Provider<LocationRepository>((ref) {
  return LocationRepository(ref.watch(dioProvider));
});

final wsServiceProvider = Provider<WsService>((ref) => WsService.instance);

/// Global online status map updated via WebSocket events.
class OnlineStatusNotifier extends Notifier<Map<String, bool>> {
  @override
  Map<String, bool> build() => Map<String, bool>.from(WsService.instance.onlineUsers);

  void setOnline(String userId, bool online) {
    state = {...state, userId: online};
  }
}

final onlineStatusNotifierProvider =
    NotifierProvider<OnlineStatusNotifier, Map<String, bool>>(
  OnlineStatusNotifier.new,
);