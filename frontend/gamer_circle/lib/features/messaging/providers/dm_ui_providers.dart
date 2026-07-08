import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Simple UI model for the horizontal "Notes / Highlights" row (adapted to gaming/parlor theme)
class DmNote {
  const DmNote({
    required this.id,
    required this.label,
    required this.imageUrl,
    this.emoji,
    this.subtitle,
  });

  final String id;
  final String label;
  final String imageUrl;
  final String? emoji;
  final String? subtitle;
}

/// Suggested contact for New Message screen (matches IG style)
class SuggestedContact {
  const SuggestedContact({
    required this.id,
    required this.name,
    this.username,
    this.avatarUrl,
    this.isVerified = false,
    this.isAI = false,
    this.lastActive,
  });

  final String id;
  final String name;
  final String? username;
  final String? avatarUrl;
  final bool isVerified;
  final bool isAI;
  final String? lastActive;

  SuggestedContact copyWith({bool? isAI}) => SuggestedContact(
        id: id,
        name: name,
        username: username,
        avatarUrl: avatarUrl,
        isVerified: isVerified,
        isAI: isAI ?? this.isAI,
        lastActive: lastActive,
      );
}

/// Tab filter for main inbox
enum DmTab { primary, requests, general }

/// Provider: horizontal notes / parlor highlights (mock, gaming themed)
final dmNotesProvider = Provider<List<DmNote>>((ref) {
  return const [
    DmNote(
      id: 'n1',
      label: "Today's vibe",
      imageUrl: 'https://picsum.photos/id/1011/200/200',
      emoji: '🎮',
      subtitle: '2x XP',
    ),
    DmNote(
      id: 'n2',
      label: 'Island mode',
      imageUrl: 'https://picsum.photos/id/1005/200/200',
      emoji: '🏝️',
    ),
    DmNote(
      id: 'n3',
      label: 'White Room',
      imageUrl: 'https://picsum.photos/id/106/200/200',
      emoji: '🎧',
    ),
    DmNote(
      id: 'n4',
      label: 'Method Man',
      imageUrl: 'https://picsum.photos/id/201/200/200',
      emoji: '🔥',
    ),
    DmNote(
      id: 'n5',
      label: 'New sticks',
      imageUrl: 'https://picsum.photos/id/180/200/200',
      subtitle: 'Parlor',
    ),
  ];
});

/// State for removed suggested ids
class SuggestedState {
  const SuggestedState({required this.all, required this.removedIds});

  final List<SuggestedContact> all;
  final Set<String> removedIds;

  List<SuggestedContact> get visible =>
      all.where((c) => !removedIds.contains(c.id)).toList();
}

class SuggestedNotifier extends Notifier<SuggestedState> {
  @override
  SuggestedState build() {
    // Curated list styled after the reference screenshots (mix of users + AI + gaming handles)
    final all = <SuggestedContact>[
      const SuggestedContact(
        id: 'ai-meta',
        name: 'Meta AI',
        username: 'AI',
        avatarUrl: null, // special handling for purple flower icon
        isAI: true,
        isVerified: true,
      ),
      const SuggestedContact(
        id: 'u1',
        name: 'heyitssheera',
        username: 'heyitssheera',
        avatarUrl: 'https://picsum.photos/id/1009/200/200',
      ),
      const SuggestedContact(
        id: 'u2',
        name: 'tnu.agrwl',
        username: 'tnu.agrwl',
        avatarUrl: 'https://picsum.photos/id/1006/200/200',
      ),
      const SuggestedContact(
        id: 'u3',
        name: 'SHEERA',
        username: 'fitnes_with_joy',
        avatarUrl: 'https://picsum.photos/id/1012/200/200',
      ),
      const SuggestedContact(
        id: 'u4',
        name: 'aell photography',
        username: '_naturephotogallery_',
        avatarUrl: 'https://picsum.photos/id/251/200/200',
      ),
      const SuggestedContact(
        id: 'u5',
        name: 'manish kumar',
        username: 'lightweaver',
        avatarUrl: 'https://picsum.photos/id/1008/200/200',
        isVerified: true,
      ),
      const SuggestedContact(
        id: 'u6',
        name: 'Rimlina Hazarika',
        username: 'rimsplayz',
        avatarUrl: 'https://picsum.photos/id/64/200/200',
      ),
      const SuggestedContact(
        id: 'u7',
        name: 'LevelUp Lounge',
        username: 'levelup_parlor',
        avatarUrl: 'https://picsum.photos/id/160/200/200',
      ),
    ];
    return SuggestedState(all: all, removedIds: {});
  }

  void remove(String id) {
    final current = state;
    state = SuggestedState(
      all: current.all,
      removedIds: {...current.removedIds, id},
    );
  }

  void restoreAll() {
    state = SuggestedState(all: state.all, removedIds: {});
  }
}

final suggestedNotifierProvider =
    NotifierProvider<SuggestedNotifier, SuggestedState>(SuggestedNotifier.new);

/// Search query for new message suggested list (live filter)
final newMessageSearchProvider = StateProvider<String>((ref) => '');

/// Filtered suggested list (reactive to search + removed)
final filteredSuggestedProvider = Provider<List<SuggestedContact>>((ref) {
  final s = ref.watch(suggestedNotifierProvider);
  final q = ref.watch(newMessageSearchProvider).toLowerCase().trim();

  final visible = s.visible;
  if (q.isEmpty) return visible;

  return visible.where((c) {
    final name = c.name.toLowerCase();
    final user = (c.username ?? '').toLowerCase();
    return name.contains(q) || user.contains(q);
  }).toList();
});

/// Selected tab for main inbox (Primary / Requests / General)
final dmSelectedTabProvider = StateProvider<DmTab>((ref) => DmTab.primary);

/// Optional search on main inbox (the big search bar)
final dmInboxSearchProvider = StateProvider<String>((ref) => '');

/// Convenience: current selected tab + search query (for screen consumption)
final dmTabAndQueryProvider = Provider<({DmTab tab, String query})>((ref) {
  return (
    tab: ref.watch(dmSelectedTabProvider),
    query: ref.watch(dmInboxSearchProvider),
  );
});