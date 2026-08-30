class AppConstants {
  AppConstants._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.dhinadts.com/api/v1',
  );
}
