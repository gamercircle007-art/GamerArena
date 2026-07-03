import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/parlor.dart';
import 'package:gamer_circle/shared/models/post.dart';
import 'package:gamer_circle/shared/models/tournament.dart';
import 'package:gamer_circle/shared/widgets/tournament_card.dart';
import 'package:gamer_circle/shared/widgets/verified_badge.dart';

class ParlorProfileScreen extends ConsumerStatefulWidget {
  const ParlorProfileScreen({super.key, required this.parlorId});

  final String parlorId;

  @override
  ConsumerState<ParlorProfileScreen> createState() => _ParlorProfileScreenState();
}

class _ParlorProfileScreenState extends ConsumerState<ParlorProfileScreen>
    with SingleTickerProviderStateMixin {
  Parlor? _parlor;
  List<Post> _posts = [];
  List<Tournament> _tournaments = [];
  late final TabController _tabs = TabController(length: 2, vsync: this);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final api = ref.read(socialApiProvider);
    final parlor = await api.fetchParlor(widget.parlorId);
    final posts = await api.fetchParlorPosts(widget.parlorId);
    final tournaments = await api.fetchParlorTournaments(widget.parlorId);
    setState(() {
      _parlor = parlor;
      _posts = posts;
      _tournaments = tournaments;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_parlor == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final p = _parlor!;
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Text(p.name),
            if (p.isVerified) ...[const SizedBox(width: 6), const VerifiedBadge()],
          ],
        ),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [Tab(text: 'Posts'), Tab(text: 'Tournaments')],
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (p.logoUrl != null)
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.network(
                      p.logoUrl!,
                      height: 160,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                    ),
                  ),
                const SizedBox(height: 8),
                Text(p.address ?? '', style: TextStyle(color: Colors.grey.shade600)),
                if (p.rating != null) Text('★ ${p.rating!.toStringAsFixed(1)}'),
                if (p.phone != null) Text(p.phone!),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  children: p.gameTypes.map((g) => Chip(label: Text(g))).toList(),
                ),
                const SizedBox(height: 8),
                Text('${p.followerCount} followers'),
                FilledButton(
                  onPressed: () async {
                    final api = ref.read(socialApiProvider);
                    if (p.isFollowing) {
                      await api.unfollowParlor(p.id);
                    } else {
                      await api.followParlor(p.id);
                    }
                    await _load();
                  },
                  child: Text(p.isFollowing ? 'Unfollow' : 'Follow'),
                ),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabs,
              children: [
                GridView.builder(
                  padding: const EdgeInsets.all(8),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 1.2,
                  ),
                  itemCount: _posts.length,
                  itemBuilder: (_, i) => Card(child: Padding(
                    padding: const EdgeInsets.all(8),
                    child: Text(_posts[i].content, maxLines: 4, overflow: TextOverflow.ellipsis),
                  )),
                ),
                ListView.builder(
                  itemCount: _tournaments.length,
                  itemBuilder: (_, i) => TournamentCard(
                    tournament: _tournaments[i],
                    onTap: () {},
                    onBook: () {},
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}