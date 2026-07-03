import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/features/parlors/providers/parlor_search_provider.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';
import 'package:intl/intl.dart';

class SearchInputScreen extends ConsumerStatefulWidget {
  const SearchInputScreen({super.key});

  @override
  ConsumerState<SearchInputScreen> createState() => _SearchInputScreenState();
}

class _SearchInputScreenState extends ConsumerState<SearchInputScreen> {
  final _queryController = TextEditingController();
  final _cityController = TextEditingController();
  DateTime? _checkIn;
  int _numPlayers = 1;

  @override
  void dispose() {
    _queryController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
    );
    if (picked != null) setState(() => _checkIn = picked);
  }

  void _search() {
    final filters = ParlourSearchFilters(
      query: _queryController.text.trim(),
      city: _cityController.text.trim().isEmpty
          ? null
          : _cityController.text.trim(),
      checkIn: _checkIn,
      numPlayers: _numPlayers,
    );
    ref.read(parlourSearchProvider.notifier).updateFilters(filters);
    context.push('/search-results');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Search Parlours'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _queryController,
            decoration: const InputDecoration(
              labelText: 'Search by name or game',
              prefixIcon: Icon(Icons.search),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _cityController,
            decoration: const InputDecoration(
              labelText: 'City (optional)',
              prefixIcon: Icon(Icons.location_city),
            ),
          ),
          const SizedBox(height: 16),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Check-in date'),
            subtitle: Text(
              _checkIn != null
                  ? DateFormat('dd MMM yyyy').format(_checkIn!)
                  : 'Select date',
            ),
            trailing: const Icon(Icons.calendar_today),
            onTap: _pickDate,
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text('Players'),
              const Spacer(),
              IconButton(
                onPressed: _numPlayers > 1
                    ? () => setState(() => _numPlayers--)
                    : null,
                icon: const Icon(Icons.remove_circle_outline),
              ),
              Text('$_numPlayers'),
              IconButton(
                onPressed: () => setState(() => _numPlayers++),
                icon: const Icon(Icons.add_circle_outline),
              ),
            ],
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _search,
            style: FilledButton.styleFrom(
              backgroundColor: BookingColors.oyoRed,
              minimumSize: const Size(double.infinity, 48),
            ),
            child: const Text('Search'),
          ),
        ],
      ),
    );
  }
}