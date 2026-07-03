class ReelApiPaths {
  ReelApiPaths._();

  static const String feed = '/reels/feed';
  static const String search = '/reels/search';
  static const String reels = '/reels';
  static String reel(String id) => '/reels/$id';
  static String reelView(String id) => '/reels/$id/view';
  static String reelLike(String id) => '/reels/$id/like';
  static String reelBookmark(String id) => '/reels/$id/bookmark';
  static String reelShare(String id) => '/reels/$id/share';
  static String reelReport(String id) => '/reels/$id/report';
  static String reelComments(String id) => '/reels/$id/comments';
  static String commentReplies(String id) => '/reels/reel-comments/$id/replies';
  static String commentLike(String id) => '/reels/reel-comments/$id/like';
  static String deleteComment(String id) => '/reels/reel-comments/$id';
  static String followUser(String id) => '/reels/users/$id/follow';
  static const String demoMusic = '/reels/music/demo';
}