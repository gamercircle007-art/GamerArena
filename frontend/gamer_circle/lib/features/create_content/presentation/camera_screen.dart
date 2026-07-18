import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:image_picker/image_picker.dart';

class CameraScreen extends StatefulWidget {
  final String mode; // 'short' or 'video'
  const CameraScreen({super.key, required this.mode});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  List<CameraDescription> _cameras = [];
  bool _isRecording = false;
  String? _videoPath;
  int _selectedDuration = 15; // seconds
  final List<int> _durations = [15, 30, 60, 180];

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    _cameras = await availableCameras();
    if (_cameras.isNotEmpty) {
      _controller = CameraController(_cameras[0], ResolutionPreset.medium);
      await _controller!.initialize();
      if (mounted) setState(() {});
    }
  }

  Future<void> _toggleRecording() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    if (_isRecording) {
      final file = await _controller!.stopVideoRecording();
      setState(() {
        _isRecording = false;
        _videoPath = file.path;
      });
      if (mounted) {
        context.push('/create/trim', extra: {
          'videoPath': _videoPath,
          'maxDuration': _selectedDuration,
        });
      }
    } else {
      await _controller!.startVideoRecording();
      setState(() => _isRecording = true);
      // Auto stop after duration
      Future.delayed(Duration(seconds: _selectedDuration), () {
        if (mounted && _isRecording) _toggleRecording();
      });
    }
  }

  void _flipCamera() async {
    if (_cameras.length < 2) return;
    final current = _controller!.description;
    final newCam = _cameras.firstWhere((c) => c != current);
    await _controller!.dispose();
    _controller = CameraController(newCam, ResolutionPreset.medium);
    await _controller!.initialize();
    setState(() {});
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          CameraPreview(_controller!),

          // Top bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(icon: const Icon(Icons.close, color: Colors.white), onPressed: () => context.pop()),
                  Row(
                    children: [
                      IconButton(icon: const Icon(Icons.flash_off, color: Colors.white), onPressed: () {}),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(12)),
                        child: Text('${_selectedDuration}s', style: const TextStyle(color: Colors.white)),
                      ),
                    ],
                  ),
                  IconButton(icon: const Icon(Icons.flip_camera_ios, color: Colors.white), onPressed: _flipCamera),
                ],
              ),
            ),
          ),

          // Duration selector
          Positioned(
            top: 80,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: _durations.map((d) {
                final selected = d == _selectedDuration;
                return GestureDetector(
                  onTap: () => setState(() => _selectedDuration = d),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: selected ? AppColors.primary : Colors.black54,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text('${d}s', style: TextStyle(color: selected ? Colors.white : Colors.white70)),
                  ),
                );
              }).toList(),
            ),
          ),

          // Right side icons
          Positioned(
            right: 16,
            top: 150,
            child: Column(
              children: [
                IconButton(icon: const Icon(Icons.music_note, color: Colors.white, size: 28), onPressed: () {}),
                const SizedBox(height: 16),
                IconButton(icon: const Icon(Icons.flip_camera_ios, color: Colors.white, size: 28), onPressed: _flipCamera),
                const SizedBox(height: 16),
                IconButton(icon: const Icon(Icons.auto_awesome, color: Colors.white, size: 28), onPressed: () {}),
                const SizedBox(height: 16),
                IconButton(
                  icon: const Icon(Icons.photo_library, color: Colors.white, size: 28),
                  onPressed: () async {
                    final picker = ImagePicker();
                    final file = await picker.pickVideo(source: ImageSource.gallery);
                    if (file != null && mounted) {
                      context.push('/create/trim', extra: {'videoPath': file.path, 'maxDuration': _selectedDuration});
                    }
                  },
                ),
              ],
            ),
          ),

          // Bottom record
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Column(
              children: [
                if (_isRecording)
                  const LinearProgressIndicator(
                    valueColor: AlwaysStoppedAnimation(Colors.red),
                    backgroundColor: Colors.white24,
                  ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(color: Colors.grey.shade800, borderRadius: BorderRadius.circular(8)),
                      child: const Icon(Icons.photo, color: Colors.white70),
                    ),
                    const SizedBox(width: 24),
                    GestureDetector(
                      onTap: _toggleRecording,
                      child: Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: _isRecording ? Colors.red : Colors.white, width: 4),
                        ),
                        child: Center(
                          child: Container(
                            width: _isRecording ? 28 : 56,
                            height: _isRecording ? 28 : 56,
                            decoration: BoxDecoration(
                              color: _isRecording ? Colors.red : Colors.white,
                              shape: _isRecording ? BoxShape.rectangle : BoxShape.circle,
                              borderRadius: _isRecording ? BorderRadius.circular(4) : null,
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 24),
                    const Icon(Icons.more_horiz, color: Colors.white70, size: 28),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
