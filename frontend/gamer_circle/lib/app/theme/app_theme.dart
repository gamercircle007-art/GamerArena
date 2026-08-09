import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_text_styles.dart';
import 'app_spacing.dart';

/// This is the file that actually wires everything into the app.
/// Wire it in main.dart:
///   MaterialApp(
///     theme: AppTheme.light,
///     darkTheme: AppTheme.dark,
///     themeMode: ThemeMode.system, // or .light / .dark to force one
///     ...
///   )
///
/// After that, every screen should read styling via `Theme.of(context)` —
/// never re-import AppColors/AppTextStyles directly inside widgets unless
/// you need a value with no ThemeData equivalent (rare).
class AppTheme {
  AppTheme._();

  static ThemeData get light => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        scaffoldBackgroundColor: AppColors.backgroundLight,
        colorScheme: const ColorScheme.light(
          primary: AppColors.primary,
          secondary: AppColors.secondary,
          surface: AppColors.surfaceLight,
          error: AppColors.error,
          onPrimary: Colors.white,
          onSecondary: Colors.white,
          onSurface: AppColors.textPrimaryLight,
          onError: Colors.white,
        ),
        textTheme: _textTheme(AppColors.textPrimaryLight),
        appBarTheme: AppBarTheme(
          backgroundColor: AppColors.surfaceLight,
          foregroundColor: AppColors.textPrimaryLight,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: AppTextStyles.headlineSmall.copyWith(
            color: AppColors.textPrimaryLight,
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: Colors.white,
            minimumSize: const Size.fromHeight(AppSpacing.buttonHeight),
            textStyle: AppTextStyles.labelLarge,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: AppColors.primary,
            side: const BorderSide(color: AppColors.primary),
            minimumSize: const Size.fromHeight(AppSpacing.buttonHeight),
            textStyle: AppTextStyles.labelLarge,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: AppColors.surfaceLight,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.sm,
          ),
          hintStyle: TextStyle(color: AppColors.textSecondaryLight),
          labelStyle: TextStyle(color: AppColors.textSecondaryLight),
          floatingLabelStyle: TextStyle(color: AppColors.primary),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.borderLight),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.borderLight),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.error),
          ),
        ),
        textSelectionTheme: const TextSelectionThemeData(
          cursorColor: AppColors.primary,
          selectionColor: Color(0x334F46E5),
          selectionHandleColor: AppColors.primary,
        ),
        cardTheme: CardThemeData(
          color: AppColors.surfaceLight,
          elevation: 1,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          ),
        ),
        dividerTheme: const DividerThemeData(
          color: AppColors.borderLight,
          thickness: 1,
        ),
      );

  static ThemeData get dark => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.backgroundDark,
        colorScheme: const ColorScheme.dark(
          primary: AppColors.primaryLight,
          secondary: AppColors.secondaryLight,
          surface: AppColors.surfaceDark,
          error: AppColors.error,
          onPrimary: AppColors.textPrimaryDark,
          onSecondary: AppColors.textPrimaryDark,
          onSurface: AppColors.textPrimaryDark,
          onError: Colors.white,
        ),
        textTheme: _textTheme(AppColors.textPrimaryDark),
        appBarTheme: AppBarTheme(
          backgroundColor: AppColors.surfaceDark,
          foregroundColor: AppColors.textPrimaryDark,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: AppTextStyles.headlineSmall.copyWith(
            color: AppColors.textPrimaryDark,
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primaryLight,
            foregroundColor: AppColors.backgroundDark,
            minimumSize: const Size.fromHeight(AppSpacing.buttonHeight),
            textStyle: AppTextStyles.labelLarge,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: AppColors.primaryLight,
            side: const BorderSide(color: AppColors.primaryLight),
            minimumSize: const Size.fromHeight(AppSpacing.buttonHeight),
            textStyle: AppTextStyles.labelLarge,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: AppColors.surfaceDark,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: AppSpacing.sm,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.borderDark),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.borderDark),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.primaryLight, width: 1.5),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            borderSide: const BorderSide(color: AppColors.error),
          ),
        ),
        cardTheme: CardThemeData(
          color: AppColors.surfaceDark,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          ),
        ),
        dividerTheme: const DividerThemeData(
          color: AppColors.borderDark,
          thickness: 1,
        ),
      );

  static TextTheme _textTheme(Color baseColor) {
    return TextTheme(
      displayLarge: AppTextStyles.displayLarge.copyWith(color: baseColor),
      headlineMedium: AppTextStyles.headlineMedium.copyWith(color: baseColor),
      headlineSmall: AppTextStyles.headlineSmall.copyWith(color: baseColor),
      bodyLarge: AppTextStyles.bodyLarge.copyWith(color: baseColor),
      bodyMedium: AppTextStyles.bodyMedium.copyWith(color: baseColor),
      bodySmall: AppTextStyles.bodySmall.copyWith(color: baseColor),
      labelLarge: AppTextStyles.labelLarge.copyWith(color: baseColor),
      labelSmall: AppTextStyles.labelSmall.copyWith(color: baseColor),
    );
  }
}
