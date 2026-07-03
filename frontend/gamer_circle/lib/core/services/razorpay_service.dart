import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:razorpay_flutter/razorpay_flutter.dart';

class RazorpayCheckoutResult {
  const RazorpayCheckoutResult({
    required this.paymentId,
    required this.orderId,
    required this.signature,
  });

  final String paymentId;
  final String orderId;
  final String signature;
}

/// Opens native Razorpay checkout on mobile; unavailable on web (use dev fallback).
class RazorpayService {
  Razorpay? _razorpay;
  Completer<RazorpayCheckoutResult>? _completer;

  bool get isSupported => !kIsWeb;

  Future<RazorpayCheckoutResult> openCheckout({
    required String keyId,
    required String orderId,
    required int amountPaise,
    required String description,
    String? contact,
    String? email,
  }) async {
    if (!isSupported) {
      throw UnsupportedError('Razorpay native checkout is not available on web');
    }

    _completer = Completer<RazorpayCheckoutResult>();
    _razorpay = Razorpay();
    _razorpay!
      ..on(Razorpay.EVENT_PAYMENT_SUCCESS, _onSuccess)
      ..on(Razorpay.EVENT_PAYMENT_ERROR, _onError)
      ..on(Razorpay.EVENT_EXTERNAL_WALLET, _onExternalWallet);

    final options = <String, dynamic>{
      'key': keyId,
      'order_id': orderId,
      'amount': amountPaise,
      'name': 'GamerCircle',
      'description': description,
      'currency': 'INR',
      if (contact != null || email != null)
        'prefill': {
          if (contact != null) 'contact': contact,
          if (email != null) 'email': email,
        },
    };

    _razorpay!.open(options);
    return _completer!.future;
  }

  void _onSuccess(PaymentSuccessResponse response) {
    final paymentId = response.paymentId;
    final orderId = response.orderId;
    final signature = response.signature;
    if (paymentId == null || orderId == null || signature == null) {
      _completer?.completeError(StateError('Incomplete Razorpay success payload'));
    } else {
      _completer?.complete(
        RazorpayCheckoutResult(
          paymentId: paymentId,
          orderId: orderId,
          signature: signature,
        ),
      );
    }
    _dispose();
  }

  void _onError(PaymentFailureResponse response) {
    _completer?.completeError(
      Exception(response.message ?? 'Payment failed (${response.code})'),
    );
    _dispose();
  }

  void _onExternalWallet(ExternalWalletResponse response) {
    _completer?.completeError(
      Exception('External wallet selected: ${response.walletName}'),
    );
    _dispose();
  }

  void _dispose() {
    _razorpay?.clear();
    _razorpay = null;
  }
}