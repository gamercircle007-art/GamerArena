import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/home/presentation/widgets/location_picker_sheet.dart';
import 'package:gamer_circle/features/home/presentation/widgets/profile_menu_button.dart';
import 'package:gamer_circle/features/home/providers/home_provider.dart';
import 'package:gamer_circle/features/home/providers/selected_location_provider.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

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

    final hubs = home.data.nearbyParlours.isNotEmpty
        ? home.data.nearbyParlours
        : _demoHubs;
    final picks = home.data.featuredParlours.isNotEmpty
        ? home.data.featuredParlours
        : _demoPicks;

    return Scaffold(
      backgroundColor: Colors.white,
      body: RefreshIndicator(
        color: OnboardingColors.primary,
        onRefresh: () => ref.read(homeProvider.notifier).refresh(),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: _HomeHeader(
                locationLabel: ref.watch(selectedLocationProvider).valueOrNull?.label ??
                    home.data.locationLabel,
                coinBalance: home.data.gcPoints?.balance ?? 200,
                displayName: displayName,
              ),
            ),
            SliverToBoxAdapter(child: _BookTableHero(onTap: () => context.push('/search-input'))),
            SliverToBoxAdapter(
              child: _HubSection(
                hubs: hubs,
                isLoading: home.isLoading,
                onHubTap: (hub) => context.push('/parlour/${hub.id}/detail'),
              ),
            ),
            SliverToBoxAdapter(
              child: _PickSection(
                name: displayName,
                picks: picks,
                onTap: (item) => context.push('/parlour/${item.id}/detail'),
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
            color: const Color(0xFFF5F5F5),
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

class _BookTableHero extends StatelessWidget {
  const _BookTableHero({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      height: 220,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF4A9FF5), Color(0xFFE8F4FD)],
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            left: 16,
            top: 24,
            child: _FoodPlate(emoji: '🍮', size: 72),
          ),
          Positioned(
            right: 16,
            top: 20,
            child: _FoodPlate(emoji: '🍰', size: 80),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 48,
            child: Center(child: _FoodPlate(emoji: '🍮', size: 90)),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 20,
            child: Center(
              child: Material(
                color: OnboardingColors.homeBlue,
                borderRadius: BorderRadius.circular(24),
                elevation: 4,
                child: InkWell(
                  onTap: onTap,
                  borderRadius: BorderRadius.circular(24),
                  child: const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 28, vertical: 12),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('🌸', style: TextStyle(fontSize: 14)),
                        SizedBox(width: 8),
                        Text(
                          'Book a Table',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 15,
                          ),
                        ),
                        SizedBox(width: 4),
                        Icon(Icons.arrow_forward, color: Colors.white, size: 18),
                        SizedBox(width: 8),
                        Text('🌸', style: TextStyle(fontSize: 14)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FoodPlate extends StatelessWidget {
  const _FoodPlate({required this.emoji, required this.size});

  final String emoji;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      alignment: Alignment.center,
      child: Text(emoji, style: TextStyle(fontSize: size * 0.45)),
    );
  }
}

class _HubSection extends StatelessWidget {
  const _HubSection({
    required this.hubs,
    required this.isLoading,
    required this.onHubTap,
  });

  final List<ParlourSearchItem> hubs;
  final bool isLoading;
  final ValueChanged<ParlourSearchItem> onHubTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Text(
            'Explore Hubs Near You',
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w800,
              color: OnboardingColors.textPrimary,
            ),
          ),
        ),
        SizedBox(
          height: 210,
          child: isLoading && hubs.isEmpty
              ? const Center(child: CircularProgressIndicator(color: OnboardingColors.primary))
              : ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: hubs.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 12),
                  itemBuilder: (_, i) => _HubCard(
                    hub: hubs[i],
                    onTap: () => onHubTap(hubs[i]),
                  ),
                ),
        ),
      ],
    );
  }
}

class _HubCard extends StatelessWidget {
  const _HubCard({required this.hub, required this.onTap});

  final ParlourSearchItem hub;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final restaurantCount = (hub.reviewCount % 20) + 5;
    return SizedBox(
      width: 200,
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        elevation: 2,
        shadowColor: Colors.black.withOpacity(0.08),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                child: hub.imageUrl != null
                    ? CachedNetworkImage(
                        imageUrl: hub.imageUrl!,
                        height: 110,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorWidget: (_, __, ___) => _hubPlaceholder(),
                      )
                    : _hubPlaceholder(),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      hub.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                        color: OnboardingColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      hub.distanceLabel.isNotEmpty
                          ? hub.distanceLabel
                          : '${(3.5 + hub.id.hashCode % 20 / 10).toStringAsFixed(1)} Kms',
                      style: const TextStyle(
                        fontSize: 12,
                        color: OnboardingColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'View $restaurantCount Restaurants',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: OnboardingColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _hubPlaceholder() {
    return Container(
      height: 110,
      width: double.infinity,
      color: const Color(0xFFE8E8E8),
      child: const Icon(Icons.storefront, color: OnboardingColors.textSecondary),
    );
  }
}

class _PickSection extends StatelessWidget {
  const _PickSection({
    required this.name,
    required this.picks,
    required this.onTap,
  });

  final String name;
  final List<ParlourSearchItem> picks;
  final ValueChanged<ParlourSearchItem> onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
          child: Text(
            '$name, What\'s Your Pick?',
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w800,
              color: OnboardingColors.textPrimary,
            ),
          ),
        ),
        ...picks.take(3).map(
              (item) => ListTile(
                onTap: () => onTap(item),
                leading: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: item.imageUrl != null
                      ? CachedNetworkImage(
                          imageUrl: item.imageUrl!,
                          width: 52,
                          height: 52,
                          fit: BoxFit.cover,
                        )
                      : Container(
                          width: 52,
                          height: 52,
                          color: const Color(0xFFE8E8E8),
                          child: const Icon(Icons.restaurant),
                        ),
                ),
                title: Text(
                  item.name,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                subtitle: Text(
                  item.locationLine.isNotEmpty
                      ? item.locationLine
                      : 'Great food & ambience',
                  style: const TextStyle(fontSize: 12),
                ),
                trailing: item.rating != null
                    ? Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1A7A4A),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '${item.rating!.toStringAsFixed(1)} ★',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      )
                    : null,
              ),
            ),
      ],
    );
  }
}

final List<ParlourSearchItem> _demoHubs = [
  const ParlourSearchItem(
    id: 'hub-1',
    name: 'Indirapuram Habitat ...',
    imageUrl: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400',
    distanceMeters: 4000,
    reviewCount: 5,
  ),
  const ParlourSearchItem(
    id: 'hub-2',
    name: 'Vaishali',
    imageUrl: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400',
    distanceMeters: 4700,
    reviewCount: 20,
  ),
  const ParlourSearchItem(
    id: 'hub-3',
    name: 'Crossing Republik',
    imageUrl: 'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400',
    distanceMeters: 6200,
    reviewCount: 12,
  ),
];

final List<ParlourSearchItem> _demoPicks = [
  const ParlourSearchItem(
    id: 'pick-1',
    name: 'The Spice Route',
    imageUrl: 'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=200',
    rating: 4.5,
    city: 'Ghaziabad',
  ),
  const ParlourSearchItem(
    id: 'pick-2',
    name: 'Cafe Mocha Lounge',
    imageUrl: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=200',
    rating: 4.2,
    city: 'Noida',
  ),
];