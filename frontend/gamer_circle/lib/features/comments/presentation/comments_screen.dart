import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/features/comments/providers/comments_provider.dart';
import 'package:gamer_circle/shared/models/comment.dart';
import 'package:gamer_circle/shared/widgets/comment_tile.dart';

class CommentsScreen extends ConsumerStatefulWidget {
  const CommentsScreen({super.key, required this.postId});

  final String postId;

  @override
  ConsumerState<CommentsScreen> createState() => _CommentsScreenState();
}

class _CommentsScreenState extends ConsumerState<CommentsScreen> {
  final _controller = TextEditingController();
  String? _replyParentId;
  String? _replyUsername;
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  void initState() {
    super.initState();
    final channel = 'post:comments:${widget.postId}';
    WsService.instance.subscribe(channel);
    _wsSub = WsService.instance.events.listen((event) {
      if (event['event'] == 'new_comment') {
        final payload = event['payload'];
        if (payload is Map<String, dynamic>) {
          ref
              .read(commentsProvider(widget.postId).notifier)
              .appendComment(Comment.fromJson(payload));
        }
      }
    });
  }

  @override
  void dispose() {
    WsService.instance.unsubscribe('post:comments:${widget.postId}');
    _wsSub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(commentsProvider(widget.postId));

    return Scaffold(
      appBar: AppBar(title: const Text('Comments')),
      body: Column(
        children: [
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: state.comments.length,
                    itemBuilder: (context, index) {
                      final c = state.comments[index];
                      return CommentTile(
                        comment: c,
                        indent: c.parentId != null ? 24 : 0,
                        onLike: () => ref
                            .read(commentsProvider(widget.postId).notifier)
                            .toggleLike(c.id),
                        onReply: () => setState(() {
                          _replyParentId = c.id;
                          _replyUsername = c.user.name;
                        }),
                      );
                    },
                  ),
          ),
          if (_replyUsername != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  Chip(label: Text('Replying to @$_replyUsername')),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => setState(() {
                      _replyParentId = null;
                      _replyUsername = null;
                    }),
                  ),
                ],
              ),
            ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(hintText: 'Add a comment...'),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.send),
                    onPressed: () async {
                      final text = _controller.text.trim();
                      if (text.isEmpty) return;
                      await ref
                          .read(commentsProvider(widget.postId).notifier)
                          .addCommentOptimistic(text, parentId: _replyParentId);
                      _controller.clear();
                      setState(() {
                        _replyParentId = null;
                        _replyUsername = null;
                      });
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}