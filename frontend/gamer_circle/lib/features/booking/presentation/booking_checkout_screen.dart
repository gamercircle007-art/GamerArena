import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/booking_flow_provider.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';
import 'package:intl/intl.dart';

/// Screen 2 of 3 — hold + countdown + pay.
///
/// UX assumptions:
/// - Hold is taken when this screen opens (optimistic pending already past).
/// - Countdown uses server `expires_at`, recomputed each tick.
/// - Leaving with an active hold releases it (don't freeze the club).
/// - Pay uses Cashfree session when present; otherwise pay-at-parlor confirm path.
class BookingCheckoutScreen extends ConsumerStatefulWidget {
  const BookingCheckoutScreen({super.key, required this.parlorId});

  final String parlorId;

  @override
  ConsumerState<BookingCheckoutScreen> createState() =>
      _BookingCheckoutScreenState();
}

class _BookingCheckoutScreenState extends ConsumerState<BookingCheckoutScreen>
    with WidgetsBindingObserver {
  String? _bookingId;
  String? _expiresAtIso;
  String? _paymentSessionId;
  String? _cfOrderId;
  bool _mockMode = false;
  bool _busy = false;
  String? _error;
  Timer? _ticker;
  Duration _remaining = Duration.zero;
  bool _warned60 = false;
  late final String _idempotencyKey =
      'hold-${DateTime.now().microsecondsSinceEpoch}';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) => _acquireHold());
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) => _tick());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _ticker?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _tick();
      // Spec: never trust grid from before background — refresh status if held.
      if (_bookingId != null) {
        _refreshStatus();
      }
    }
  }

  Future<void> _refreshStatus() async {
    final id = _bookingId;
    if (id == null) return;
    try {
      final data =
          await ref.read(gamingBookingRepositoryProvider).fetchBookingStatus(id);
      final exp = data['hold_expires_at']?.toString();
      if (exp != null && mounted) {
        setState(() => _expiresAtIso = exp);
        _tick();
      }
    } catch (_) {}
  }

  void _tick() {
    final iso = _expiresAtIso;
    if (iso == null) return;
    final exp = DateTime.tryParse(iso)?.toLocal();
    if (exp == null) return;
    final left = exp.difference(DateTime.now());
    if (!mounted) return;
    setState(() => _remaining = left.isNegative ? Duration.zero : left);
    if (!_warned60 && left.inSeconds <= 60 && left.inSeconds > 0) {
      _warned60 = true;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Hold expires in under a minute')),
      );
    }
    if (left <= Duration.zero && _bookingId != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Hold expired — pick another time')),
      );
      ref.read(bookingSelectionProvider.notifier).state = null;
      if (mounted) context.pop();
    }
  }

  Future<void> _acquireHold() async {
    final sel = ref.read(bookingSelectionProvider);
    if (sel == null || sel.parlorId != widget.parlorId) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Session expired — select a time again')),
        );
        context.pop();
      }
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repo = ref.read(gamingBookingRepositoryProvider);
      final result = await repo.holdSlot(
        parlorId: sel.parlorId,
        stationType: sel.stationType,
        date: sel.date,
        startTime: sel.startTime,
        durationHours: sel.durationHours,
        units: sel.units,
        idempotencyKey: _idempotencyKey,
      );
      final booking = result['booking'] as Map<String, dynamic>? ?? {};
      if (!mounted) return;
      setState(() {
        _bookingId = booking['id']?.toString();
        _expiresAtIso = result['expires_at']?.toString() ??
            booking['hold_expires_at']?.toString();
        _busy = false;
      });
      _tick();
    } on DioException catch (e) {
      final code = e.response?.statusCode;
      final msg = e.response?.data is Map
          ? (e.response!.data['message']?.toString() ?? e.message)
          : e.message;
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = code == 409
            ? 'Someone just took that time — pick another'
            : (msg ?? 'Could not hold slot');
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_error!)),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _releaseAndLeave() async {
    final id = _bookingId;
    if (id != null) {
      try {
        await ref.read(gamingBookingRepositoryProvider).releaseHold(id);
      } catch (_) {}
    }
    ref.read(bookingSelectionProvider.notifier).state = null;
    if (mounted) context.pop();
  }

  Future<void> _payOnline() async {
    final id = _bookingId;
    if (id == null) return;
    setState(() => _busy = true);
    try {
      final repo = ref.read(gamingBookingRepositoryProvider);
      final result = await repo.payHeldBooking(id);
      if (!mounted) return;
      setState(() {
        _paymentSessionId = result['payment_session_id']?.toString();
        _cfOrderId = result['cf_order_id']?.toString();
        _mockMode = result['mock_mode'] == true;
        _expiresAtIso = result['expires_at']?.toString() ?? _expiresAtIso;
        _busy = false;
      });
      // Poll — webhook is authoritative (do not trust SDK alone).
      if (mounted) {
        context.pushReplacement(
          '/booking/status/$id',
          extra: {
            'mockMode': _mockMode,
            'paymentSessionId': _paymentSessionId,
            'cfOrderId': _cfOrderId,
          },
        );
      }
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? e.response!.data['message']?.toString()
          : e.message;
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(msg ?? 'Payment start failed — hold still active')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _payAtParlor() async {
    final sel = ref.read(bookingSelectionProvider);
    final id = _bookingId;
    if (sel == null || id == null) return;
    setState(() => _busy = true);
    try {
      // Release hold then create confirmed pay-at-parlor via v2 (uses EXCLUDE).
      final repo = ref.read(gamingBookingRepositoryProvider);
      try {
        await repo.releaseHold(id);
      } catch (_) {}
      final result = await repo.createBookingV2(
        parlorId: sel.parlorId,
        stationType: sel.stationType,
        date: sel.date,
        startTime: sel.startTime,
        durationHours: sel.durationHours,
        units: sel.units,
        paymentMode: 'pay_at_parlor',
        idempotencyKey: 'payparlor-$_idempotencyKey',
      );
      final booking = result['booking'] as Map<String, dynamic>?;
      final newId = booking?['id']?.toString();
      ref.read(bookingSelectionProvider.notifier).state = null;
      if (newId != null && mounted) {
        context.pushReplacement('/booking/status/$newId');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not confirm: $e')),
      );
    }
  }

  String _fmt(Duration d) {
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    final h = d.inHours;
    if (h > 0) return '$h:$m:$s';
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    final sel = ref.watch(bookingSelectionProvider);
    if (sel == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Checkout')),
        body: const Center(child: Text('No selection')),
      );
    }

    final urgent = _remaining.inSeconds > 0 && _remaining.inSeconds <= 60;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        await _releaseAndLeave();
      },
      child: Scaffold(
        backgroundColor: BookingColors.background,
        appBar: AppBar(
          title: const Text('2 · Checkout'),
          backgroundColor: BookingColors.oyoRed,
          foregroundColor: Colors.white,
          leading: IconButton(
            icon: const Icon(Icons.close),
            onPressed: _busy ? null : _releaseAndLeave,
          ),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_expiresAtIso != null)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: urgent ? const Color(0xFFFFF1F0) : Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: urgent ? BookingColors.oyoRed : BookingColors.border,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.timer_outlined,
                      color: urgent ? BookingColors.oyoRed : BookingColors.textSecondary,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _remaining == Duration.zero
                            ? 'Hold expired'
                            : 'Hold expires in ${_fmt(_remaining)}',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          color: urgent ? BookingColors.oyoRed : BookingColors.textPrimary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            Text(
              sel.parlorName,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            _Line('Date', DateFormat('EEE, dd MMM').format(sel.date)),
            _Line('Time', '${sel.startTimeDisplay} · ${sel.durationHours}h'),
            _Line('Station', '${sel.stationType} · x${sel.units}'),
            const Divider(height: 28),
            const Text('Itemised total', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            _Line('Subtotal', formatInr(sel.priceRupees)),
            _Line('Taxes & fees', 'Included'),
            _Line('Total due', formatInr(sel.priceRupees), bold: true),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.red)),
              TextButton(
                onPressed: _busy ? null : _acquireHold,
                child: const Text('Retry hold'),
              ),
            ],
            if (_busy && _bookingId == null) ...[
              const SizedBox(height: 24),
              const Center(
                child: CircularProgressIndicator(color: BookingColors.oyoRed),
              ),
              const SizedBox(height: 8),
              const Center(child: Text('Holding your slot…')),
            ],
          ],
        ),
        bottomNavigationBar: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: BookingColors.oyoRed,
                    ),
                    onPressed: (_busy || _bookingId == null) ? null : _payOnline,
                    child: const Text(
                      'Pay with UPI / card',
                      style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: OutlinedButton(
                    onPressed: (_busy || _bookingId == null) ? null : _payAtParlor,
                    child: const Text('Pay at parlor'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Line extends StatelessWidget {
  const _Line(this.label, this.value, {this.bold = false});

  final String label;
  final String value;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontWeight: bold ? FontWeight.w800 : FontWeight.w500,
      fontSize: bold ? 16 : 14,
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(child: Text(label, style: style)),
          Text(value, style: style),
        ],
      ),
    );
  }
}
