class MessagingApiPaths {
  static const conversations = '/conversations';
  static const findOrCreate = '/conversations/find-or-create';

  static String conversation(String id) => '/conversations/$id';
  static String messages(String id) => '/conversations/$id/messages';
  static String messageReact(String convId, String msgId) =>
      '/conversations/$convId/messages/$msgId/react';
  static String messageDelivered(String convId, String msgId) =>
      '/conversations/$convId/messages/$msgId/delivered';
  static String messageViewed(String convId, String msgId) =>
      '/conversations/$convId/messages/$msgId/viewed';
  static String messageDelete(String convId, String msgId) =>
      '/conversations/$convId/messages/$msgId';
  static String media(String id) => '/conversations/$id/media';
}

class FriendsApiPaths {
  static const friends = '/friends';
  static const request = '/friends/request';
  static const requests = '/friends/requests';
  static const requestsSent = '/friends/requests/sent';
  static const suggestions = '/friends/suggestions';

  static String acceptRequest(String id) => '/friends/requests/$id/accept';
  static String declineRequest(String id) => '/friends/requests/$id/decline';
  static String cancelRequest(String id) => '/friends/requests/$id';
  static String unfriend(String userId) => '/friends/$userId';
}

class StoriesApiPaths {
  static const stories = '/stories';
  static const feed = '/stories/feed';

  static String userStories(String userId) => '/stories/user/$userId';
  static String view(String id) => '/stories/$id/view';
  static String viewers(String id) => '/stories/$id/viewers';
  static String delete(String id) => '/stories/$id';
}

class SocialApiPaths {
  static const locationUpdate = '/location/update';
  static const ghostMode = '/location/ghost-mode';
  static const friendsMap = '/location/friends-map';
  static const locationPrivacy = '/location/privacy';
  static const heartbeat = '/users/me/heartbeat';
  static const statusPrivacy = '/users/me/status-privacy';
  static const myProfile = '/users/me';
  static const searchUsers = '/users/search';
  static const qrCode = '/users/me/qr-code';

  static String userStatus(String id) => '/users/$id/status';
  static String userProfile(String id) => '/users/$id/profile';
  static String mutualFriends(String id) => '/users/$id/mutual-friends';
  static String blockUser(String id) => '/users/$id/block';
}