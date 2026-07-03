import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/shared/models/story.dart';

class StoriesFeedNotifier extends AsyncNotifier<List<StoryGroup>> {
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  Future<List<StoryGroup>> build() async {
    ref.onDispose(() => _wsSub?.cancel());
    _listenWs();
    return ref.read(storiesRepositoryProvider).getFeed();
  }

  void _listenWs() {
    _wsSub = WsService.instance.events.listen((event) {
      if (event['type'] == 'new_story') {
        ref.invalidateSelf();
      }
    });
  }

  Future<void> markViewed(String storyId) async {
    await ref.read(storiesRepositoryProvider).markViewed(storyId);
    await refresh();
  }

  Future<void> refresh() async {
    state = AsyncData(await ref.read(storiesRepositoryProvider).getFeed());
  }
}

final storiesFeedProvider =
    AsyncNotifierProvider<StoriesFeedNotifier, List<StoryGroup>>(
  StoriesFeedNotifier.new,
);

final currentStoryIndexProvider = StateProvider.family<int, int>((ref, _) => 0);

final myStoriesProvider = FutureProvider<List<Story>>((ref) async {
  final auth = ref.watch(authNotifierProvider);
  if (auth is! AuthAuthenticated) return [];
  return ref.read(storiesRepositoryProvider).getUserStories(auth.user.id);
});