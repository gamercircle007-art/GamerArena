import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/home/presentation/widgets/city_filter_rail.dart';
import 'package:gamer_circle/features/home/presentation/widgets/home_posts_rail.dart';
import 'package:gamer_circle/features/home/presentation/widgets/location_picker_sheet.dart';
import 'package:gamer_circle/features/home/presentation/widgets/profile_menu_button.dart';
import 'package:gamer_circle/features/home/presentation/widgets/nearby_parlors_section.dart';
import 'package:gamer_circle/features/home/presentation/widgets/quick_picks_section.dart';
import 'package:gamer_circle/features/home/providers/home_filters_provider.dart';
import 'package:gamer_circle/features/home/providers/home_provider.dart';
import 'package:gamer_circle/features/home/providers/selected_location_provider.dart';


class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(homeProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final home = ref.watch(homeProvider);
    final auth = ref.watch(authNotifierProvider);
    final displayName = switch (auth) {
      AuthAuthenticated(:final user) => user.username,
      _ => 'Guest',
    };

    final selectedCity = ref.watch(homeSelectedCityProvider);
    final quickPickFilter = ref.watch(homeQuickPickFilterProvider);
    final radiusFilter = ref.watch(homeRadiusFilterProvider);
    final quickPicks = home.data.quickPickParlours;
    final allParlors = home.data.allParlours;

    return ColoredBox(
      color: Colors.white,
      child: RefreshIndicator(
        color: OnboardingColors.primary,
        onRefresh: () => ref.read(homeProvider.notifier).refresh(),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            if (home.error != null)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                  child: Material(
                    color: const Color(0xFFFFF3F3),
                    borderRadius: BorderRadius.circular(10),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          const Icon(Icons.cloud_off, color: Color(0xFFB91C1C), size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Could not load parlors: ${home.error}',
                              style: const TextStyle(
                                color: Color(0xFFB91C1C),
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            SliverToBoxAdapter(
              child: _HomeHeader(
                locationLabel: ref.watch(selectedLocationProvider).valueOrNull?.label ??
                    home.data.locationLabel,
                coinBalance: home.data.gcPoints?.balance ?? 200,
                displayName: displayName,
              ),
            ),
            SliverToBoxAdapter(
              child: HomePostsRail(
                posts: home.data.posts,
                isLoading: home.isLoading,
                onPostTap: (post) =>
                    context.push('/posts/${post.id}/comments'),
                onSeeAllTap: () => context.push('/feed'),
              ),
            ),
            SliverToBoxAdapter(
              child: CityFilterRail(
                cities: home.data.cities.isNotEmpty
                    ? home.data.cities
                    : fallbackHomeCities,
                selectedCity: selectedCity,
                onNearbyTap: () {
                  ref.read(homeSelectedCityProvider.notifier).state = null;
                  ref.read(homeProvider.notifier).load();
                },
                onCityTap: (city) {
                  ref.read(homeSelectedCityProvider.notifier).state = city;
                  ref.read(homeProvider.notifier).load();
                },
              ),
            ),
            SliverToBoxAdapter(
              child: NearbyParlorsSection(
                parlours: allParlors,
                selectedRadius: radiusFilter,
                isLoading: home.isLoading,
                onRadiusChanged: (filter) {
                  ref.read(homeRadiusFilterProvider.notifier).state = filter;
                  ref.read(homeProvider.notifier).load();
                },
                onParlourTap: (item) =>
                    context.push('/parlour/${item.id}/detail'),
              ),
            ),
            SliverToBoxAdapter(
              child: QuickPicksSection(
                parlours: quickPicks,
                selectedFilter: quickPickFilter,
                isLoading: home.isLoading,
                onFilterChanged: (filter) {
                  ref.read(homeQuickPickFilterProvider.notifier).state = filter;
                  ref.read(homeProvider.notifier).load();
                },
                onParlourTap: (item) =>
                    context.push('/parlour/${item.id}/detail'),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: 100)),
          ],
        ),
      ),
    );
  }
}

class _HomeHeader extends ConsumerWidget {
  const _HomeHeader({
    required this.locationLabel,
    required this.coinBalance,
    required this.displayName,
  });

  final String locationLabel;
  final int coinBalance;
  final String displayName;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final label = locationLabel == 'Select location' ||
            locationLabel == 'Around you' ||
            locationLabel.isEmpty
        ? 'Khora Colony, Ghaziabad'
        : locationLabel;

    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 52, 16, 12),
      child: Column(
        children: [
          Row(
            children: [
              Builder(
                builder: (context) => IconButton(
                  onPressed: () => Scaffold.of(context).openDrawer(),
                  icon: const Icon(Icons.menu_rounded),
                  color: OnboardingColors.textPrimary,
                  tooltip: 'Menu',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                ),
              ),
              Expanded(
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () => showLocationPickerSheet(context, ref),
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.location_on,
                            color: OnboardingColors.primary,
                            size: 18,
                          ),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              label,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: OnboardingColors.textPrimary,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const Icon(
                            Icons.keyboard_arrow_down,
                            size: 20,
                            color: OnboardingColors.textPrimary,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              _CoinBadge(balance: coinBalance),
              const SizedBox(width: 8),
              ProfileMenuButton(displayName: displayName),
            ],
          ),
          const SizedBox(height: 14),
          Material(
            color: AppColors.backgroundLight,
            borderRadius: BorderRadius.circular(28),
            child: InkWell(
              onTap: () => context.push('/search-input'),
              borderRadius: BorderRadius.circular(28),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                child: const Row(
                  children: [
                    Icon(Icons.search, color: OnboardingColors.textSecondary, size: 22),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Search restaurants, locations or cuisines',
                        style: TextStyle(
                          color: OnboardingColors.textSecondary,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CoinBadge extends StatelessWidget {
  const _CoinBadge({required this.balance});

  final int balance;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: OnboardingColors.walletGold.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 20,
            height: 20,
            decoration: const BoxDecoration(
              color: OnboardingColors.walletGold,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.monetization_on, color: Colors.white, size: 14),
          ),
          const SizedBox(width: 4),
          Text(
            '$balance',
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 13,
              color: OnboardingColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}

