# marksheet_mobile

A new Flutter project.

## Local development

The Android emulator is configured in `lib/config/constant.dart` to call the
backend on the development computer through Android's localhost alias:

```powershell
flutter run
```

`10.0.2.2` maps to the development computer's localhost from the Android
emulator. For Flutter web or desktop, change `AppConstants.apiBaseUrl` to
`http://127.0.0.1:8001/api/v1`. A physical phone cannot access a backend that is
intentionally bound only to the development computer's loopback interface.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
