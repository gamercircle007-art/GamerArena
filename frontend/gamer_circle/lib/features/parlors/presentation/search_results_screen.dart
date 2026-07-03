import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/features/parlors/providers/parlor_search_provider.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';
import 'package:gamer_circle/shared/widgets/parlour_list_card.dart';

class SearchResultsScreen extends ConsumerStatefulWidget {
  const SearchResultsScreen({super.key});

  @override
  ConsumerState<SearchResultsScreen> createState() => _SearchResultsScreenState();
}

class _SearchResultsScreenState extends ConsumerState<SearchResultsScreen> {
  final _scrollController = ScrollController();
  final _queryController = TextEditingController();

  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initialized) return;
    _initialized = true;
    final uri = GoRouterState.of(context).uri;
    final under299 = uri.queryParameters['under299'] == 'true';
    final game = uri.queryParameters['game'];
    final filters = ParlourSearchFilters(
      under299: under299,
      gameType: game,
      query: uri.queryParameters['q'] ?? '',
    );
    Future.microtask(
      () => ref
          .read(parlourSearchProvider.notifier)
          .initialize(initialFilters: filters),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _queryController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(parlourSearchProvider.notifier).loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final search = ref.watch(parlourSearchProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(search.filters.under299 ? 'Under ₹299' : 'Search Results'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: () => context.push('/search-input'),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _queryController..text = search.filters.query,
              decoration: InputDecoration(
                hintText: 'Search parlours...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: search.filters.query.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _queryController.clear();
                          ref.read(parlourSearchProvider.notifier).setQuery('');
                        },
                      )
                    : null,
              ),
              onChanged: (v) =>
                  ref.read(parlourSearchProvider.notifier).setQuery(v),
            ),
          ),
          if (search.locationDenied)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  const Text('Location permission required'),
                  TextButton(
                    onPressed: () =>
                        ref.read(parlourSearchProvider.notifier).initialize(),
                    child: const Text('Enable location'),
                  ),
                ],
              ),
            ),
          Expanded(
            child: RefreshIndicator(
              color: BookingColors.oyoRed,
              onRefresh: () => ref.read(parlourSearchProvider.notifier).refresh(),
              child: search.isLoading && search.items.isEmpty
                  ? ListView.builder(
                      itemCount: 6,
                      itemBuilder: (_, __) => const ParlourListCardShimmer(),
                    )
                  : search.items.isEmpty
                      ? ListView(
                          children: const [
                            SizedBox(height: 80),
                            Center(
                              child: Text(
                                'No parlours found',
                                style: TextStyle(
                                  color: BookingColors.textSecondary,
                                ),
                              ),
                            ),
                          ],
                        )
                      : ListView.builder(
                          controller: _scrollController,
                          itemCount: search.items.length +
                              (search.isLoadingMore ? 1 : 0),
                          itemBuilder: (_, i) {
                            if (i >= search.items.length) {
                              return const Padding(
                                padding: EdgeInsets.all(16),
                                child: Center(
                                  child: CircularProgressIndicator(
                                    color: BookingColors.oyoRed,
                                  ),
                                ),
                              );
                            }
                            final item = search.items[i];
                            return ParlourListCard(
                              parlour: item,
                              onTap: () =>
                                  context.push('/parlour/${item.id}/detail'),
                            );
                          },
                        ),
            ),
          ),
        ],
      ),
    );
  }
}