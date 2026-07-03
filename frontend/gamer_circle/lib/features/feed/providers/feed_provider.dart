import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/data/demo_data_loader.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/post.dart';
import 'package:gamer_circle/shared/models/tournament.dart';

sealed class FeedItem {
  const FeedItem();
}

class FeedPostItem extends FeedItem {
  const FeedPostItem(this.post);
  final Post post;
}

class FeedTournamentItem extends FeedItem {
  const FeedTournamentItem(this.tournament);
  final Tournament tournament;
}

class FeedState {
  const FeedState({
    this.items = const [],
    this.page = 1,
    this.isLoading = false,
    this.hasMore = true,
    this.newPostsBanner = 0,
    this.error,
  });

  final List<FeedItem> items;
  final int page;
  final bool isLoading;
  final bool hasMore;
  final int newPostsBanner;
  final String? error;

  FeedState copyWith({
    List<FeedItem>? items,
    int? page,
    bool? isLoading,
    bool? hasMore,
    int? newPostsBanner,
    String? error,
  }) =>
      FeedState(
        items: items ?? this.items,
        page: page ?? this.page,
        isLoading: isLoading ?? this.isLoading,
        hasMore: hasMore ?? this.hasMore,
        newPostsBanner: newPostsBanner ?? this.newPostsBanner,
        error: error,
      );
}

class FeedNotifier extends StateNotifier<FeedState> {
  FeedNotifier(this._api) : super(const FeedState());

  final dynamic _api;

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading) return;
    final page = refresh ? 1 : state.page;
    state = state.copyWith(isLoading: true, error: null);
    try {
      var raw = await _api.fetchFeed(page: page);
      if (raw.isEmpty && page == 1) {
        raw = await DemoDataLoader.loadFeedItems();
      }
      final parsed = raw.map<FeedItem>((item) {
        final map = item as Map<String, dynamic>;
        final type = map['type'] as String;
        final data = map['data'] as Map<String, dynamic>;
        if (type == 'tournament_announcement') {
          return FeedTournamentItem(Tournament.fromJson(data));
        }
        return FeedPostItem(Post.fromJson(data));
      }).toList();

      state = state.copyWith(
        items: refresh ? parsed : [...state.items, ...parsed],
        page: page + 1,
        hasMore: parsed.length >= 20,
        isLoading: false,
        newPostsBanner: refresh ? 0 : state.newPostsBanner,
      );
    } catch (e) {
      if (page == 1) {
        try {
          final raw = await DemoDataLoader.loadFeedItems();
          final parsed = raw.map<FeedItem>((item) {
            final map = item as Map<String, dynamic>;
            final type = map['type'] as String;
            final data = map['data'] as Map<String, dynamic>;
            if (type == 'tournament_announcement') {
              return FeedTournamentItem(Tournament.fromJson(data));
            }
            return FeedPostItem(Post.fromJson(data));
          }).toList();
          state = state.copyWith(
            items: parsed,
            page: 2,
            hasMore: false,
            isLoading: false,
          );
          return;
        } catch (_) {}
      }
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void addPostToTop(Post post) {
    state = state.copyWith(
      items: [FeedPostItem(post), ...state.items],
      newPostsBanner: state.newPostsBanner + 1,
    );
  }

  void dismissNewPostsBanner() {
    state = state.copyWith(newPostsBanner: 0);
  }

  void updatePostLike(String postId, bool liked, int likesCount) {
    state = state.copyWith(
      items: state.items.map((item) {
        if (item is FeedPostItem && item.post.id == postId) {
          return FeedPostItem(item.post.copyWith(isLiked: liked, likesCount: likesCount));
        }
        return item;
      }).toList(),
    );
  }
}

final feedProvider = StateNotifierProvider<FeedNotifier, FeedState>((ref) {
  return FeedNotifier(ref.watch(socialApiProvider));
});