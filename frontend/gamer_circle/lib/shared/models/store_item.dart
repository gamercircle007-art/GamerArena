class StoreItem {
  const StoreItem({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.currency,
    required this.category,
    this.badge,
    this.imageUrl,
  });

  final String id;
  final String name;
  final String description;
  final int price;
  final String currency;
  final String category;
  final String? badge;
  final String? imageUrl;

  factory StoreItem.fromJson(Map<String, dynamic> json) => StoreItem(
        id: json['id'] as String,
        name: json['name'] as String,
        description: json['description'] as String,
        price: json['price'] as int,
        currency: json['currency'] as String? ?? 'INR',
        category: json['category'] as String? ?? 'general',
        badge: json['badge'] as String?,
        imageUrl: json['image_url'] as String?,
      );

  String get formattedPrice => currency == 'INR' ? '₹$price' : '$currency $price';
}