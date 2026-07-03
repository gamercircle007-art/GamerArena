import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

class CreateTournamentScreen extends ConsumerStatefulWidget {
  const CreateTournamentScreen({super.key});

  @override
  ConsumerState<CreateTournamentScreen> createState() => _CreateTournamentScreenState();
}

class _CreateTournamentScreenState extends ConsumerState<CreateTournamentScreen> {
  final _title = TextEditingController();
  final _slots = TextEditingController(text: '16');
  final _fee = TextEditingController(text: '0');
  final _rules = TextEditingController();
  final _prize1 = TextEditingController();
  String _gameType = 'BGMI';
  String _format = 'Squad';
  DateTime _start = DateTime.now().add(const Duration(days: 1));
  DateTime _end = DateTime.now().add(const Duration(days: 1, hours: 3));
  bool _submitting = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Tournament')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(controller: _title, decoration: const InputDecoration(labelText: 'Title')),
          DropdownButtonFormField(
            value: _gameType,
            items: ['BGMI', 'Valorant', 'FIFA', 'COD']
                .map((g) => DropdownMenuItem(value: g, child: Text(g)))
                .toList(),
            onChanged: (v) => setState(() => _gameType = v!),
            decoration: const InputDecoration(labelText: 'Game'),
          ),
          DropdownButtonFormField(
            value: _format,
            items: ['Solo', 'Duo', 'Squad']
                .map((g) => DropdownMenuItem(value: g, child: Text(g)))
                .toList(),
            onChanged: (v) => setState(() => _format = v!),
            decoration: const InputDecoration(labelText: 'Format'),
          ),
          TextField(
            controller: _slots,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Total slots'),
          ),
          TextField(
            controller: _fee,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Entry fee (0 = free)'),
          ),
          TextField(controller: _prize1, decoration: const InputDecoration(labelText: '1st prize')),
          TextField(
            controller: _rules,
            maxLines: 4,
            decoration: const InputDecoration(labelText: 'Rules'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _submitting
                ? null
                : () async {
                    setState(() => _submitting = true);
                    try {
                      final t = await ref.read(socialApiProvider).createTournament({
                        'title': _title.text,
                        'game_type': _gameType,
                        'format': _format,
                        'start_time': _start.toUtc().toIso8601String(),
                        'end_time': _end.toUtc().toIso8601String(),
                        'total_slots': int.parse(_slots.text),
                        'entry_fee': _fee.text,
                        'prizes': {'1st': _prize1.text},
                        'rules': _rules.text,
                      });
                      if (context.mounted) context.go('/tournaments/${t.id}');
                    } finally {
                      if (mounted) setState(() => _submitting = false);
                    }
                  },
            child: _submitting
                ? const CircularProgressIndicator()
                : const Text('Create Tournament'),
          ),
        ],
      ),
    );
  }
}