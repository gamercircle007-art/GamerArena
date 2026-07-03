import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';

class BookingBottomCta extends StatelessWidget {
  const BookingBottomCta({
    super.key,
    required this.price,
    this.originalPrice,
    this.label = 'Book Now',
    this.subtitle,
    this.onPressed,
    this.isLoading = false,
    this.enabled = true,
  });

  final double price;
  final double? originalPrice;
  final String label;
  final String? subtitle;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        16,
        12,
        16,
        12 + MediaQuery.paddingOf(context).bottom,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Text(
                        formatInr(price),
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: BookingColors.textPrimary,
                        ),
                      ),
                      if (originalPrice != null && originalPrice! > price) ...[
                        const SizedBox(width: 6),
                        Text(
                          formatInr(originalPrice!),
                          style: const TextStyle(
                            fontSize: 13,
                            decoration: TextDecoration.lineThrough,
                            color: BookingColors.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                  if (subtitle != null)
                    Text(
                      subtitle!,
                      style: const TextStyle(
                        fontSize: 12,
                        color: BookingColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 140,
              height: 48,
              child: FilledButton(
                onPressed: enabled && !isLoading ? onPressed : null,
                style: FilledButton.styleFrom(
                  backgroundColor: BookingColors.oyoRed,
                  disabledBackgroundColor:
                      BookingColors.oyoRed.withOpacity(0.4),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: isLoading
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Text(
                        label,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}