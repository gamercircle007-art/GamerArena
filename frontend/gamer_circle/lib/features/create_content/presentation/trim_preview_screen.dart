import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

class TrimPreviewScreen extends StatefulWidget {
  final String videoPath;
  final int maxDuration;

  const TrimPreviewScreen({super.key, required this.videoPath, required this.maxDuration});

  @override
  State<TrimPreviewScreen> createState() => _TrimPreviewScreenState();
}

class _TrimPreviewScreenState extends State<TrimPreviewScreen> {
  late VideoPlayerController _controller;
  double _start = 0;
  double _end = 0;
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.networkUrl(Uri.parse(widget.videoPath))
      ..initialize().then((_) {
        _end = _controller.value.duration.inSeconds.toDouble().clamp(0, widget.maxDuration.toDouble());
        setState(() {});
      });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _togglePlay() {
    setState(() {
      if (_isPlaying) {
        _controller.pause();
      } else {
        _controller.play();
      }
      _isPlaying = !_isPlaying;
    });
  }

  void _goToAddDetails() {
    context.pushReplacement('/create/add-details', extra: {
      'postType': 'short',
      'videoUrl': widget.videoPath,
      'durationSeconds': (_end - _start).round(),
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text('Trim & Preview'),
        actions: [
          TextButton(
            onPressed: _goToAddDetails,
            child: const Text('Next', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: Column(
        children: [
          if (_controller.value.isInitialized)
            AspectRatio(
              aspectRatio: _controller.value.aspectRatio,
              child: VideoPlayer(_controller),
            )
          else
            const Expanded(child: Center(child: CircularProgressIndicator())),

          const SizedBox(height: 20),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('${_start.toInt()}s', style: const TextStyle(color: Colors.white)),
                    Text('${_end.toInt()}s / ${widget.maxDuration}s', style: const TextStyle(color: Colors.white70)),
                  ],
                ),
                RangeSlider(
                  values: RangeValues(_start, _end),
                  min: 0,
                  max: widget.maxDuration.toDouble(),
                  divisions: widget.maxDuration,
                  onChanged: (values) {
                    setState(() {
                      _start = values.start;
                      _end = values.end;
                    });
                  },
                  activeColor: AppColors.primary,
                ),
                const Text('Drag to trim (demo)', style: TextStyle(color: Colors.white54, fontSize: 12)),
              ],
            ),
          ),

          const Spacer(),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              IconButton(icon: const Icon(Icons.content_cut, color: Colors.white), onPressed: () {}),
              IconButton(icon: const Icon(Icons.volume_up, color: Colors.white), onPressed: () {}),
              IconButton(icon: const Icon(Icons.text_fields, color: Colors.white), onPressed: () {}),
              IconButton(icon: const Icon(Icons.emoji_emotions, color: Colors.white), onPressed: () {}),
            ],
          ),

          const SizedBox(height: 20),

          IconButton(
            iconSize: 48,
            icon: Icon(_isPlaying ? Icons.pause_circle : Icons.play_circle, color: Colors.white),
            onPressed: _controller.value.isInitialized ? _togglePlay : null,
          ),

          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
