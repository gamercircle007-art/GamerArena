import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

class ParlorSearchSkeleton extends StatelessWidget {
  const ParlorSearchSkeleton({super.key, this.count = 4});

  final int count;

  @override
  Widget build(BuildContext context) {
    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (_, index) => Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 14),
          child: Shimmer.fromColors(
            baseColor: const Color(0xFFE5E7EB),
            highlightColor: const Color(0xFFF9FAFB),
            child: Container(
              height: 220,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
        ),
        childCount: count,
      ),
    );
  }
}