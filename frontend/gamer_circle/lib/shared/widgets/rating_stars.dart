import 'package:flutter/material.dart';
import 'package:flutter_rating_bar/flutter_rating_bar.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';

class RatingStars extends StatelessWidget {
  const RatingStars({
    super.key,
    required this.rating,
    this.size = 16,
    this.showValue = false,
    this.interactive = false,
    this.onRatingUpdate,
  });

  final double rating;
  final double size;
  final bool showValue;
  final bool interactive;
  final ValueChanged<double>? onRatingUpdate;

  @override
  Widget build(BuildContext context) {
    final stars = RatingBarIndicator(
      rating: rating,
      itemBuilder: (_, __) => const Icon(
        Icons.star_rounded,
        color: Color(0xFFF59E0B),
      ),
      itemCount: 5,
      itemSize: size,
    );

    if (!interactive) {
      if (!showValue) return stars;
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          stars,
          const SizedBox(width: 4),
          Text(
            rating.toStringAsFixed(1),
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: BookingColors.textPrimary,
            ),
          ),
        ],
      );
    }

    return RatingBar.builder(
      initialRating: rating,
      minRating: 1,
      direction: Axis.horizontal,
      allowHalfRating: true,
      itemCount: 5,
      itemSize: size,
      itemBuilder: (_, __) => const Icon(
        Icons.star_rounded,
        color: Color(0xFFF59E0B),
      ),
      onRatingUpdate: onRatingUpdate ?? (_) {},
    );
  }
}