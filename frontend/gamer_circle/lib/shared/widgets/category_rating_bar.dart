import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:percent_indicator/linear_percent_indicator.dart';

class CategoryRatingBar extends StatelessWidget {
  const CategoryRatingBar({
    super.key,
    required this.label,
    required this.rating,
    this.maxRating = 5,
  });

  final String label;
  final double rating;
  final double maxRating;

  @override
  Widget build(BuildContext context) {
    final percent = (rating / maxRating).clamp(0.0, 1.0);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: BookingColors.textSecondary,
              ),
            ),
          ),
          Expanded(
            child: LinearPercentIndicator(
              lineHeight: 8,
              percent: percent,
              backgroundColor: BookingColors.background,
              progressColor: const Color(0xFFF59E0B),
              barRadius: const Radius.circular(4),
              padding: EdgeInsets.zero,
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 28,
            child: Text(
              rating.toStringAsFixed(1),
              textAlign: TextAlign.end,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: BookingColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class CategoryRatingsSection extends StatelessWidget {
  const CategoryRatingsSection({
    super.key,
    required this.ratings,
    this.title = 'Category Ratings',
  });

  final Map<String, double> ratings;
  final String title;

  @override
  Widget build(BuildContext context) {
    if (ratings.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            color: BookingColors.textPrimary,
          ),
        ),
        const SizedBox(height: 8),
        ...ratings.entries.map(
          (e) => CategoryRatingBar(label: e.key, rating: e.value),
        ),
      ],
    );
  }
}