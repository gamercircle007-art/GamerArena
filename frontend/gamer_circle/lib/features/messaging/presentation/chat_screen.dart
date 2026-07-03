import 'dart:async';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:intl/intl.dart';
import 'package:gamer_circle/features/messaging/providers/messages_provider.dart';
import 'package:gamer_circle/shared/models/message.dart';
import 'package:gamer_circle/features/messaging/presentation/chat_info_screen.dart';
import 'package:gamer_circle/shared/widgets/message_bubble.dart';
import 'package:gamer_circle/shared/widgets/reactions_row.dart';
import 'package:flutter_slidable/flutter_slidable.dart';
import 'package:gamer_circle/shared/widgets/online_dot.dart';
import 'package:gamer_circle/shared/widgets/typing_indicator.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({
    super.key,
    required this.conversationId,
    required this.otherUserId,
    required this.otherUserName,
    this.otherUserAvatar,
  });

  final String conversationId;
  final String otherUserId;
  final String otherUserName;
  final String? otherUserAvatar;

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _textCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final _focusNode = FocusNode();
  Timer? _typingTimer;
  bool _isTyping = false;
  bool _showNewMsgBtn = false;
  bool _ephemeralMode = false;
  bool _showEmoji = false;
  String? _replyToId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(messagesProvider(widget.conversationId).notifier).markAllRead();
    });
    _scrollCtrl.addListener(() {
      if (!_scrollCtrl.hasClients) return;
      final atBottom = _scrollCtrl.position.pixels < 200;
      if (atBottom != !_showNewMsgBtn) setState(() => _showNewMsgBtn = !atBottom);
    });
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    _focusNode.dispose();
    _typingTimer?.cancel();
    _stopTyping();
    super.dispose();
  }

  void _onTextChange(String text) {
    if (text.isNotEmpty && !_isTyping) {
      _isTyping = true;
      WsService.instance.sendAction('typing_start', {
        'conversation_id': widget.conversationId,
      });
    }
    _typingTimer?.cancel();
    _typingTimer = Timer(const Duration(seconds: 3), _stopTyping);
  }

  void _stopTyping() {
    if (_isTyping) {
      _isTyping = false;
      WsService.instance.sendAction('typing_stop', {
        'conversation_id': widget.conversationId,
      });
    }
  }

  Future<void> _send() async {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) return;
    _textCtrl.clear();
    _stopTyping();
    await ref.read(messagesProvider(widget.conversationId).notifier).sendMessage(
          content: text,
          replyToId: _replyToId,
          isEphemeral: _ephemeralMode,
        );
    setState(() => _replyToId = null);
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          0,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final messagesAsync = ref.watch(messagesProvider(widget.conversationId));
    final isOnline = ref.watch(userOnlineStatusProvider(widget.otherUserId));
    final typingUsers = ref.watch(typingUsersProvider(widget.conversationId));

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF5E5873),
        elevation: 0,
        titleSpacing: 0,
        title: Row(
          children: [
            Stack(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: const Color(0xFF7367F0).withOpacity(0.1),
                  backgroundImage: widget.otherUserAvatar != null
                      ? CachedNetworkImageProvider(widget.otherUserAvatar!)
                      : null,
                  child: widget.otherUserAvatar == null
                      ? Text(
                          widget.otherUserName.isNotEmpty
                              ? widget.otherUserName[0].toUpperCase()
                              : '?',
                          style: const TextStyle(
                            color: Color(0xFF7367F0),
                            fontWeight: FontWeight.bold,
                          ),
                        )
                      : null,
                ),
                Positioned(
                  bottom: 0,
                  right: 0,
                  child: OnlineDot(isOnline: isOnline, size: OnlineDotSize.small),
                ),
              ],
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.otherUserName,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF5E5873),
                  ),
                ),
                Text(
                  isOnline ? 'Active now' : 'Offline',
                  style: TextStyle(
                    fontSize: 11,
                    color: isOnline ? Colors.green : const Color(0xFF82868B),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              _ephemeralMode ? Icons.local_fire_department : Icons.local_fire_department_outlined,
              color: _ephemeralMode ? Colors.orange : null,
            ),
            onPressed: () => setState(() => _ephemeralMode = !_ephemeralMode),
          ),
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ChatInfoScreen(
                  conversationId: widget.conversationId,
                  otherUserName: widget.otherUserName,
                ),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Stack(
              children: [
                messagesAsync.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (e, _) => Center(child: Text('Error: $e')),
                  data: (messages) => _MessagesList(
                    messages: messages,
                    conversationId: widget.conversationId,
                    scrollCtrl: _scrollCtrl,
                    onLoadMore: () => ref
                        .read(messagesProvider(widget.conversationId).notifier)
                        .loadMore(),
                    onReply: (id) => setState(() => _replyToId = id),
                    onReact: (msgId, emoji) => ref
                        .read(messagesProvider(widget.conversationId).notifier)
                        .addReaction(msgId, emoji),
                  ),
                ),
                if (_showNewMsgBtn)
                  Positioned(
                    bottom: 8,
                    left: 0,
                    right: 0,
                    child: Center(
                      child: GestureDetector(
                        onTap: _scrollToBottom,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 7,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFF7367F0),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Text(
                            'New messages ↓',
                            style: TextStyle(color: Colors.white, fontSize: 12),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          if (typingUsers.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Align(
                alignment: Alignment.centerLeft,
                child: TypingIndicator(userName: widget.otherUserName),
              ),
            ),
          if (_replyToId != null)
            Container(
              color: const Color(0xFFF0EFFF),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  const Icon(Icons.reply, size: 16, color: Color(0xFF7367F0)),
                  const SizedBox(width: 8),
                  const Expanded(child: Text('Replying...', style: TextStyle(fontSize: 12))),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => setState(() => _replyToId = null),
                  ),
                ],
              ),
            ),
          _buildInputBar(),
        ],
      ),
    );
  }

  void _showAttachmentSheet() {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.photo_outlined),
              title: const Text('Photo'),
              onTap: () => Navigator.pop(ctx),
            ),
            ListTile(
              leading: const Icon(Icons.videocam_outlined),
              title: const Text('Video'),
              onTap: () => Navigator.pop(ctx),
            ),
            ListTile(
              leading: const Icon(Icons.location_on_outlined),
              title: const Text('Location'),
              onTap: () => Navigator.pop(ctx),
            ),
            ListTile(
              leading: const Icon(Icons.mic_outlined),
              title: const Text('Audio'),
              onTap: () => Navigator.pop(ctx),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputBar() {
    final hasText = _textCtrl.text.trim().isNotEmpty;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (_showEmoji)
          Container(
            height: 200,
            color: Colors.white,
            child: GridView.count(
              crossAxisCount: 8,
              padding: const EdgeInsets.all(8),
              children: ['😀', '😂', '❤️', '🔥', '👍', '🎮', '😮', '😢', '🙌', '✨']
                  .map((e) => GestureDetector(
                        onTap: () {
                          _textCtrl.text += e;
                          _onTextChange(_textCtrl.text);
                        },
                        child: Center(child: Text(e, style: const TextStyle(fontSize: 24))),
                      ))
                  .toList(),
            ),
          ),
        Container(
          color: Colors.white,
          padding: EdgeInsets.only(
            left: 8,
            right: 12,
            top: 8,
            bottom: MediaQuery.of(context).padding.bottom + 8,
          ),
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.add_circle_outline),
                onPressed: _showAttachmentSheet,
              ),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFFF8F8F8),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: const Color(0xFFE4E4E4)),
                  ),
                  child: TextField(
                    controller: _textCtrl,
                    focusNode: _focusNode,
                    onChanged: (v) {
                      _onTextChange(v);
                      setState(() {});
                    },
                    maxLines: 5,
                    minLines: 1,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      hintText: 'Message...',
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                  ),
                ),
              ),
              IconButton(
                icon: Icon(_showEmoji ? Icons.keyboard : Icons.emoji_emotions_outlined),
                onPressed: () => setState(() => _showEmoji = !_showEmoji),
              ),
              GestureDetector(
                onTap: hasText ? _send : null,
                child: Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: hasText ? const Color(0xFF7367F0) : Colors.grey.shade300,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    hasText ? Icons.send_rounded : Icons.mic,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MessagesList extends StatelessWidget {
  const _MessagesList({
    required this.messages,
    required this.conversationId,
    required this.scrollCtrl,
    required this.onLoadMore,
    required this.onReply,
    required this.onReact,
  });

  final List<Message> messages;
  final String conversationId;
  final ScrollController scrollCtrl;
  final VoidCallback onLoadMore;
  final void Function(String id) onReply;
  final void Function(String msgId, String emoji) onReact;

  void _showReactions(BuildContext context, Message msg) {
    showModalBottomSheet(
      context: context,
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Wrap(
          spacing: 16,
          children: ['❤️', '😂', '😮', '🎮', '👍'].map((e) {
            return GestureDetector(
              onTap: () {
                Navigator.pop(context);
                onReact(msg.id, e);
              },
              child: Text(e, style: const TextStyle(fontSize: 28)),
            );
          }).toList(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return NotificationListener<ScrollNotification>(
      onNotification: (n) {
        if (n is ScrollEndNotification &&
            scrollCtrl.position.pixels >= scrollCtrl.position.maxScrollExtent - 200) {
          onLoadMore();
        }
        return false;
      },
      child: ListView.builder(
        reverse: true,
        controller: scrollCtrl,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        itemCount: messages.length,
        itemBuilder: (_, i) {
          final msg = messages[i];
          final showDate = i == messages.length - 1 ||
              !_sameDay(msg.createdAt, messages[i + 1].createdAt);
          return Column(
            crossAxisAlignment:
                msg.isMine ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: [
              if (showDate) _DateSeparator(date: msg.createdAt),
              Slidable(
                startActionPane: ActionPane(
                  motion: const DrawerMotion(),
                  extentRatio: 0.15,
                  children: [
                    SlidableAction(
                      onPressed: (_) => onReply(msg.id),
                      icon: Icons.reply,
                      backgroundColor: const Color(0xFF7367F0).withOpacity(0.1),
                      foregroundColor: const Color(0xFF7367F0),
                    ),
                  ],
                ),
                child: MessageBubble(
                  message: msg,
                  onLongPress: () => _showReactions(context, msg),
                ),
              ),
              ReactionsRow(
                reactions: msg.reactions,
                onEmojiTap: (e) => onReact(msg.id, e),
              ),
            ],
          );
        },
      ),
    );
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;
}

class _DateSeparator extends StatelessWidget {
  const _DateSeparator({required this.date});

  final DateTime date;

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    String label;
    if (_sameDay(date, now)) {
      label = 'Today';
    } else if (_sameDay(date, now.subtract(const Duration(days: 1)))) {
      label = 'Yesterday';
    } else {
      label = DateFormat('MMM d, yyyy').format(date);
    }
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.grey.shade200,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
        ),
      ),
    );
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;
}