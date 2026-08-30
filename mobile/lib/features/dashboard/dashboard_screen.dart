import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../repositories/academic_repository.dart';
import '../auth/auth_controller.dart';
import '../capture/capture_setup_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthController>().user!;
    return Scaffold(
      appBar: AppBar(
        title: const Text('VCEW Marksheets'),
        actions: [
          IconButton(
            tooltip: 'Sign out',
            onPressed: () => context.read<AuthController>().logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Biofuels and Bioenergy',
            style: Theme.of(
              context,
            ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 6),
          Text(
            '${user.username} · ${user.userType.toLowerCase()}',
            style: const TextStyle(color: Color(0xFF66788A)),
          ),
          const SizedBox(height: 24),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.document_scanner_outlined,
                    size: 34,
                    color: Color(0xFF1F6FEB),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    'Capture marksheets',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'B.Tech Biotechnology · Semester VI. Capture or upload one full internal marksheet for each of the 50 students.',
                  ),
                  const SizedBox(height: 22),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => CaptureSetupScreen(
                          repository: AcademicRepository(ApiClient()),
                        ),
                      ),
                    ),
                    icon: const Icon(Icons.arrow_forward),
                    label: const Text('Choose subject'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
