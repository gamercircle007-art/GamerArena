import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:visibility_detector/visibility_detector.dart';

class ReelVideoPlayer extends StatefulWidget {
  const ReelVideoPlayer({
    super.key,
    required this.videoUrl,
    required this.isActive,
    this.filterMatrix,
    this.muted = false,
    this.onTap,
    this.onDoubleTap,
  });

  final String videoUrl;
  final bool isActive;
  final List<double>? filterMatrix;
  final bool muted;
  final VoidCallback? onTap;
  final VoidCallback? onDoubleTap;

  @override
  State<ReelVideoPlayer> createState() => _ReelVideoPlayerState();
}

class _ReelVideoPlayerState extends State<ReelVideoPlayer> {
  VideoPlayerController? _controller;
  bool _initialized = false;
  bool _paused = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  @override
  void didUpdateWidget(ReelVideoPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.videoUrl != widget.videoUrl) {
      _disposeController();
      _init();
    }
    if (oldWidget.isActive != widget.isActive) {
      _syncPlayback();
    }
    if (oldWidget.muted != widget.muted && _controller != null) {
      _controller!.setVolume(widget.muted ? 0 : 1);
    }
  }

  Future<void> _init() async {
    final controller = VideoPlayerController.networkUrl(Uri.parse(widget.videoUrl));
    _controller = controller;
    try {
      await controller.initialize();
      await controller.setLooping(true);
      await controller.setVolume(widget.muted ? 0 : 1);
      if (mounted) {
        setState(() => _initialized = true);
        _syncPlayback();
      }
    } catch (_) {
      if (mounted) setState(() => _initialized = false);
    }
  }

  void _syncPlayback() {
    final c = _controller;
    if (c == null || !_initialized) return;
    if (widget.isActive && !_paused) {
      c.play();
    } else {
      c.pause();
    }
  }

  void _disposeController() {
    _controller?.dispose();
    _controller = null;
    _initialized = false;
  }

  @override
  void dispose() {
    _disposeController();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialized || _controller == null) {
      return const Center(
        child: CircularProgressIndicator(color: Colors.white),
      );
    }

    Widget video = FittedBox(
      fit: BoxFit.cover,
      child: SizedBox(
        width: _controller!.value.size.width,
        height: _controller!.value.size.height,
        child: VideoPlayer(_controller!),
      ),
    );

    if (widget.filterMatrix != null) {
      video = ColorFiltered(
        colorFilter: ColorFilter.matrix(widget.filterMatrix!),
        child: video,
      );
    }

    return VisibilityDetector(
      key: Key(widget.videoUrl),
      onVisibilityChanged: (info) {
        if (info.visibleFraction < 0.6) {
          _controller?.pause();
        } else if (widget.isActive && !_paused) {
          _controller?.play();
        }
      },
      child: GestureDetector(
        onTap: () {
          setState(() {
            _paused = !_paused;
            if (_paused) {
              _controller?.pause();
            } else {
              _controller?.play();
            }
          });
          widget.onTap?.call();
        },
        onDoubleTap: widget.onDoubleTap,
        onLongPressStart: (_) => _controller?.pause(),
        onLongPressEnd: (_) {
          if (!_paused) _controller?.play();
        },
        child: Stack(
          fit: StackFit.expand,
          children: [
            video,
            if (_paused)
              const Center(
                child: Icon(Icons.play_arrow_rounded, size: 72, color: Colors.white70),
              ),
          ],
        ),
      ),
    );
  }
}

List<double>? filterMatrixForName(String name) {
  switch (name) {
    case 'bright':
      return const [
        1.2, 0, 0, 0, 20,
        0, 1.2, 0, 0, 20,
        0, 0, 1.2, 0, 20,
        0, 0, 0, 1, 0,
      ];
    case 'vintage':
      return const [
        0.9, 0.3, 0.1, 0, 10,
        0.2, 0.8, 0.1, 0, 5,
        0.1, 0.2, 0.7, 0, 0,
        0, 0, 0, 1, 0,
      ];
    case 'cinema':
      return const [
        1.1, 0, 0, 0, -10,
        0, 1.0, 0, 0, 0,
        0, 0, 0.9, 0, 10,
        0, 0, 0, 1, 0,
      ];
    case 'warm':
      return const [
        1.1, 0.1, 0, 0, 15,
        0, 1.0, 0, 0, 5,
        0, 0, 0.9, 0, 0,
        0, 0, 0, 1, 0,
      ];
    case 'cool':
      return const [
        0.9, 0, 0.1, 0, 0,
        0, 1.0, 0.1, 0, 0,
        0.1, 0.1, 1.2, 0, 10,
        0, 0, 0, 1, 0,
      ];
    case 'bw':
      return const [
        0.33, 0.33, 0.33, 0, 0,
        0.33, 0.33, 0.33, 0, 0,
        0.33, 0.33, 0.33, 0, 0,
        0, 0, 0, 1, 0,
      ];
    default:
      return null;
  }
}