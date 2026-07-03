import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/reel.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';

class ReelCommentsScreen extends ConsumerStatefulWidget {
  const ReelCommentsScreen({super.key, required this.reelId});

  final String reelId;

  @override
  ConsumerState<ReelCommentsScreen> createState() => _ReelCommentsScreenState();
}

class _ReelCommentsScreenState extends ConsumerState<ReelCommentsScreen> {
  final _controller = TextEditingController();
  List<ReelComment> _comments = [];
  bool _loading = true;
  String? _replyToId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final items = await ref.read(reelApiProvider).fetchComments(widget.reelId);
      setState(() => _comments = items);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _submit() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    final comment = await ref.read(reelApiProvider).postComment(
          widget.reelId,
          text,
          parentId: _replyToId,
        );
    setState(() {
      if (_replyToId == null) {
        _comments = [comment, ..._comments];
      }
      _controller.clear();
      _replyToId = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Comments')),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _comments.isEmpty
                    ? const Center(child: Text('Be the first to comment'))
                    : ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _comments.length,
                        separatorBuilder: (_, __) => const Divider(height: 20),
                        itemBuilder: (context, i) {
                          final c = _comments[i];
                          return _CommentTile(
                            comment: c,
                            onReply: () => setState(() => _replyToId = c.id),
                            onLike: () async {
                              if (c.isLiked) {
                                await ref.read(reelApiProvider).unlikeComment(c.id);
                              } else {
                                await ref.read(reelApiProvider).likeComment(c.id);
                              }
                              await _load();
                            },
                          );
                        },
                      ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: InputDecoration(
                        hintText: _replyToId != null ? 'Write a reply…' : 'Add a comment…',
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(onPressed: _submit, icon: const Icon(Icons.send)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CommentTile extends StatelessWidget {
  const _CommentTile({
    required this.comment,
    required this.onReply,
    required this.onLike,
  });

  final ReelComment comment;
  final VoidCallback onReply;
  final VoidCallback onLike;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        UserAvatar(name: comment.user.displayName, imageUrl: comment.user.avatarUrl, radius: 16),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(comment.user.displayName, style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text(comment.content),
              const SizedBox(height: 6),
              Row(
                children: [
                  Text('${comment.likesCount} likes', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  const SizedBox(width: 12),
                  GestureDetector(onTap: onReply, child: const Text('Reply', style: TextStyle(fontSize: 12))),
                  if (comment.replyCount > 0) ...[
                    const SizedBox(width: 12),
                    Text('${comment.replyCount} replies', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ],
              ),
            ],
          ),
        ),
        IconButton(
          icon: Icon(comment.isLiked ? Icons.favorite : Icons.favorite_border, size: 18),
          onPressed: onLike,
        ),
      ],
    );
  }
}