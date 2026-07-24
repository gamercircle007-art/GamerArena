import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/accept_location_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/check_location_onboarding_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/skip_location_usecase.dart';

/// Shows a one-time dialog to request location access (native prompt on Allow).
class LocationPermissionPrompt extends ConsumerStatefulWidget {
  final Widget? child;

  const LocationPermissionPrompt({super.key, required this.child});

  @override
  ConsumerState<LocationPermissionPrompt> createState() =>
      _LocationPermissionPromptState();
}

class _LocationPermissionPromptState
    extends ConsumerState<LocationPermissionPrompt> {
  bool _checked = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _promptIfNeeded());
  }

  Future<void> _promptIfNeeded() async {
    if (_checked) return;
    _checked = true;

    final checkResult =
        await getIt<CheckLocationOnboardingUseCase>()(NoParams());
    final alreadyHandled = checkResult.fold((_) => true, (completed) => completed);
    if (alreadyHandled || !mounted) return;

    final allow = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Allow location access?'),
        content: const Text(
          'Gamer Circle uses your location to find nearby gamers and sessions.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Not now'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
            ),
            child: const Text('Allow'),
          ),
        ],
      ),
    );

    if (!mounted) return;

    if (allow == true) {
      final result = await getIt<AcceptLocationUseCase>()(NoParams());
      result.fold(
        (failure) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(failure.message),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        (_) {},
      );
    } else {
      await getIt<SkipLocationUseCase>()(NoParams());
    }
  }

  @override
  Widget build(BuildContext context) => widget.child ?? const SizedBox.shrink();
}