import 'dart:io';

import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../repositories/academic_repository.dart';

class OcrReviewScreen extends StatefulWidget {
  const OcrReviewScreen({
    super.key,
    required this.repository,
    required this.marksheetId,
    required this.imagePath,
    required this.studentLabel,
  });
  final AcademicRepository repository;
  final String marksheetId, imagePath, studentLabel;
  @override
  State<OcrReviewScreen> createState() => _OcrReviewScreenState();
}

class _OcrReviewScreenState extends State<OcrReviewScreen> {
  bool processing = true, saving = false;
  String? error;
  List<Map<String, dynamic>> extractions = [];
  final controllers = <String, TextEditingController>{};
  final selectedOptions = <String, String>{};

  @override
  void initState() {
    super.initState();
    process();
  }

  Future<void> process() async {
    try {
      final data = await widget.repository.processOcr(widget.marksheetId);
      extractions = (data['extractions'] as List)
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
      for (final item in extractions) {
        final value = item['reviewed_value'] ?? item['numeric_value'];
        controllers[item['id']] = TextEditingController(
          text: value == null ? '' : _displayNumber(value),
        );
      }
      if (extractions.isEmpty) {
        error = 'No handwritten mark cells were found. Retake the full sheet.';
      }
    } catch (exception) {
      error = ApiClient.message(exception);
    }
    if (mounted) setState(() => processing = false);
  }

  String _displayNumber(dynamic value) {
    final number = (value as num).toDouble();
    return number == number.roundToDouble()
        ? number.toInt().toString()
        : number.toString();
  }

  double get total => controllers.values.fold(
    0,
    (sum, controller) => sum + (double.tryParse(controller.text.trim()) ?? 0),
  );

  Future<void> saveAndApprove() async {
    final corrections = <Map<String, dynamic>>[];
    for (final item in extractions) {
      final questionNumber = extractions.indexOf(item) + 1;
      final value = double.tryParse(controllers[item['id']]!.text.trim());
      if (value == null || value < 0) {
        setState(() => error = 'Enter a valid mark for every question.');
        return;
      }
      if (questionNumber >= 11 && selectedOptions[item['id']] == null) {
        setState(() => error = 'Select option A or B for question $questionNumber.');
        return;
      }
      final maximum = questionNumber <= 10 ? 2 : questionNumber <= 15 ? 13 : 15;
      if (value > maximum) {
        setState(() => error = 'Question $questionNumber cannot exceed $maximum marks.');
        return;
      }
      corrections.add({
        'extraction_id': item['id'],
        'corrected_numeric_value': value,
        'selected_option': selectedOptions[item['id']],
      });
    }
    setState(() {
      saving = true;
      error = null;
    });
    try {
      await widget.repository.reviewOcr(widget.marksheetId, corrections);
      await widget.repository.approve(widget.marksheetId);
      if (mounted) Navigator.pop(context, true);
    } catch (exception) {
      if (mounted) setState(() => error = ApiClient.message(exception));
    }
    if (mounted) setState(() => saving = false);
  }

  @override
  void dispose() {
    for (final controller in controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Check extracted marks')),
    body: processing
        ? const Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 18),
                Text('Extracting handwritten marks…'),
              ],
            ),
          )
        : ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                widget.studentLabel,
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              const Text(
                'Only question marks and their total are retained.',
                style: TextStyle(color: Color(0xFF66788A)),
              ),
              const SizedBox(height: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: Image.file(
                  File(widget.imagePath),
                  height: 210,
                  width: double.infinity,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 18),
              ...extractions.asMap().entries.map(
                (entry) => _markCard(entry.value, entry.key + 1),
              ),
              if (extractions.isNotEmpty)
                Card(
                  child: ListTile(
                    title: const Text(
                      'Total',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    trailing: Text(
                      _displayNumber(total),
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              if (error != null)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              ElevatedButton.icon(
                onPressed: saving || extractions.isEmpty
                    ? null
                    : saveAndApprove,
                icon: const Icon(Icons.verified_outlined),
                label: Text(saving ? 'Saving…' : 'Approve marks'),
              ),
              const SizedBox(height: 24),
            ],
          ),
  );

  Widget _markCard(Map<String, dynamic> item, int questionNumber) => Card(
    margin: const EdgeInsets.only(bottom: 10),
    child: ListTile(
      title: Text(
        'Question $questionNumber',
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
      subtitle: questionNumber <= 10
          ? const Text('Compulsory · maximum 2')
          : Row(children: [
              const Text('Attempted option: '),
              DropdownButton<String>(
                value: selectedOptions[item['id']],
                hint: const Text('A or B'),
                items: const [DropdownMenuItem(value: 'A', child: Text('A')), DropdownMenuItem(value: 'B', child: Text('B'))],
                onChanged: (value) => setState(() { if (value != null) selectedOptions[item['id']] = value; }),
              ),
              Text(questionNumber <= 15 ? ' · max 13' : ' · max 15'),
            ]),
      trailing: SizedBox(
        width: 88,
        child: TextField(
          controller: controllers[item['id']],
          onChanged: (_) => setState(() {}),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          textAlign: TextAlign.center,
          decoration: const InputDecoration(labelText: 'Mark'),
        ),
      ),
    ),
  );
}
