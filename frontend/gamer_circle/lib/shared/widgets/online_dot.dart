import 'package:flutter/material.dart';

enum OnlineDotSize { small, medium, large }

class OnlineDot extends StatefulWidget {
  const OnlineDot({
    super.key,
    required this.isOnline,
    this.size = OnlineDotSize.small,
    this.pulse = false,
  });

  final bool isOnline;
  final OnlineDotSize size;
  final bool pulse;

  @override
  State<OnlineDot> createState() => _OnlineDotState();
}

class _OnlineDotState extends State<OnlineDot> with SingleTickerProviderStateMixin {
  AnimationController? _controller;

  @override
  void initState() {
    super.initState();
    if (widget.pulse && widget.isOnline) {
      _controller = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 1200),
      )..repeat();
    }
  }

  @override
  void didUpdateWidget(OnlineDot oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.pulse && widget.isOnline && _controller == null) {
      _controller = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 1200),
      )..repeat();
    } else if ((!widget.pulse || !widget.isOnline) && _controller != null) {
      _controller!.dispose();
      _controller = null;
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  double get _dimension => switch (widget.size) {
        OnlineDotSize.small => 8,
        OnlineDotSize.medium => 12,
        OnlineDotSize.large => 16,
      };

  @override
  Widget build(BuildContext context) {
    final dot = Container(
      width: _dimension,
      height: _dimension,
      decoration: BoxDecoration(
        color: widget.isOnline ? const Color(0xFF28C76F) : const Color(0xFFBDBDBD),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 1.5),
      ),
    );

    if (_controller == null) return dot;

    return AnimatedBuilder(
      animation: _controller!,
      builder: (_, child) {
        final scale = 1.0 + (_controller!.value * 0.35);
        return Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: _dimension * scale,
              height: _dimension * scale,
              decoration: BoxDecoration(
                color: const Color(0xFF28C76F).withOpacity(0.25),
                shape: BoxShape.circle,
              ),
            ),
            child!,
          ],
        );
      },
      child: dot,
    );
  }
}