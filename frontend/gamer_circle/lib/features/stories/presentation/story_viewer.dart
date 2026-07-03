import 'dart:async';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/stories/providers/stories_provider.dart';
import 'package:gamer_circle/shared/models/story.dart';
import 'package:video_player/video_player.dart';

class StoryViewer extends ConsumerStatefulWidget {
  const StoryViewer({
    super.key,
    required this.groups,
    this.initialGroupIndex = 0,
  });

  final List<StoryGroup> groups;
  final int initialGroupIndex;

  @override
  ConsumerState<StoryViewer> createState() => _StoryViewerState();
}

class _StoryViewerState extends ConsumerState<StoryViewer> {
  late int _groupIndex;
  late int _storyIndex;
  Timer? _timer;
  double _progress = 0;
  bool _paused = false;
  VideoPlayerController? _videoCtrl;

  StoryGroup get _group => widget.groups[_groupIndex];
  Story get _story => _group.stories[_storyIndex];

  @override
  void initState() {
    super.initState();
    _groupIndex = widget.initialGroupIndex.clamp(0, widget.groups.length - 1);
    _storyIndex = 0;
    _startStory();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _videoCtrl?.dispose();
    super.dispose();
  }

  Future<void> _startStory() async {
    _timer?.cancel();
    _videoCtrl?.dispose();
    _videoCtrl = null;
    setState(() => _progress = 0);

    await ref.read(storiesFeedProvider.notifier).markViewed(_story.id);

    if (_story.mediaType == 'video') {
      _videoCtrl = VideoPlayerController.networkUrl(Uri.parse(_story.mediaUrl));
      await _videoCtrl!.initialize();
      _videoCtrl!.play();
      _videoCtrl!.addListener(() {
        if (_videoCtrl!.value.isInitialized && !_paused) {
          final d = _videoCtrl!.value.duration.inMilliseconds;
          final p = _videoCtrl!.value.position.inMilliseconds;
          if (d > 0) setState(() => _progress = p / d);
          if (_videoCtrl!.value.position >= _videoCtrl!.value.duration) {
            _nextStory();
          }
        }
      });
      setState(() {});
      return;
    }

    final duration = Duration(seconds: _story.durationSeconds);
    final started = DateTime.now();
    _timer = Timer.periodic(const Duration(milliseconds: 50), (t) {
      if (_paused) return;
      final elapsed = DateTime.now().difference(started);
      setState(() => _progress = elapsed.inMilliseconds / duration.inMilliseconds);
      if (elapsed >= duration) {
        t.cancel();
        _nextStory();
      }
    });
  }

  void _nextStory() {
    if (_storyIndex < _group.stories.length - 1) {
      setState(() => _storyIndex++);
      _startStory();
    } else if (_groupIndex < widget.groups.length - 1) {
      setState(() {
        _groupIndex++;
        _storyIndex = 0;
      });
      _startStory();
    } else {
      Navigator.pop(context);
    }
  }

  void _prevStory() {
    if (_storyIndex > 0) {
      setState(() => _storyIndex--);
      _startStory();
    } else if (_groupIndex > 0) {
      setState(() {
        _groupIndex--;
        _storyIndex = widget.groups[_groupIndex].stories.length - 1;
      });
      _startStory();
    }
  }

  Future<void> _replyToStory() async {
    final conv = await ref
        .read(conversationsProvider.notifier)
        .createConversation(_group.userId);
    if (!mounted) return;
    context.push(
      '/messages/chat/${conv.id}',
      extra: {
        'otherUserId': _group.userId,
        'otherUserName': _group.userName ?? 'User',
        'otherUserAvatar': _group.userAvatar,
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTapDown: (d) {
          final w = MediaQuery.of(context).size.width;
          if (d.globalPosition.dx < w / 3) {
            _prevStory();
          } else {
            _nextStory();
          }
        },
        onLongPressStart: (_) {
          setState(() => _paused = true);
          _videoCtrl?.pause();
        },
        onLongPressEnd: (_) {
          setState(() => _paused = false);
          _videoCtrl?.play();
        },
        onVerticalDragEnd: (d) {
          if (d.primaryVelocity != null && d.primaryVelocity! > 300) {
            Navigator.pop(context);
          } else if (d.primaryVelocity != null && d.primaryVelocity! < -300) {
            _replyToStory();
          }
        },
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (_story.mediaType == 'video' && _videoCtrl != null && _videoCtrl!.value.isInitialized)
              FittedBox(
                fit: BoxFit.cover,
                child: SizedBox(
                  width: _videoCtrl!.value.size.width,
                  height: _videoCtrl!.value.size.height,
                  child: VideoPlayer(_videoCtrl!),
                ),
              )
            else
              CachedNetworkImage(imageUrl: _story.mediaUrl, fit: BoxFit.cover),

            SafeArea(
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                    child: Row(
                      children: List.generate(_group.stories.length, (i) {
                        final value = i < _storyIndex
                            ? 1.0
                            : i == _storyIndex
                                ? _progress.clamp(0.0, 1.0)
                                : 0.0;
                        return Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 2),
                            child: LinearProgressIndicator(
                              value: value,
                              backgroundColor: Colors.white24,
                              color: Colors.white,
                              minHeight: 2,
                            ),
                          ),
                        );
                      }),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Row(
                      children: [
                        CircleAvatar(
                          backgroundImage: _group.userAvatar != null
                              ? NetworkImage(_group.userAvatar!)
                              : null,
                          child: _group.userAvatar == null
                              ? Text((_group.userName ?? '?')[0].toUpperCase())
                              : null,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _group.userName ?? 'Story',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close, color: Colors.white),
                          onPressed: () => Navigator.pop(context),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: _replyToStory,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                              decoration: BoxDecoration(
                                border: Border.all(color: Colors.white54),
                                borderRadius: BorderRadius.circular(24),
                              ),
                              child: Text(
                                "Reply to ${_group.userName ?? 'story'}...",
                                style: const TextStyle(color: Colors.white70),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Text('❤️', style: TextStyle(fontSize: 24)),
                        const SizedBox(width: 8),
                        const Text('😂', style: TextStyle(fontSize: 24)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}