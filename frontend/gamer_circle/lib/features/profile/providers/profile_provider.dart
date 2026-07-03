import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/profile/data/profile_repository.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(ref.watch(dioProvider));
});

final publicProfileProvider =
    FutureProvider.family<PublicProfile, String>((ref, userId) {
  return ref.read(profileRepositoryProvider).getUserProfile(userId);
});