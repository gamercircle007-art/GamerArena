import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/data/social_remote_datasource.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/comment.dart';

class CommentsState {
  const CommentsState({this.comments = const [], this.isLoading = false, this.error});

  final List<Comment> comments;
  final bool isLoading;
  final String? error;

  CommentsState copyWith({List<Comment>? comments, bool? isLoading, String? error}) =>
      CommentsState(
        comments: comments ?? this.comments,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class CommentsNotifier extends StateNotifier<CommentsState> {
  CommentsNotifier(this._api, this.postId) : super(const CommentsState(isLoading: true)) {
    loadComments();
  }

  final SocialRemoteDataSource _api;
  final String postId;

  Future<void> loadComments() async {
    state = state.copyWith(isLoading: true);
    try {
      final comments = await _api.fetchComments(postId);
      state = CommentsState(comments: comments);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> addCommentOptimistic(String content, {String? parentId}) async {
    final optimistic = Comment(
      id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
      user: const CommentUser(id: 'me', name: 'You'),
      content: content,
      parentId: parentId,
      likesCount: 0,
      isDeleted: false,
      createdAt: DateTime.now(),
    );
    state = state.copyWith(comments: [...state.comments, optimistic]);
    try {
      final saved = await _api.addComment(postId, content, parentId: parentId);
      state = state.copyWith(
        comments: state.comments
            .map<Comment>((c) => c.id == optimistic.id ? saved : c)
            .toList(),
      );
    } catch (e) {
      state = state.copyWith(
        comments: state.comments.where((c) => c.id != optimistic.id).toList(),
        error: e.toString(),
      );
    }
  }

  void appendComment(Comment comment) {
    if (state.comments.any((c) => c.id == comment.id)) return;
    state = state.copyWith(comments: [...state.comments, comment]);
  }

  Future<void> toggleLike(String commentId) async {
    toggleLikeLocal(commentId);
    try {
      await _api.like('comment', commentId);
    } catch (_) {
      toggleLikeLocal(commentId);
    }
  }

  void toggleLikeLocal(String commentId) {
    state = state.copyWith(
      comments: state.comments.map((c) {
        if (c.id != commentId) return c;
        return c.copyWith(
          isLiked: !c.isLiked,
          likesCount: c.isLiked ? c.likesCount - 1 : c.likesCount + 1,
        );
      }).toList(),
    );
  }
}

final commentsProvider =
    StateNotifierProvider.family<CommentsNotifier, CommentsState, String>(
  (ref, postId) => CommentsNotifier(ref.watch(socialApiProvider), postId),
);