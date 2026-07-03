import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';

part 'user_model.freezed.dart';
part 'user_model.g.dart';

@freezed
class UserModel with _$UserModel {
  const UserModel._();

  const factory UserModel({
    required String id,
    String? email,
    @JsonKey(name: 'name') String? name,
    String? username,
    @JsonKey(name: 'phone_number') String? phoneNumber,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
  }) = _UserModel;

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);

  User toEntity() => User(
        id: id,
        email: email ?? '',
        username: username ?? name ?? phoneNumber ?? 'User',
        avatarUrl: avatarUrl,
      );
}