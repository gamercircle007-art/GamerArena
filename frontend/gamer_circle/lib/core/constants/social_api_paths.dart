class SocialApiPaths {
  SocialApiPaths._();

  static const String feed = '/feed';
  static const String store = '/store';
  static const String posts = '/posts';
  static String post(String id) => '/posts/$id';
  static String postComments(String postId) => '/posts/$postId/comments';

  static const String tournaments = '/tournaments';
  static String tournament(String id) => '/tournaments/$id';
  static String bookTournament(String id) => '/tournaments/$id/book';

  static const String bookings = '/bookings';
  static String booking(String id) => '/bookings/$id';
  static const String myBookings = '/users/me/bookings';
  static const String myFollowing = '/users/me/following';

  static const String parlors = '/parlors';
  static String parlor(String id) => '/parlors/$id';
  static String parlorPosts(String id) => '/parlors/$id/posts';
  static String parlorTournaments(String id) => '/parlors/$id/tournaments';
  static const String parlorAnalytics = '/parlors/me/analytics';

  static const String follows = '/follows';
  static String unfollow(String parlorId) => '/follows/$parlorId';
  static const String likes = '/likes';
  static String unlike(String type, String id) => '/likes/$type/$id';

  static String commentReplies(String id) => '/comments/$id/replies';
  static String commentLike(String id) => '/comments/$id/like';

  static const String notifications = '/notifications';
  static const String notificationsUnread = '/notifications/unread-count';
  static const String notificationsReadAll = '/notifications/read-all';
  static String notificationRead(String id) => '/notifications/$id/read';

  static const String nearbyParlors = '/geo/nearby-parlors';
  static const String searchParlors = '/geo/search-parlors';
  static const String nearbyTournaments = '/geo/nearby-tournaments';
  static const String search = '/search';
  static const String presignedUrl = '/uploads/presigned-url';

  static String bookingPaymentOrder(String bookingId) =>
      '/payments/razorpay/bookings/$bookingId/order';
  static String bookingPaymentVerify(String bookingId) =>
      '/payments/razorpay/bookings/$bookingId/verify';
  static const String razorpayConfig = '/payments/razorpay/config';
}