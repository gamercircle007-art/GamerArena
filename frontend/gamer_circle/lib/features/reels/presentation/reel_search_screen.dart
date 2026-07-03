import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/reel.dart';
import 'package:cached_network_image/cached_network_image.dart';

class ReelSearchScreen extends ConsumerStatefulWidget {
  const ReelSearchScreen({super.key});

  @override
  ConsumerState<ReelSearchScreen> createState() => _ReelSearchScreenState();
}

class _ReelSearchScreenState extends ConsumerState<ReelSearchScreen> {
  final _query = TextEditingController();
  List<Reel> _results = [];
  bool _loading = false;
  String _sort = 'trending';

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final q = _query.text.trim();
    if (q.isEmpty) return;
    setState(() => _loading = true);
    try {
      final page = await ref.read(reelApiProvider).searchReels(q: q, sort: _sort);
      setState(() => _results = page.items);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Search Reels')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _query,
                    decoration: const InputDecoration(
                      hintText: 'Username, caption, hashtag, location…',
                      prefixIcon: Icon(Icons.search),
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(onPressed: _search, icon: const Icon(Icons.search)),
              ],
            ),
          ),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                ChoiceChip(
                  label: const Text('Trending'),
                  selected: _sort == 'trending',
                  onSelected: (_) => setState(() => _sort = 'trending'),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Newest'),
                  selected: _sort == 'newest',
                  onSelected: (_) => setState(() => _sort = 'newest'),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Popular'),
                  selected: _sort == 'popular',
                  onSelected: (_) => setState(() => _sort = 'popular'),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _results.isEmpty
                    ? const Center(child: Text('Search for reels'))
                    : GridView.builder(
                        padding: const EdgeInsets.all(12),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          mainAxisSpacing: 8,
                          crossAxisSpacing: 8,
                          childAspectRatio: 9 / 16,
                        ),
                        itemCount: _results.length,
                        itemBuilder: (context, i) {
                          final reel = _results[i];
                          return ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                if (reel.thumbnailUrl != null)
                                  CachedNetworkImage(
                                    imageUrl: reel.thumbnailUrl!,
                                    fit: BoxFit.cover,
                                  )
                                else
                                  const ColoredBox(color: Colors.black12),
                                Positioned(
                                  left: 8,
                                  bottom: 8,
                                  right: 8,
                                  child: Text(
                                    reel.caption ?? reel.user.displayName,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      shadows: [Shadow(color: Colors.black, blurRadius: 4)],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}