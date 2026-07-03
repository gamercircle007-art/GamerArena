import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/reels/widgets/reel_video_player.dart';
import 'package:image_picker/image_picker.dart';
import 'package:video_compress/video_compress.dart';
import 'package:video_player/video_player.dart';

const kReelFilters = [
  'normal',
  'bright',
  'vintage',
  'cinema',
  'warm',
  'cool',
  'bw',
];

const kAspectRatios = ['9:16', '1:1', '4:5'];

const kPrivacyOptions = [
  ('public', 'Public'),
  ('followers', 'Followers Only'),
  ('friends', 'Friends Only'),
  ('private', 'Private'),
  ('unlisted', 'Unlisted'),
  ('country_only', 'Country Only'),
  ('international', 'International'),
];

class CreateReelScreen extends ConsumerStatefulWidget {
  const CreateReelScreen({super.key, this.initialPath});

  final String? initialPath;

  @override
  ConsumerState<CreateReelScreen> createState() => _CreateReelScreenState();
}

class _CreateReelScreenState extends ConsumerState<CreateReelScreen> {
  final _caption = TextEditingController();
  final _textOverlay = TextEditingController();
  String? _videoPath;
  VideoPlayerController? _preview;
  double _trimStart = 0;
  double _trimEnd = 30;
  double _duration = 30;
  String _aspectRatio = '9:16';
  String _filter = 'normal';
  String _privacy = 'public';
  String? _musicTitle;
  bool _muted = false;
  bool _uploading = false;
  double _uploadProgress = 0;
  bool _showTextOverlay = false;
  Offset _textPosition = const Offset(40, 120);

  @override
  void initState() {
    super.initState();
    if (widget.initialPath != null) {
      _setVideo(widget.initialPath!);
    }
  }

  @override
  void dispose() {
    _caption.dispose();
    _textOverlay.dispose();
    _preview?.dispose();
    super.dispose();
  }

  Future<void> _pickVideo(ImageSource source) async {
    final file = await ImagePicker().pickVideo(
      source: source,
      maxDuration: const Duration(seconds: 60),
    );
    if (file == null) return;
    await _setVideo(file.path);
  }

  Future<void> _setVideo(String path) async {
    _preview?.dispose();
    final controller = VideoPlayerController.file(File(path));
    await controller.initialize();
    final dur = controller.value.duration.inSeconds.toDouble().clamp(5.0, 60.0);
    setState(() {
      _videoPath = path;
      _preview = controller;
      _duration = dur;
      _trimEnd = dur.clamp(5.0, 30.0);
      _trimStart = 0;
    });
    controller.play();
    controller.setLooping(true);
  }

  Future<void> _showSourcePicker() async {
    await showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Choose from Gallery'),
              onTap: () {
                Navigator.pop(ctx);
                _pickVideo(ImageSource.gallery);
              },
            ),
            ListTile(
              leading: const Icon(Icons.videocam_outlined),
              title: const Text('Record Video'),
              onTap: () {
                Navigator.pop(ctx);
                _pickVideo(ImageSource.camera);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickMusic() async {
    final tracks = await ref.read(reelApiProvider).fetchDemoMusic();
    if (!mounted || tracks.isEmpty) return;
    final picked = await showModalBottomSheet<String>(
      context: context,
      builder: (ctx) => ListView(
        children: tracks
            .map(
              (t) => ListTile(
                title: Text(t['title'] as String? ?? 'Track'),
                subtitle: Text(t['artist'] as String? ?? ''),
                onTap: () => Navigator.pop(ctx, t['title'] as String?),
              ),
            )
            .toList(),
      ),
    );
    if (picked != null) setState(() => _musicTitle = picked);
  }

  Future<void> _upload() async {
    if (_videoPath == null) return;
    setState(() {
      _uploading = true;
      _uploadProgress = 0.1;
    });
    try {
      final info = await VideoCompress.compressVideo(
        _videoPath!,
        quality: VideoQuality.MediumQuality,
        deleteOrigin: false,
        includeAudio: !_muted,
      );
      final compressedPath = info?.path ?? _videoPath!;
      setState(() => _uploadProgress = 0.35);

      final bytes = await File(compressedPath).readAsBytes();
      final api = ref.read(socialApiProvider);
      final videoPresigned = await api.presignedUrl('video/mp4', 'reel_media');
      await api.uploadToPresignedUrl(
        uploadUrl: videoPresigned['upload_url'] as String,
        bytes: bytes,
        contentType: 'video/mp4',
      );
      setState(() => _uploadProgress = 0.65);

      String? thumbUrl;
      final thumb = await VideoCompress.getFileThumbnail(compressedPath, quality: 75);
      if (thumb.existsSync()) {
        final thumbPresigned = await api.presignedUrl('image/jpeg', 'reel_thumbnail');
        await api.uploadToPresignedUrl(
          uploadUrl: thumbPresigned['upload_url'] as String,
          bytes: await thumb.readAsBytes(),
          contentType: 'image/jpeg',
        );
        thumbUrl = thumbPresigned['public_url'] as String;
      }
      setState(() => _uploadProgress = 0.85);

      await ref.read(reelApiProvider).createReel({
        'video_url': videoPresigned['public_url'],
        'thumbnail_url': thumbUrl,
        'cover_url': thumbUrl,
        'caption': _caption.text.trim().isEmpty ? null : _caption.text.trim(),
        'duration_seconds': (_trimEnd - _trimStart).round().clamp(5, 30),
        'aspect_ratio': _aspectRatio,
        'filter_name': _filter,
        'music_title': _musicTitle,
        'privacy': _privacy,
        'width': 1080,
        'height': _aspectRatio == '9:16' ? 1920 : (_aspectRatio == '1:1' ? 1080 : 1350),
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Reel uploaded!')),
        );
        context.go('/reels');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Upload failed: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _uploading = false;
          _uploadProgress = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('Create Reel'),
        actions: [
          if (_videoPath != null)
            TextButton(
              onPressed: _uploading ? null : _upload,
              child: _uploading
                  ? SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        value: _uploadProgress > 0 ? _uploadProgress : null,
                        strokeWidth: 2,
                      ),
                    )
                  : const Text('Post', style: TextStyle(fontWeight: FontWeight.w700)),
            ),
        ],
      ),
      body: _videoPath == null
          ? Center(
              child: FilledButton.icon(
                onPressed: _showSourcePicker,
                icon: const Icon(Icons.video_library_outlined),
                label: const Text('Select or Record Video'),
              ),
            )
          : Column(
              children: [
                Expanded(
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      if (_preview != null && _preview!.value.isInitialized)
                        ColorFiltered(
                          colorFilter: ColorFilter.matrix(
                            filterMatrixForName(_filter) ??
                                const [
                                  1, 0, 0, 0, 0,
                                  0, 1, 0, 0, 0,
                                  0, 0, 1, 0, 0,
                                  0, 0, 0, 1, 0,
                                ],
                          ),
                          child: FittedBox(
                            fit: BoxFit.cover,
                            child: SizedBox(
                              width: _preview!.value.size.width,
                              height: _preview!.value.size.height,
                              child: VideoPlayer(_preview!),
                            ),
                          ),
                        ),
                      if (_showTextOverlay && _textOverlay.text.isNotEmpty)
                        Positioned(
                          left: _textPosition.dx,
                          top: _textPosition.dy,
                          child: GestureDetector(
                            onPanUpdate: (d) {
                              setState(() => _textPosition += d.delta);
                            },
                            child: Text(
                              _textOverlay.text,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 24,
                                fontWeight: FontWeight.w800,
                                shadows: [Shadow(color: Colors.black, blurRadius: 6)],
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                Container(
                  color: const Color(0xFF111111),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Trim (5–30 sec)', style: TextStyle(color: Colors.white70)),
                        RangeSlider(
                          values: RangeValues(_trimStart, _trimEnd),
                          min: 0,
                          max: _duration,
                          onChanged: (v) {
                            var start = v.start;
                            var end = v.end;
                            if (end - start < 5) end = start + 5;
                            if (end - start > 30) end = start + 30;
                            setState(() {
                              _trimStart = start;
                              _trimEnd = end;
                            });
                          },
                        ),
                        Wrap(
                          spacing: 8,
                          children: kAspectRatios.map((r) {
                            return ChoiceChip(
                              label: Text(r),
                              selected: _aspectRatio == r,
                              onSelected: (_) => setState(() => _aspectRatio = r),
                            );
                          }).toList(),
                        ),
                        const SizedBox(height: 8),
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: kReelFilters.map((f) {
                              return Padding(
                                padding: const EdgeInsets.only(right: 8),
                                child: ChoiceChip(
                                  label: Text(f),
                                  selected: _filter == f,
                                  onSelected: (_) => setState(() => _filter = f),
                                ),
                              );
                            }).toList(),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            FilterChip(
                              label: const Text('Mute'),
                              selected: _muted,
                              onSelected: (v) => setState(() => _muted = v),
                            ),
                            const SizedBox(width: 8),
                            ActionChip(
                              label: Text(_musicTitle ?? 'Add Music'),
                              onPressed: _pickMusic,
                            ),
                            const SizedBox(width: 8),
                            ActionChip(
                              label: const Text('Add Text'),
                              onPressed: () => setState(() => _showTextOverlay = true),
                            ),
                          ],
                        ),
                        if (_showTextOverlay) ...[
                          const SizedBox(height: 8),
                          TextField(
                            controller: _textOverlay,
                            style: const TextStyle(color: Colors.white),
                            decoration: const InputDecoration(
                              labelText: 'Overlay text',
                              labelStyle: TextStyle(color: Colors.white54),
                            ),
                            onChanged: (_) => setState(() {}),
                          ),
                        ],
                        const SizedBox(height: 8),
                        TextField(
                          controller: _caption,
                          style: const TextStyle(color: Colors.white),
                          decoration: const InputDecoration(
                            labelText: 'Caption & hashtags',
                            labelStyle: TextStyle(color: Colors.white54),
                          ),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          value: _privacy,
                          dropdownColor: const Color(0xFF222222),
                          style: const TextStyle(color: Colors.white),
                          decoration: const InputDecoration(labelText: 'Privacy'),
                          items: kPrivacyOptions
                              .map((e) => DropdownMenuItem(value: e.$1, child: Text(e.$2)))
                              .toList(),
                          onChanged: (v) => setState(() => _privacy = v ?? 'public'),
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