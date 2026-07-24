import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/home/presentation/widgets/landing_promo_card.dart';
import 'package:gamer_circle/features/home/presentation/widgets/location_permission_banner.dart';
import 'package:gamer_circle/features/home/presentation/widgets/parlor_filter_chips.dart';
import 'package:gamer_circle/features/home/presentation/widgets/parlor_result_card.dart';
import 'package:gamer_circle/features/home/presentation/widgets/parlor_search_skeleton.dart';
import 'package:gamer_circle/features/home/providers/parlor_search_provider.dart';

class LandingPage extends ConsumerStatefulWidget {
  const LandingPage({super.key});

  @override
  ConsumerState<LandingPage> createState() => _LandingPageState();
}

class _LandingPageState extends ConsumerState<LandingPage> {
  final _searchController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(parlorSearchProvider.notifier).initialize(),
    );
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(parlorSearchProvider.notifier).loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authNotifierProvider);
    final search = ref.watch(parlorSearchProvider);
    final greeting = switch (user) {
      AuthAuthenticated(:final user) => user.username,
      _ => 'Gamer',
    };

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () => ref.read(parlorSearchProvider.notifier).refresh(),
        color: AppColors.primary,
        child: CustomScrollView(
          controller: _scrollController,
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(8, 12, 12, 0),
                child: Row(
                  children: [
                    Builder(
                      builder: (context) => IconButton(
                        onPressed: () => Scaffold.of(context).openDrawer(),
                        icon: const Icon(Icons.menu_rounded),
                        color: AppColors.textPrimary,
                        tooltip: 'Menu',
                      ),
                    ),
                    ShaderMask(
                      shaderCallback: (bounds) => const LinearGradient(
                        colors: [AppColors.primary, AppColors.secondary],
                      ).createShader(bounds),
                      child: const Text(
                        'GAMER CIRCLE',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                          letterSpacing: -0.5,
                        ),
                      ),
                    ),
                    const Spacer(),
                    IconButton(
                      onPressed: () => context.push('/discover'),
                      icon: const Icon(Icons.map_outlined),
                      color: AppColors.textPrimary,
                      tooltip: 'Map',
                    ),
                  ],
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Hey $greeting,',
                      style: const TextStyle(
                        fontSize: 15,
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Find gaming parlors\nnear you',
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                        height: 1.2,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 20)),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: TextField(
                  controller: _searchController,
                  onChanged: (v) =>
                      ref.read(parlorSearchProvider.notifier).setQuery(v),
                  decoration: InputDecoration(
                    hintText: 'Search parlors, area, city, state…',
                    prefixIcon: const Icon(Icons.search_rounded),
                    suffixIcon: search.isSearching
                        ? const Padding(
                            padding: EdgeInsets.all(12),
                            child: SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          )
                        : (search.filters.query.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear),
                                onPressed: () {
                                  _searchController.clear();
                                  ref
                                      .read(parlorSearchProvider.notifier)
                                      .setQuery('');
                                },
                              )
                            : null),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide:
                          const BorderSide(color: AppColors.divider),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide:
                          const BorderSide(color: AppColors.divider),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(
                        color: AppColors.primary,
                        width: 1.5,
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 12)),
            SliverToBoxAdapter(
              child: ParlorFilterChips(
                filters: search.filters,
                onChanged: (f) =>
                    ref.read(parlorSearchProvider.notifier).updateFilters(f),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 8)),
            if (search.locationDenied)
              SliverToBoxAdapter(
                child: LocationPermissionBanner(
                  onEnableLocation: () =>
                      ref.read(parlorSearchProvider.notifier).initialize(),
                  onCitySelected: (city) => ref
                      .read(parlorSearchProvider.notifier)
                      .setManualCity(city),
                ),
              ),
            if (search.error != null)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Text(
                    search.error!,
                    style: const TextStyle(color: Color(0xFFEF4444)),
                  ),
                ),
              ),
            if (search.isLoading)
              const ParlorSearchSkeleton()
            else if (!search.locationDenied && search.parlors.isEmpty)
              SliverFillRemaining(
                hasScrollBody: false,
                child: _EmptyState(
                  hasQuery: search.filters.query.isNotEmpty ||
                      search.filters.minRating != null ||
                      search.filters.openNow,
                ),
              )
            else ...[
              SliverToBoxAdapter(
                child: Padding(
                  padding:
                      const EdgeInsets.fromLTRB(20, 8, 20, 12),
                  child: Text(
                    search.total > 0
                        ? '${search.total} parlors nearby'
                        : 'Nearby parlors',
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
              ),
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) =>
                      ParlorResultCard(parlor: search.parlors[index]),
                  childCount: search.parlors.length,
                ),
              ),
              if (search.isLoadingMore)
                const SliverToBoxAdapter(
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ),
            ],
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => context.push('/feed'),
                        icon: const Icon(Icons.dynamic_feed_outlined),
                        label: const Text('Gamer Feed'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => context.push('/discover'),
                        icon: const Icon(Icons.map_outlined),
                        label: const Text('Discover'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.only(top: 24, bottom: 32),
                child: LandingPromoCard(
                  onTap: () => context.push('/discover'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.hasQuery});

  final bool hasQuery;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              hasQuery ? Icons.search_off_rounded : Icons.videogame_asset_off,
              size: 56,
              color: const Color(0xFFD1D5DB),
            ),
            const SizedBox(height: 16),
            Text(
              hasQuery
                  ? 'No parlors match your search'
                  : 'No nearby gaming parlors found',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              hasQuery
                  ? 'Try a different keyword or widen your radius filter.'
                  : 'Expand your search radius or pick another city.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}