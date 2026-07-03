import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

typedef WsEventHandler = void Function(Map<String, dynamic> event);

class WsService {
  WsService._();
  static final WsService instance = WsService._();

  WebSocketChannel? _channel;
  final Set<String> _channels = {};
  final _eventController = StreamController<Map<String, dynamic>>.broadcast();
  Timer? _reconnectTimer;
  Timer? _heartbeatTimer;
  int _backoffSeconds = 1;
  String? _token;
  String? _baseUrl;

  final Map<String, bool> onlineUsers = {};

  Stream<Map<String, dynamic>> get events => _eventController.stream;

  Future<void> connect({required String baseUrl, required String token}) async {
    _baseUrl = baseUrl;
    _token = token;
    await _open();
    _startHeartbeat();
  }

  Future<void> _open() async {
    if (_token == null || _baseUrl == null) return;
    final uri = Uri.parse('$_baseUrl/ws?token=$_token');
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(uri);
    _backoffSeconds = 1;

    for (final channel in _channels) {
      _send({'action': 'subscribe', 'channel': channel});
    }

    _channel!.stream.listen(
      (raw) {
        try {
          final decoded = jsonDecode(raw as String) as Map<String, dynamic>;
          _handleEvent(decoded);
          _eventController.add(decoded);
        } catch (_) {}
      },
      onDone: _scheduleReconnect,
      onError: (_) => _scheduleReconnect(),
    );
  }

  void _handleEvent(Map<String, dynamic> event) {
    final type = event['type'] as String? ?? event['event'] as String?;
    if (type == 'user_online') {
      final uid = event['user_id'] as String?;
      if (uid != null) onlineUsers[uid] = true;
    } else if (type == 'user_offline') {
      final uid = event['user_id'] as String?;
      if (uid != null) onlineUsers[uid] = false;
    }

    final payload = event['payload'];
    if (payload is Map<String, dynamic>) {
      final payloadType = payload['type'] as String?;
      if (payloadType == 'user_online') {
        final uid = payload['user_id'] as String?;
        if (uid != null) onlineUsers[uid] = true;
      } else if (payloadType == 'user_offline') {
        final uid = payload['user_id'] as String?;
        if (uid != null) onlineUsers[uid] = false;
      }
    }
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _send({'type': 'heartbeat'});
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _send({'type': 'heartbeat'});
    });
  }

  void subscribe(String channel) {
    _channels.add(channel);
    _send({'action': 'subscribe', 'channel': channel});
  }

  void unsubscribe(String channel) {
    _channels.remove(channel);
    _send({'action': 'unsubscribe', 'channel': channel});
  }

  void sendAction(String action, Map<String, dynamic> data) {
    _send({'action': action, ...data});
  }

  void _send(Map<String, dynamic> payload) {
    _channel?.sink.add(jsonEncode(payload));
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(seconds: _backoffSeconds), () async {
      _backoffSeconds = (_backoffSeconds * 2).clamp(1, 8);
      await _open();
    });
  }

  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _heartbeatTimer?.cancel();
    await _channel?.sink.close();
    _channel = null;
    _channels.clear();
    onlineUsers.clear();
  }

  bool isUserOnline(String userId) => onlineUsers[userId] ?? false;
}