import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_client.dart';
import 'auth_controller.dart';

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});
  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final current = TextEditingController();
  final next = TextEditingController();
  final confirm = TextEditingController();
  String? error;
  bool busy = false;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Secure your account')),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Change the demo password',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        const Text(
          'A personal password is required before marksheets can be captured.',
        ),
        const SizedBox(height: 24),
        TextField(
          controller: current,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Current password'),
        ),
        const SizedBox(height: 14),
        TextField(
          controller: next,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'New password'),
        ),
        const SizedBox(height: 14),
        TextField(
          controller: confirm,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Confirm password'),
        ),
        if (error != null) ...[
          const SizedBox(height: 12),
          Text(error!, style: const TextStyle(color: Colors.red)),
        ],
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: busy ? null : submit,
          child: Text(busy ? 'Updating…' : 'Change password'),
        ),
      ],
    ),
  );
  Future<void> submit() async {
    if (next.text.length < 8 || next.text != confirm.text) {
      setState(
        () => error = 'Use at least 8 characters and ensure passwords match.',
      );
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final auth = context.read<AuthController>();
      await auth.repository.changePassword(current.text, next.text);
      await auth.logout();
    } catch (e) {
      setState(() => error = ApiClient.message(e));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
}
