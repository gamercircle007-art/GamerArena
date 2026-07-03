import 'dart:convert';

import 'package:flutter/services.dart';

/// Loads bundled demo JSON for feed and store when the API has no data.
class DemoDataLoader {
  DemoDataLoader._();

  static const _feedAsset = 'assets/data/demo_feed.json';
  static const _storeAsset = 'assets/data/demo_store.json';

  static Future<List<dynamic>> loadFeedItems() async {
    final raw = await rootBundle.loadString(_feedAsset);
    final json = jsonDecode(raw) as Map<String, dynamic>;
    return json['items'] as List<dynamic>? ?? [];
  }

  static Future<List<Map<String, dynamic>>> loadStoreItems() async {
    final raw = await rootBundle.loadString(_storeAsset);
    final json = jsonDecode(raw) as Map<String, dynamic>;
    return (json['items'] as List<dynamic>)
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
  }
}