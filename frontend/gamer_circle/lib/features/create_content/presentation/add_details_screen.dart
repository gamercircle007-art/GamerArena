import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/constants/social_api_paths.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/services/dms_service.dart';
import 'package:gamer_circle/core/utils/api_error_utils.dart';

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
  bool _publishing = false;

  @override
  void dispose() {
    _captionCtrl.dispose();
    super.dispose();
  }

  bool _isLocalFilePath(String path) {
    return path.startsWith('/') ||
        path.startsWith('file:') ||
        !path.startsWith('http');
  }

  Future<void> _publish() async {
    if (_publishing) return;
    setState(() => _publishing = true);

    try {
      String? finalUrl = widget.videoUrl;
      if (finalUrl != null && _isLocalFilePath(finalUrl)) {
        final localPath =
            finalUrl.startsWith('file:') ? Uri.parse(finalUrl).toFilePath() : finalUrl;
        final file = File(localPath);
        if (!await file.exists()) {
          throw StateError('Selected media file was not found');
        }
        try {
          final result = await ref.read(dmsServiceProvider).uploadFile(
                file: file,
                assetType: 'video',
                fileType: 'video/mp4',
                context: widget.postType == 'reel' || widget.postType == 'short'
                    ? 'reel'
                    : 'post',
              );
          finalUrl = result.cdnUrl;
        } on DioException catch (e) {
          throw Exception(
            messageFromDioException(e, 'Media upload failed'),
          );
        }
      }

      // Dio baseUrl already includes /api/v1 — never prefix paths again.
      final dio = ref.read(dioProvider);
      final caption = _captionCtrl.text.trim();
      await dio.post(
        SocialApiPaths.posts,
        data: {
          'content': caption.isEmpty ? 'New ${widget.postType}' : caption,
          'media_urls': finalUrl != null && finalUrl.startsWith('http')
              ? [finalUrl]
              : <String>[],
          'post_type': widget.postType,
          'title': caption.isEmpty ? null : caption,
          'visibility': _visibility.toLowerCase(),
          'audience': _audience.toLowerCase().replaceAll(' ', ''),
          'game_types': _gameTypes,
          'hashtags': <String>[],
          'allow_comments': allowComments,
          'allow_remix': allowRemix,
          'allow_duet': allowDuet,
          'hide_likes': hideLikes,
          'duration_seconds': widget.durationSeconds?.toDouble(),
        },
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Content uploaded!')),
      );
      context.go('/feed');
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            messageFromDioException(e, 'Could not create post'),
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Upload error: $e')),
      );
    } finally {
      if (mounted) setState(() => _publishing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = true;
    final title = widget.postType == 'reel' || widget.postType == 'short'
        ? 'Upload Short'
        : 'Post';

    return Scaffold(
      backgroundColor: isDark ? Colors.black : AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: isDark ? Colors.black : AppColors.surfaceLight,
        title: const Text('Add details'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
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
                        ? DecorationImage(
                            image: NetworkImage(widget.videoUrl!),
                            fit: BoxFit.cover,
                          )
                        : null,
                  ),
                  child: widget.videoUrl!.startsWith('http')
                      ? null
                      : const Center(
                          child: Icon(Icons.videocam, color: Colors.white),
                        ),
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
          const ListTile(
            leading: CircleAvatar(
              backgroundImage:
                  NetworkImage('https://picsum.photos/id/1011/200/200'),
            ),
            title: Text('Sheera'),
            subtitle: Text('@sheera'),
          ),
          const Divider(color: Colors.white12),
          _buildSettingTile('🌐 Visibility', _visibility, () async {
            final v =
                await _showOptions(context, ['Public', 'Friends', 'Private']);
            if (v != null) setState(() => _visibility = v);
          }),
          _buildSettingTile('👥 Select audience', _audience, () async {
            final a = await _showOptions(
              context,
              ['Everyone', 'Followers only', '18+'],
            );
            if (a != null) setState(() => _audience = a);
          }),
          _buildSettingTile(
            '🎮 Game type',
            _gameTypes.isEmpty ? 'Select' : _gameTypes.join(', '),
            () async {
              setState(() => _gameTypes = ['BGMI', 'Valorant']);
            },
          ),
          _buildSettingTile('📍 Location', _location ?? 'Tag a parlor', () {
            setState(() => _location = 'Neon Arena Delhi');
          }),
          _buildSettingTile('💬 Community', 'Comments, Remix, Duet', () async {}),
          const Divider(color: Colors.white12),
          const Text(
            'By posting, you agree to our Terms.',
            style: TextStyle(color: Colors.white54, fontSize: 12),
          ),
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
                  onPressed: _publishing ? null : () => context.pop(),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white,
                    side: const BorderSide(color: Colors.white54),
                  ),
                  child: const Text('Save draft'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: _publishing ? null : _publish,
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.black,
                  ),
                  child: _publishing
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(title),
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
            .map(
              (o) => ListTile(
                title: Text(o, style: const TextStyle(color: Colors.white)),
                onTap: () => Navigator.pop(c, o),
              ),
            )
            .toList(),
      ),
    );
  }
}
