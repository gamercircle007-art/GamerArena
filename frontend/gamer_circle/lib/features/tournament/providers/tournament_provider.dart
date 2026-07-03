import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/tournament.dart';

final tournamentProvider =
    AsyncNotifierProviderFamily<TournamentNotifier, Tournament, String>(
  TournamentNotifier.new,
);

class TournamentNotifier extends FamilyAsyncNotifier<Tournament, String> {
  @override
  Future<Tournament> build(String arg) async {
    return ref.read(socialApiProvider).fetchTournament(arg);
  }

  void updateSlots(int bookedSlots) {
    final current = state.valueOrNull;
    if (current == null) return;
    final status = bookedSlots >= current.totalSlots ? 'full' : current.status;
    state = AsyncData(current.copyWith(bookedSlots: bookedSlots, status: status));
  }
}