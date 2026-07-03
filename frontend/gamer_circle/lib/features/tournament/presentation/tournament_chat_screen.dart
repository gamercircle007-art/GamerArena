import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

class ChatMessage {
  ChatMessage({
    required this.userId,
    required this.content,
    required this.sentAt,
  });

  final String userId;
  final String content;
  final DateTime sentAt;

  factory ChatMessage.fromPayload(Map<String, dynamic> json) => ChatMessage(
        userId: json['user_id'] as String? ?? 'unknown',
        content: json['content'] as String? ?? '',
        sentAt: DateTime.now(),
      );
}

class TournamentChatScreen extends ConsumerStatefulWidget {
  const TournamentChatScreen({super.key, required this.tournamentId});

  final String tournamentId;

  @override
  ConsumerState<TournamentChatScreen> createState() => _TournamentChatScreenState();
}

class _TournamentChatScreenState extends ConsumerState<TournamentChatScreen> {
  final _messages = <ChatMessage>[];
  final _controller = TextEditingController();
  StreamSubscription<Map<String, dynamic>>? _wsSub;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    final channel = 'tournament_chat:${widget.tournamentId}';
    WsService.instance.subscribe(channel);
    _wsSub = WsService.instance.events.listen((event) {
      if (event['event'] == 'chat_message') {
        final payload = event['payload'];
        if (payload is Map<String, dynamic>) {
          setState(() => _messages.add(ChatMessage.fromPayload(payload)));
        }
      }
    });
  }

  @override
  void dispose() {
    WsService.instance.unsubscribe('tournament_chat:${widget.tournamentId}');
    _wsSub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() => _sending = true);
    try {
      await ref.read(dioProvider).post(
        '/tournaments/${widget.tournamentId}/chat',
        data: {'content': text},
      );
      _controller.clear();
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tournament Chat')),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? const Center(child: Text('No messages yet. Say hi!'))
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _messages.length,
                    itemBuilder: (_, i) {
                      final m = _messages[i];
                      return Align(
                        alignment: Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.deepPurple.shade50,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                m.userId.substring(0, 8),
                                style: TextStyle(
                                  fontSize: 11,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                              Text(m.content),
                            ],
                          ),
                        ),
                      );
                    },
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
                      decoration: const InputDecoration(hintText: 'Message...'),
                    ),
                  ),
                  IconButton(
                    onPressed: _sending ? null : _send,
                    icon: _sending
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.send),
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