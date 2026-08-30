class UserProfile {
  const UserProfile({
    required this.id,
    required this.username,
    required this.userType,
    required this.mustChangePassword,
  });
  final String id;
  final String username;
  final String userType;
  final bool mustChangePassword;
  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    id: json['id'],
    username: json['username'],
    userType: json['user_type'],
    mustChangePassword: json['must_change_password'] ?? false,
  );
}

class AcademicRecord {
  AcademicRecord(this.data);
  final Map<String, dynamic> data;
  String get id => data['id'].toString();
  String text(String key) => data[key]?.toString() ?? '';
  int integer(String key) => (data[key] as num?)?.toInt() ?? 0;
}
