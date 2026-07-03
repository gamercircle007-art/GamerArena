import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

final unreadNotificationCountProvider =
    StateNotifierProvider<UnreadCountNotifier, int>((ref) {
  return UnreadCountNotifier(ref);
});

class UnreadCountNotifier extends StateNotifier<int> {
  UnreadCountNotifier(this._ref) : super(0) {
    _load();
    WsService.instance.events.listen((event) {
      if (event['event'] == 'notification') {
        state = state + 1;
      }
    });
  }

  final Ref _ref;

  Future<void> _load() async {
    try {
      final count = await _ref.read(socialApiProvider).unreadCount();
      state = count;
    } catch (_) {}
  }

  void reset() => state = 0;
}