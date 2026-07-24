import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/feed/data/interaction_repository.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

/// rankedFeedProvider(feedType) - FamilyAsyncNotifier per ALG-FL03
class RankedFeedNotifier extends FamilyAsyncNotifier<Map<String, dynamic>, String> {
  late final InteractionRepository _repo;
  int _page = 1;
  final List<Map<String, dynamic>> _items = [];
  bool _hasMore = true;

  @override
  Future<Map<String, dynamic>> build(String arg) async {
    final feedType = arg;
    _repo = InteractionRepository(ref.watch(dioProvider));
    _page = 1;
    _items.clear();
    _hasMore = true;
    return _loadPage(feedType);
  }

  Future<Map<String, dynamic>> _loadPage(String feedType) async {
    final data = await _repo.getRankedFeed(feedType: feedType, page: _page);
    final newItems = (data['items'] as List? ?? []).cast<Map<String, dynamic>>();
    _items.addAll(newItems);
    _hasMore = newItems.length >= 20;
    return {'items': _items, 'page': _page, 'personalized': data['personalized'] ?? false, 'hasMore': _hasMore};
  }

  Future<void> loadMore(String feedType) async {
    if (!_hasMore || state.isLoading) return;
    _page += 1;
    state = const AsyncValue.loading();
    try {
      final next = await _loadPage(feedType);
      state = AsyncValue.data(next);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  // Track helpers (call from UI or Trackable)
  Future<void> trackView(String contentId, String contentType, {int? pos, int? dur}) =>
      _repo.track(contentId: contentId, contentType: contentType, action: 'view', positionInFeed: pos, viewDurationMs: dur);

  Future<void> trackDwell(String contentId, String contentType, {int? pos, int? dur}) =>
      _repo.track(contentId: contentId, contentType: contentType, action: 'dwell', positionInFeed: pos, viewDurationMs: dur);

  Future<void> trackSkip(String contentId, String contentType, {int? pos}) =>
      _repo.track(contentId: contentId, contentType: contentType, action: 'skip', positionInFeed: pos);

  Future<void> trackLike(String contentId, String contentType) =>
      _repo.track(contentId: contentId, contentType: contentType, action: 'like');

  Future<void> trackShare(String contentId, String contentType) =>
      _repo.track(contentId: contentId, contentType: contentType, action: 'share');
}

final rankedFeedProvider = AsyncNotifierProvider.family<RankedFeedNotifier, Map<String, dynamic>, String>(
  RankedFeedNotifier.new,
);
