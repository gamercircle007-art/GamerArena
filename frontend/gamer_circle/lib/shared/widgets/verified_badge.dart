import 'package:flutter/material.dart';

class VerifiedBadge extends StatelessWidget {
  const VerifiedBadge({super.key, this.size = 16});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: const BoxDecoration(
        color: Colors.deepPurple,
        shape: BoxShape.circle,
      ),
      child: Icon(Icons.check, size: size * 0.65, color: Colors.white),
    );
  }
}