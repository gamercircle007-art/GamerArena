import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

/// Booking flow palette — shared tokens from [AppColors].
class BookingColors {
  BookingColors._();

  static const Color oyoRed = AppColors.error;
  static const Color confirmedGreen = AppColors.success;
  static const Color cancelledOrange = AppColors.primaryDark;

  static const Color textPrimary = AppColors.textPrimaryLight;
  static const Color textSecondary = AppColors.textSecondaryLight;
  static const Color border = AppColors.borderLight;
  static const Color background = AppColors.backgroundLight;
}