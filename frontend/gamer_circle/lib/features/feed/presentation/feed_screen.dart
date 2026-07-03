import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/feed/providers/feed_provider.dart';
import 'package:gamer_circle/features/stories/presentation/stories_rail.dart';
import 'package:gamer_circle/shared/models/post.dart';
import 'package:gamer_circle/shared/widgets/loading_shimmer.dart';
import 'package:gamer_circle/shared/widgets/social_top_bar.dart';
import 'package:gamer_circle/shared/widgets/post_card.dart';
import 'package:gamer_circle/shared/widgets/tournament_card.dart';

class FeedScreen extends ConsumerStatefulWidget {
  const FeedScreen({super.key});

  @override
  ConsumerState<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends ConsumerState<FeedScreen> {
  final _scrollController = ScrollController();
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(feedProvider.notifier).load(refresh: true));
    _scrollController.addListener(_onScroll);
    _wsSub = WsService.instance.events.listen((event) {
      if (event['event'] == 'new_post') {
        final payload = event['payload'];
        if (payload is Map<String, dynamic>) {
          ref.read(feedProvider.notifier).addPostToTop(Post.fromJson(payload));
        }
      }
    });
  }

  void _onScroll() {
    if (_scrollController.position.pixels >
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(feedProvider.notifier).load();
    }
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final feed = ref.watch(feedProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gamer Feed'),
        actions: const [SocialTopBarActions()],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(feedProvider.notifier).load(refresh: true),
        child: Column(
          children: [
            const StoriesRail(),
            if (feed.newPostsBanner > 0)
              MaterialBanner(
                content: Text('${feed.newPostsBanner} new posts ↑'),
                actions: [
                  TextButton(
                    onPressed: () {
                      ref.read(feedProvider.notifier).dismissNewPostsBanner();
                      ref.read(feedProvider.notifier).load(refresh: true);
                    },
                    child: const Text('VIEW'),
                  ),
                ],
              ),
            Expanded(
              child: feed.items.isEmpty && feed.isLoading
                  ? ListView(children: const [PostCardShimmer(), TournamentCardShimmer()])
                  : ListView.builder(
                      controller: _scrollController,
                      itemCount: feed.items.length + (feed.isLoading ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index >= feed.items.length) {
                          return const Padding(
                            padding: EdgeInsets.all(16),
                            child: Center(child: CircularProgressIndicator()),
                          );
                        }
                        final item = feed.items[index];
                        if (item is FeedPostItem) {
                          final post = item.post;
                          return PostCard(
                            post: post,
                            onLike: () async {
                              final api = ref.read(socialApiProvider);
                              final liked = !post.isLiked;
                              ref.read(feedProvider.notifier).updatePostLike(
                                    post.id,
                                    liked,
                                    post.likesCount + (liked ? 1 : -1),
                                  );
                              if (liked) {
                                await api.like('post', post.id);
                              } else {
                                await api.unlike('post', post.id);
                              }
                            },
                            onComment: () => context.push('/posts/${post.id}/comments'),
                          );
                        }
                        if (item is FeedTournamentItem) {
                          final t = item.tournament;
                          return TournamentCard(
                            tournament: t,
                            onTap: () => context.push('/tournaments/${t.id}'),
                            onBook: () => context.push('/tournaments/${t.id}'),
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}