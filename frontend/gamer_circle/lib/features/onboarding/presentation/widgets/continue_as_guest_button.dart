import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';

class ContinueAsGuestButton extends StatelessWidget {
  const ContinueAsGuestButton({
    super.key,
    required this.onPressed,
    this.pillStyle = false,
  });

  final VoidCallback onPressed;
  final bool pillStyle;

  @override
  Widget build(BuildContext context) {
    if (pillStyle) {
      return Align(
        alignment: Alignment.centerRight,
        child: Material(
          color: OnboardingColors.guestPillBg,
          borderRadius: BorderRadius.circular(24),
          child: InkWell(
            onTap: onPressed,
            borderRadius: BorderRadius.circular(24),
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Continue as guest',
                    style: TextStyle(
                      color: OnboardingColors.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  SizedBox(width: 4),
                  Icon(
                    Icons.chevron_right,
                    size: 18,
                    color: OnboardingColors.textPrimary,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    return TextButton(
      onPressed: onPressed,
      style: TextButton.styleFrom(
        foregroundColor: OnboardingColors.primary,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      ),
      child: const Text(
        'Continue as guest',
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}