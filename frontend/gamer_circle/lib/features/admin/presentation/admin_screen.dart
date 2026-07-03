import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';

class AdminScreen extends ConsumerStatefulWidget {
  const AdminScreen({super.key});

  @override
  ConsumerState<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends ConsumerState<AdminScreen> {
  Map<String, dynamic>? _stats;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final res = await ref.read(dioProvider).get('/admin/stats');
      setState(() => _stats = res.data as Map<String, dynamic>);
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Admin')),
      body: _error != null
          ? Center(child: Text(_error!, textAlign: TextAlign.center))
          : _stats == null
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _AdminTile('Users', '${_stats!['users']}'),
                    _AdminTile('Parlors', '${_stats!['parlors']}'),
                    _AdminTile('Tournaments', '${_stats!['tournaments']}'),
                    _AdminTile('Bookings', '${_stats!['bookings']}'),
                    const SizedBox(height: 16),
                    Text('Status: ${_stats!['status']}'),
                  ],
                ),
    );
  }
}

class _AdminTile extends StatelessWidget {
  const _AdminTile(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(label),
        trailing: Text(value, style: Theme.of(context).textTheme.titleLarge),
      ),
    );
  }
}