import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/services/dms_service.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'dart:io';

class AddDetailsScreen extends ConsumerStatefulWidget {
  final String postType; // post, reel, video
  final String? videoUrl;
  final int? durationSeconds;

  const AddDetailsScreen({
    super.key,
    required this.postType,
    this.videoUrl,
    this.durationSeconds,
  });

  @override
  ConsumerState<AddDetailsScreen> createState() => _AddDetailsScreenState();
}

class _AddDetailsScreenState extends ConsumerState<AddDetailsScreen> {
  final _captionCtrl = TextEditingController();
  String _visibility = 'Public';
  String _audience = 'Everyone';
  List<String> _gameTypes = [];
  String? _location;
  bool allowComments = true;
  bool allowRemix = true;
  bool allowDuet = true;
  bool hideLikes = false;

  @override
  Widget build(BuildContext context) {
    final isDark = true;
    final title = widget.postType == 'reel' || widget.postType == 'short' ? 'Upload Short' : 'Post';

    return Scaffold(
      backgroundColor: isDark ? Colors.black : AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: isDark ? Colors.black : AppColors.surfaceLight,
        title: const Text('Add details'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Thumbnail + caption row (for video/short)
          if (widget.videoUrl != null)
            Row(
              children: [
                Container(
                  width: 120,
                  height: 70,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade800,
                    borderRadius: BorderRadius.circular(8),
                    image: widget.videoUrl!.startsWith('http')
                        ? DecorationImage(image: NetworkImage(widget.videoUrl!), fit: BoxFit.cover)
                        : null,
                  ),
                  child: widget.videoUrl!.startsWith('http') ? null : const Center(child: Icon(Icons.videocam, color: Colors.white)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _captionCtrl,
                    maxLines: 3,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      hintText: 'Caption your Short #gaming',
                      hintStyle: TextStyle(color: Colors.white38),
                      border: InputBorder.none,
                    ),
                  ),
                ),
              ],
            )
          else
            TextField(
              controller: _captionCtrl,
              maxLines: 4,
              style: const TextStyle(color: Colors.white, fontSize: 16),
              decoration: const InputDecoration(
                hintText: "What's on your gaming mind?",
                hintStyle: TextStyle(color: Colors.white38),
                border: InputBorder.none,
              ),
            ),

          const Divider(color: Colors.white12),

          // Author
          const ListTile(
            leading: CircleAvatar(backgroundImage: NetworkImage('https://picsum.photos/id/1011/200/200')),
            title: Text('Sheera'),
            subtitle: Text('@sheera'),
          ),

          const Divider(color: Colors.white12),

          _buildSettingTile('🌐 Visibility', _visibility, () async {
            final v = await _showOptions(context, ['Public', 'Friends', 'Private']);
            if (v != null) setState(() => _visibility = v);
          }),
          _buildSettingTile('👥 Select audience', _audience, () async {
            final a = await _showOptions(context, ['Everyone', 'Followers only', '18+']);
            if (a != null) setState(() => _audience = a);
          }),
          _buildSettingTile('🎮 Game type', _gameTypes.isEmpty ? 'Select' : _gameTypes.join(', '), () async {
            setState(() => _gameTypes = ['BGMI', 'Valorant']);
          }),
          _buildSettingTile('📍 Location', _location ?? 'Tag a parlor', () {
            setState(() => _location = 'Neon Arena Delhi');
          }),

          _buildSettingTile('💬 Community', 'Comments, Remix, Duet', () async {
            // stub for now
          }),

          const Divider(color: Colors.white12),

          const Text('By posting, you agree to our Terms.', style: TextStyle(color: Colors.white54, fontSize: 12)),

          const SizedBox(height: 80),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () {
                    // TODO: save draft
                    context.pop();
                  },
                  style: OutlinedButton.styleFrom(foregroundColor: Colors.white, side: const BorderSide(color: Colors.white54)),
                  child: const Text('Save draft'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: () async {
                    // Demo: upload if local video, then create
                    String? finalUrl = widget.videoUrl;
                    if (widget.videoUrl != null && widget.videoUrl!.startsWith('/')) {
                      try {
                        final dms = ref.read(dmsServiceProvider);
                        final result = await dms.uploadFile(
                          file: File(widget.videoUrl!),
                          assetType: 'video',
                          fileType: 'video/mp4',
                          context: 'reel',
                        );
                        finalUrl = result.cdnUrl;
                      } catch (e) {}
                    }
                    // Hook backend create
                    try {
                      final dio = ref.read(dioProvider);
                      await dio.post('/api/v1/posts', data: {
                        'content': _captionCtrl.text.trim().isEmpty ? 'New ${widget.postType}' : _captionCtrl.text.trim(),
                        'media_urls': finalUrl != null ? [finalUrl] : [],
                        'post_type': widget.postType,
                        'title': _captionCtrl.text.trim(),
                        'visibility': _visibility.toLowerCase(),
                        'audience': _audience.toLowerCase().replaceAll(' ', ''),
                        'game_types': _gameTypes,
                        'hashtags': [], // extracted in backend
                        'allow_comments': allowComments,
                        'allow_remix': allowRemix,
                        'duration_seconds': widget.durationSeconds?.toDouble(),
                        'video_asset_id': null, // set if using asset
                      });
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Content uploaded!')));
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Upload error: $e')));
                    }
                    context.go('/feed');
                  },
                  style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.black),
                  child: Text(title),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSettingTile(String title, String value, VoidCallback onTap) {
    return ListTile(
      title: Text(title, style: const TextStyle(color: Colors.white)),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(value, style: const TextStyle(color: Colors.white70)),
          const Icon(Icons.chevron_right, color: Colors.white54),
        ],
      ),
      onTap: onTap,
    );
  }

  Future<String?> _showOptions(BuildContext ctx, List<String> options) async {
    return showModalBottomSheet<String>(
      context: ctx,
      backgroundColor: Colors.grey.shade900,
      builder: (c) => Column(
        mainAxisSize: MainAxisSize.min,
        children: options
            .map((o) => ListTile(
                  title: Text(o, style: const TextStyle(color: Colors.white)),
                  onTap: () => Navigator.pop(c, o),
                ))
            .toList(),
      ),
    );
  }
}
