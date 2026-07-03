import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/core/services/dms_service.dart';
import 'package:gamer_circle/features/stories/providers/stories_provider.dart';
import 'package:image_picker/image_picker.dart';

class StoryCreator extends ConsumerStatefulWidget {
  const StoryCreator({super.key});

  @override
  ConsumerState<StoryCreator> createState() => _StoryCreatorState();
}

class _StoryCreatorState extends ConsumerState<StoryCreator> {
  final _caption = TextEditingController();
  String? _mediaPath;
  String _mediaType = 'image';
  String _privacy = 'friends';
  bool _uploading = false;

  @override
  void dispose() {
    _caption.dispose();
    super.dispose();
  }

  Future<void> _pick(ImageSource source, {bool video = false}) async {
    final picker = ImagePicker();
    if (video) {
      final file = await picker.pickVideo(source: source, maxDuration: const Duration(seconds: 60));
      if (file != null) setState(() {
        _mediaPath = file.path;
        _mediaType = 'video';
      });
    } else {
      final file = await picker.pickImage(source: source, imageQuality: 85);
      if (file != null) setState(() {
        _mediaPath = file.path;
        _mediaType = 'image';
      });
    }
  }

  Future<void> _publish() async {
    if (_mediaPath == null || _uploading) return;
    setState(() => _uploading = true);
    try {
      final ext = _mediaPath!.split('.').last.toLowerCase();
      final fileType = _mediaType == 'video' ? 'video/$ext' : 'image/jpeg';
      final upload = await ref.read(dmsServiceProvider).uploadFile(
            file: File(_mediaPath!),
            assetType: _mediaType,
            fileType: fileType,
            context: 'story',
          );
      await ref.read(storiesRepositoryProvider).createStory(
            mediaUrl: upload.cdnUrl,
            assetId: upload.assetId,
            mediaType: _mediaType,
            caption: _caption.text.trim().isEmpty ? null : _caption.text.trim(),
            privacy: _privacy,
          );
      ref.invalidate(storiesFeedProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Story added!')),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        title: const Text('Add Story'),
        actions: [
          if (_mediaPath != null)
            TextButton(
              onPressed: _uploading ? null : _publish,
              child: _uploading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Share', style: TextStyle(color: Colors.white)),
            ),
        ],
      ),
      body: _mediaPath == null
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _PickButton(
                    icon: Icons.photo_library_outlined,
                    label: 'Gallery Photo',
                    onTap: () => _pick(ImageSource.gallery),
                  ),
                  const SizedBox(height: 12),
                  _PickButton(
                    icon: Icons.videocam_outlined,
                    label: 'Gallery Video',
                    onTap: () => _pick(ImageSource.gallery, video: true),
                  ),
                  const SizedBox(height: 12),
                  _PickButton(
                    icon: Icons.camera_alt_outlined,
                    label: 'Take Photo',
                    onTap: () => _pick(ImageSource.camera),
                  ),
                ],
              ),
            )
          : Column(
              children: [
                Expanded(
                  child: _mediaType == 'video'
                      ? const Center(
                          child: Icon(Icons.play_circle_fill, color: Colors.white, size: 64),
                        )
                      : Image.file(File(_mediaPath!), fit: BoxFit.contain),
                ),
                Container(
                  color: Colors.black87,
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      TextField(
                        controller: _caption,
                        style: const TextStyle(color: Colors.white),
                        decoration: const InputDecoration(
                          hintText: 'Add caption...',
                          hintStyle: TextStyle(color: Colors.white54),
                          border: InputBorder.none,
                        ),
                      ),
                      const SizedBox(height: 8),
                      SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(value: 'everyone', label: Text('Everyone')),
                          ButtonSegment(value: 'friends', label: Text('Friends')),
                          ButtonSegment(value: 'close_friends', label: Text('Close')),
                        ],
                        selected: {_privacy},
                        onSelectionChanged: (s) => setState(() => _privacy = s.first),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

class _PickButton extends StatelessWidget {
  const _PickButton({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, color: Colors.white),
      label: Text(label, style: const TextStyle(color: Colors.white)),
      style: OutlinedButton.styleFrom(
        side: const BorderSide(color: Colors.white54),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      ),
    );
  }
}