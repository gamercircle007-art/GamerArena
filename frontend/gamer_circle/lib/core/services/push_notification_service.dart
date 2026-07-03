/// FCM push notification service (stub until Firebase credentials are configured).
///
/// Wire firebase_core + firebase_messaging when google-services.json and
/// GoogleService-Info.plist are added to the project.
class PushNotificationService {
  PushNotificationService._();
  static final PushNotificationService instance = PushNotificationService._();

  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
  }

  Future<void> requestPermission() async {}

  void handleNotificationTap(Map<String, dynamic> data) {}
}