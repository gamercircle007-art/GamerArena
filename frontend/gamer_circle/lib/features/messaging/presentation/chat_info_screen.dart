import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/shared/models/message.dart';

class ChatInfoScreen extends ConsumerStatefulWidget {
  const ChatInfoScreen({
    super.key,
    required this.conversationId,
    required this.otherUserName,
  });

  final String conversationId;
  final String otherUserName;

  @override
  ConsumerState<ChatInfoScreen> createState() => _ChatInfoScreenState();
}

class _ChatInfoScreenState extends ConsumerState<ChatInfoScreen> {
  List<Message> _media = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadMedia();
  }

  Future<void> _loadMedia() async {
    try {
      _media = await ref.read(messagingRepositoryProvider).getMedia(widget.conversationId);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.otherUserName)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                const ListTile(
                  title: Text('Media, Links and Docs'),
                  subtitle: Text('Photos and videos shared in this chat'),
                ),
                if (_media.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(24),
                    child: Center(child: Text('No media yet')),
                  )
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(12),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 4,
                      mainAxisSpacing: 4,
                    ),
                    itemCount: _media.length,
                    itemBuilder: (_, i) {
                      final m = _media[i];
                      return Container(
                        color: Colors.grey.shade200,
                        child: m.thumbnailUrl != null || m.mediaUrl != null
                            ? Image.network(
                                m.thumbnailUrl ?? m.mediaUrl!,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => const Icon(Icons.image),
                              )
                            : const Icon(Icons.audiotrack),
                      );
                    },
                  ),
              ],
            ),
    );
  }
}