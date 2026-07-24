import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key, this.userName});

  final String? userName;

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 4,
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: List.generate(3, (i) {
              return AnimatedBuilder(
                animation: _controller,
                builder: (_, __) {
                  final t = (_controller.value + i * 0.2) % 1.0;
                  final opacity = 0.3 + (t < 0.5 ? t * 1.4 : (1 - t) * 1.4);
                  return Container(
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(opacity),
                      shape: BoxShape.circle,
                    ),
                  );
                },
              );
            }),
          ),
        ),
        if (widget.userName != null) ...[
          const SizedBox(width: 8),
          Text(
            '${widget.userName} is typing...',
            style: const TextStyle(fontSize: 11, color: AppColors.textSecondaryLight),
          ),
        ],
      ],
    );
  }
}