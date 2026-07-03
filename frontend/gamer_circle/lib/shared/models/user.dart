class AppUser {
  const AppUser({
    required this.id,
    this.name,
    this.username,
    this.email,
    this.phoneNumber,
    this.avatarUrl,
    this.role = 'user',
    this.isActive = true,
  });

  final String id;
  final String? name;
  final String? username;
  final String? email;
  final String? phoneNumber;
  final String? avatarUrl;
  final String role;
  final bool isActive;

  bool get isParlorOwner => role == 'parlor_owner';

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: json['id'] as String,
        name: json['name'] as String?,
        username: json['username'] as String?,
        email: json['email'] as String?,
        phoneNumber: json['phone_number'] as String?,
        avatarUrl: json['avatar_url'] as String?,
        role: json['role'] as String? ?? 'user',
        isActive: json['is_active'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'username': username,
        'email': email,
        'phone_number': phoneNumber,
        'avatar_url': avatarUrl,
        'role': role,
        'is_active': isActive,
      };

  AppUser copyWith({
    String? id,
    String? name,
    String? username,
    String? email,
    String? phoneNumber,
    String? avatarUrl,
    String? role,
    bool? isActive,
  }) =>
      AppUser(
        id: id ?? this.id,
        name: name ?? this.name,
        username: username ?? this.username,
        email: email ?? this.email,
        phoneNumber: phoneNumber ?? this.phoneNumber,
        avatarUrl: avatarUrl ?? this.avatarUrl,
        role: role ?? this.role,
        isActive: isActive ?? this.isActive,
      );
}