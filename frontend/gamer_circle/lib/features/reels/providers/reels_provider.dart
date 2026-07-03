import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/reel.dart';

class ReelsState {
  const ReelsState({
    this.reels = const [],
    this.page = 1,
    this.hasMore = true,
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.currentIndex = 0,
  });

  final List<Reel> reels;
  final int page;
  final bool hasMore;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final int currentIndex;

  ReelsState copyWith({
    List<Reel>? reels,
    int? page,
    bool? hasMore,
    bool? isLoading,
    bool? isLoadingMore,
    String? error,
    int? currentIndex,
    bool clearError = false,
  }) {
    return ReelsState(
      reels: reels ?? this.reels,
      page: page ?? this.page,
      hasMore: hasMore ?? this.hasMore,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      error: clearError ? null : (error ?? this.error),
      currentIndex: currentIndex ?? this.currentIndex,
    );
  }
}

final reelsProvider = NotifierProvider<ReelsNotifier, ReelsState>(ReelsNotifier.new);

class ReelsNotifier extends Notifier<ReelsState> {
  @override
  ReelsState build() => const ReelsState();

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading) return;
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final page = await ref.read(reelApiProvider).fetchFeed(page: 1);
      state = state.copyWith(
        reels: page.items,
        page: 1,
        hasMore: page.hasMore,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true);
    try {
      final nextPage = state.page + 1;
      final page = await ref.read(reelApiProvider).fetchFeed(page: nextPage);
      state = state.copyWith(
        reels: [...state.reels, ...page.items],
        page: nextPage,
        hasMore: page.hasMore,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: e.toString());
    }
  }

  void setCurrentIndex(int index) {
    state = state.copyWith(currentIndex: index);
    if (index >= state.reels.length - 2) loadMore();
  }

  void updateReel(Reel reel) {
    final idx = state.reels.indexWhere((r) => r.id == reel.id);
    if (idx < 0) return;
    final updated = [...state.reels];
    updated[idx] = reel;
    state = state.copyWith(reels: updated);
  }

  Future<void> toggleLike(String reelId) async {
    final idx = state.reels.indexWhere((r) => r.id == reelId);
    if (idx < 0) return;
    final reel = state.reels[idx];
    final api = ref.read(reelApiProvider);
    try {
      final res = reel.isLiked
          ? await api.unlikeReel(reelId)
          : await api.likeReel(reelId);
      updateReel(reel.copyWith(
        isLiked: !reel.isLiked,
        likesCount: res['likes_count'] as int? ?? reel.likesCount,
      ));
    } catch (_) {}
  }

  Future<void> toggleBookmark(String reelId) async {
    final idx = state.reels.indexWhere((r) => r.id == reelId);
    if (idx < 0) return;
    final reel = state.reels[idx];
    try {
      final res = await ref.read(reelApiProvider).bookmarkReel(reelId);
      updateReel(reel.copyWith(
        isBookmarked: res['bookmarked'] as bool? ?? !reel.isBookmarked,
        bookmarksCount: res['bookmarks_count'] as int? ?? reel.bookmarksCount,
      ));
    } catch (_) {}
  }

  Future<void> toggleFollow(String userId) async {
    for (var i = 0; i < state.reels.length; i++) {
      if (state.reels[i].user.id != userId) continue;
      final reel = state.reels[i];
      final api = ref.read(reelApiProvider);
      try {
        final res = reel.user.isFollowing
            ? await api.unfollowUser(userId)
            : await api.followUser(userId);
        updateReel(reel.copyWith(
          user: ReelUser(
            id: reel.user.id,
            username: reel.user.username,
            name: reel.user.name,
            avatarUrl: reel.user.avatarUrl,
            followersCount: res['followers_count'] as int? ?? reel.user.followersCount,
            followingCount: reel.user.followingCount,
            isFollowing: res['following'] as bool? ?? !reel.user.isFollowing,
          ),
        ));
      } catch (_) {}
    }
  }
}