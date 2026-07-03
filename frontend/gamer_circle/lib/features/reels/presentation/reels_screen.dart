import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/reels/providers/reels_provider.dart';
import 'package:gamer_circle/features/reels/widgets/reel_overlay.dart';
import 'package:gamer_circle/features/reels/widgets/reel_video_player.dart';
import 'package:gamer_circle/shared/models/reel.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shimmer/shimmer.dart';

class ReelsScreen extends ConsumerStatefulWidget {
  const ReelsScreen({super.key});

  @override
  ConsumerState<ReelsScreen> createState() => _ReelsScreenState();
}

class _ReelsScreenState extends ConsumerState<ReelsScreen> {
  late PageController _pageController;
  bool _showHeart = false;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    Future.microtask(() => ref.read(reelsProvider.notifier).load());
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _flashHeart() {
    setState(() => _showHeart = true);
    Future.delayed(const Duration(milliseconds: 800), () {
      if (mounted) setState(() => _showHeart = false);
    });
  }

  Future<void> _shareReel(Reel reel) async {
    try {
      final res = await ref.read(reelApiProvider).shareReel(reel.id);
      final url = res['share_url'] as String? ?? reel.videoUrl;
      await Share.share('Check out this reel on GamerCircle: $url');
    } catch (_) {
      await Share.share(reel.videoUrl);
    }
  }

  void _showMoreMenu(Reel reel) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.flag_outlined),
              title: const Text('Report'),
              onTap: () async {
                Navigator.pop(ctx);
                await ref.read(reelApiProvider).reportReel(reel.id, 'Inappropriate content');
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Report submitted')),
                  );
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.visibility_off_outlined),
              title: const Text('Hide reel'),
              onTap: () => Navigator.pop(ctx),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(reelsProvider);

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Reels', style: TextStyle(fontWeight: FontWeight.w800)),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => context.push('/reels/search'),
          ),
        ],
      ),
      body: state.isLoading
          ? _LoadingSkeleton()
          : state.error != null && state.reels.isEmpty
              ? _ErrorState(message: state.error!, onRetry: () => ref.read(reelsProvider.notifier).load())
              : state.reels.isEmpty
                  ? _EmptyState(onRefresh: () => ref.read(reelsProvider.notifier).load())
                  : PageView.builder(
                      controller: _pageController,
                      scrollDirection: Axis.vertical,
                      itemCount: state.reels.length,
                      onPageChanged: (i) {
                        ref.read(reelsProvider.notifier).setCurrentIndex(i);
                        final reel = state.reels[i];
                        ref.read(reelApiProvider).recordView(reel.id);
                      },
                      itemBuilder: (context, index) {
                        final reel = state.reels[index];
                        final isActive = state.currentIndex == index;
                        return Stack(
                          fit: StackFit.expand,
                          children: [
                            ReelVideoPlayer(
                              videoUrl: reel.videoUrl,
                              isActive: isActive,
                              filterMatrix: filterMatrixForName(reel.filterName),
                              onDoubleTap: () {
                                _flashHeart();
                                if (!reel.isLiked) {
                                  ref.read(reelsProvider.notifier).toggleLike(reel.id);
                                }
                              },
                            ),
                            ReelOverlay(
                              reel: reel,
                              showHeart: _showHeart && isActive,
                              onLike: () => ref.read(reelsProvider.notifier).toggleLike(reel.id),
                              onComment: () => context.push('/reels/${reel.id}/comments'),
                              onShare: () => _shareReel(reel),
                              onBookmark: () => ref.read(reelsProvider.notifier).toggleBookmark(reel.id),
                              onFollow: () => ref.read(reelsProvider.notifier).toggleFollow(reel.user.id),
                              onMore: () => _showMoreMenu(reel),
                            ),
                          ],
                        );
                      },
                    ),
    );
  }
}

class _LoadingSkeleton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: const Color(0xFF1A1A2E),
      highlightColor: const Color(0xFF2D2D44),
      child: Container(color: Colors.black),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onRefresh});
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.play_circle_outline, size: 64, color: Colors.white38),
          const SizedBox(height: 16),
          const Text('No reels yet', style: TextStyle(color: Colors.white70, fontSize: 18)),
          const SizedBox(height: 12),
          FilledButton(onPressed: onRefresh, child: const Text('Refresh')),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}