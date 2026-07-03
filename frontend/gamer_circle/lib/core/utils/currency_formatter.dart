import 'package:intl/intl.dart';

final inrFormatter = NumberFormat.currency(
  locale: 'en_IN',
  symbol: '₹',
  decimalDigits: 0,
);

String formatInr(num amount) => inrFormatter.format(amount);