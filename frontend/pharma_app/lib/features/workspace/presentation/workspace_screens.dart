import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/network/api_client.dart';
import '../../chat/bloc/chat_bloc.dart';
import '../../chat/bloc/chat_event.dart';

final _api = ApiClient();

class _Heading extends StatelessWidget {
  final String title, subtitle;
  final Widget? action;
  const _Heading(this.title, this.subtitle, {this.action});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 5),
              Text(subtitle, style: TextStyle(color: Colors.blueGrey.shade600)),
            ],
          ),
        ),
        ?action,
      ],
    ),
  );
}

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});
  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  List<dynamic> items = [];
  bool loading = true, uploading = false;
  double progress = 0;
  String? error, notice;
  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      items = await _api.documents();
    } catch (e) {
      error = _api.friendlyError(e);
    }
    if (mounted) setState(() => loading = false);
  }

  Future<void> pickUpload() async {
    try {
      final selection = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );
      if (selection.isEmpty) return;
      final file = selection.single;
      final size = await file.length() ?? 0;
      if (size > 50 * 1024 * 1024) {
        setState(() => error = 'PDF files must be 50 MB or smaller.');
        return;
      }
      final bytes = await file.readAsBytes();
      if (bytes.length > 50 * 1024 * 1024) {
        setState(() => error = 'PDF files must be 50 MB or smaller.');
        return;
      }
      setState(() {
        uploading = true;
        error = null;
        notice = null;
        progress = 0;
      });
      final result = await _api.uploadPdf(file.name, bytes, (sent, total) {
        if (mounted && total > 0) setState(() => progress = sent / total);
      });
      setState(
        () => notice = result['duplicate'] == true
            ? 'This PDF is already indexed (existing document reused).'
            : 'PDF uploaded: ${result['chunks_created']} text sections indexed.',
      );
      await refresh();
    } catch (e) {
      if (mounted) setState(() => error = _api.friendlyError(e));
    } finally {
      if (mounted) setState(() => uploading = false);
    }
  }

  Future<void> remove(Map item) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete document?'),
        content: Text(
          '“${item['file_name'] ?? item['title']}” and its indexed content will be deleted.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await _api.deleteDocument(item['id'].toString());
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  Future<void> showDetails(Map<String, dynamic> item) async {
    try {
      final id = item['id'].toString();
      final responses = await Future.wait([
        _api.documentDetail(id),
        _api.documentStatus(id),
      ]);
      if (!mounted) return;
      final detail = responses[0];
      final status = responses[1]['status'];
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(detail['file_name'] ?? detail['title'] ?? 'Document'),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  _SettingRow('Status', status),
                  _SettingRow('Type', detail['document_type']),
                  _SettingRow('Created', _date(detail['created_at'])),
                  _SettingRow('Updated', _date(detail['updated_at'])),
                  _SettingRow('Content SHA-256', detail['content_hash']),
                  if (detail['url'] != null)
                    _SettingRow('Source URL', detail['url']),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (mounted) setState(() => error = _api.friendlyError(e));
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _Heading(
        'Documents',
        'PDF knowledge indexed for grounded answers.',
        action: FilledButton.icon(
          onPressed: uploading ? null : pickUpload,
          icon: const Icon(Icons.upload_file),
          label: const Text('Upload PDF'),
        ),
      ),
      if (uploading)
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Uploading and indexing PDF…'),
                const SizedBox(height: 10),
                LinearProgressIndicator(value: progress > 0 ? progress : null),
              ],
            ),
          ),
        ),
      if (notice != null) _Notice(notice!, good: true),
      if (error != null)
        _Notice(
          error!,
          good: false,
          onClose: () => setState(() => error = null),
        ),
      Expanded(
        child: Card(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : items.isEmpty
              ? const _Empty(
                  icon: Icons.description_outlined,
                  title: 'No documents yet',
                  detail: 'Upload a PDF to make it searchable in chat.',
                )
              : RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(8),
                    itemCount: items.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, i) {
                      final item = Map<String, dynamic>.from(items[i]);
                      return ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.picture_as_pdf_outlined),
                        ),
                        title: Text(
                          item['file_name'] ?? item['title'] ?? 'PDF',
                        ),
                        subtitle: Text(
                          '${item['document_type']} · ${_date(item['created_at'])}',
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            _StatusPill(item['status'] ?? 'unknown'),
                            IconButton(
                              tooltip: 'Document details',
                              onPressed: () => showDetails(item),
                              icon: const Icon(Icons.info_outline),
                            ),
                            IconButton(
                              tooltip: 'Delete document',
                              onPressed: () => remove(item),
                              icon: const Icon(Icons.delete_outline),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
        ),
      ),
    ],
  );
}

class SourcesScreen extends StatefulWidget {
  const SourcesScreen({super.key});
  @override
  State<SourcesScreen> createState() => _SourcesScreenState();
}

class _SourcesScreenState extends State<SourcesScreen> {
  List<dynamic> items = [];
  bool loading = true;
  String? error, notice;
  @override
  void initState() {
    super.initState();
    refresh();
  }

  final Map<String, Future<Map<String, dynamic>>> _statuses = {};
  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      items = await _api.sources();
      _statuses
        ..clear()
        ..addEntries(
          items.map((item) {
            final id = item['id'].toString();
            return MapEntry(id, _api.sourceStatus(id));
          }),
        );
    } catch (e) {
      error = _api.friendlyError(e);
    }
    if (mounted) setState(() => loading = false);
  }

  Future<void> addSource() async {
    final name = TextEditingController(), url = TextEditingController();
    final yes = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add approved website'),
        content: SizedBox(
          width: 420,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: name,
                decoration: const InputDecoration(labelText: 'Source name'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: url,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  labelText: 'Website root URL',
                  hintText: 'https://docs.example.com',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Add source'),
          ),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await _api.createSource(name.text.trim(), url.text.trim());
      setState(
        () => notice =
            'Source added. Its crawl scope is restricted to this configured site.',
      );
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  Future<void> editSource(Map<String, dynamic> item) async {
    final name = TextEditingController(text: item['name']?.toString() ?? '');
    final url = TextEditingController(text: item['base_url']?.toString() ?? '');
    final yes = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit source configuration'),
        content: SizedBox(
          width: 420,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: name,
                decoration: const InputDecoration(labelText: 'Source name'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: url,
                decoration: const InputDecoration(
                  labelText: 'Website root URL',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await _api.patchSource(item['id'].toString(), {
        'name': name.text.trim(),
        'base_url': url.text.trim(),
      });
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  Future<void> update(
    Map<String, dynamic> item,
    Map<String, dynamic> changes,
  ) async {
    try {
      await _api.patchSource(item['id'].toString(), changes);
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  Future<void> crawl(Map<String, dynamic> item) async {
    try {
      final result = await _api.crawlSource(item['id'].toString());
      setState(
        () => notice =
            'Crawl ${result['status']}: ${result['pages_indexed']} indexed, ${result['pages_skipped']} unchanged, ${result['pages_failed']} failed, ${result['pages_blocked']} blocked by robots rules.',
      );
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  Future<void> remove(Map<String, dynamic> item) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove source?'),
        content: const Text(
          'This removes only documents and vectors indexed under this source.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remove'),
          ),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await _api.deleteSource(item['id'].toString());
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _Heading(
        'Knowledge sources',
        'Only explicitly configured websites can be crawled.',
        action: FilledButton.icon(
          onPressed: addSource,
          icon: const Icon(Icons.add),
          label: const Text('Add source'),
        ),
      ),
      if (notice != null) _Notice(notice!, good: true),
      if (error != null) _Notice(error!, good: false),
      Expanded(
        child: Card(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : items.isEmpty
              ? const _Empty(
                  icon: Icons.language,
                  title: 'No approved sources',
                  detail:
                      'Add a site root before crawling. Arbitrary URLs cannot be submitted to the crawler.',
                )
              : RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView.separated(
                    itemCount: items.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, i) {
                      final item = Map<String, dynamic>.from(items[i]);
                      final enabled = item['is_active'] == true;
                      final crawlEnabled = item['crawl_enabled'] == true;
                      return ListTile(
                        isThreeLine: true,
                        leading: const CircleAvatar(
                          child: Icon(Icons.language),
                        ),
                        title: Text(item['name'] ?? item['domain']),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(item['base_url'] ?? ''),
                            Text(
                              '${enabled ? 'Active' : 'Disabled'} · Crawling ${crawlEnabled ? 'enabled' : 'disabled'}',
                            ),
                            Text(
                              item['last_crawled_at'] == null
                                  ? 'Not crawled yet'
                                  : 'Last crawl ${_date(item['last_crawled_at'])}',
                            ),
                            FutureBuilder<Map<String, dynamic>>(
                              future: _statuses[item['id'].toString()],
                              builder: (context, snapshot) {
                                final log = snapshot.data?['latest_crawl'];
                                if (log is! Map ||
                                    log['error_message'] == null) {
                                  return const SizedBox.shrink();
                                }
                                return Text(
                                  'Latest crawl issue: ${log['error_message']}',
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Colors.deepOrange,
                                  ),
                                );
                              },
                            ),
                          ],
                        ),
                        trailing: PopupMenuButton<String>(
                          tooltip: 'Source actions',
                          onSelected: (action) {
                            switch (action) {
                              case 'active':
                                update(item, {'is_active': !enabled});
                                break;
                              case 'crawl_enabled':
                                update(item, {'crawl_enabled': !crawlEnabled});
                                break;
                              case 'edit':
                                editSource(item);
                                break;
                              case 'crawl':
                                crawl(item);
                                break;
                              case 'delete':
                                remove(item);
                                break;
                            }
                          },
                          itemBuilder: (context) => [
                            PopupMenuItem(
                              value: 'active',
                              child: Text(
                                enabled ? 'Disable source' : 'Enable source',
                              ),
                            ),
                            PopupMenuItem(
                              value: 'crawl_enabled',
                              child: Text(
                                crawlEnabled
                                    ? 'Disable crawling'
                                    : 'Enable crawling',
                              ),
                            ),
                            const PopupMenuItem(
                              value: 'edit',
                              child: Text('Edit source'),
                            ),
                            PopupMenuItem(
                              value: 'crawl',
                              enabled: enabled && crawlEnabled,
                              child: const Text('Crawl now'),
                            ),
                            const PopupMenuItem(
                              value: 'delete',
                              child: Text('Remove source'),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
        ),
      ),
    ],
  );
}

class HistoryScreen extends StatefulWidget {
  final void Function()? onOpen;
  const HistoryScreen({super.key, this.onOpen});
  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<dynamic> items = [];
  bool loading = true;
  String? error;
  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      items = await _api.conversations();
    } catch (e) {
      error = _api.friendlyError(e);
    }
    if (mounted) setState(() => loading = false);
  }

  Future<void> open(Map<String, dynamic> item) async {
    try {
      final detail = await _api.conversation(item['id'].toString());
      if (!mounted) return;
      context.read<ChatBloc>().add(
        ChatConversationOpened(
          item['id'].toString(),
          List<Map<String, dynamic>>.from(detail['messages'] ?? []),
        ),
      );
      widget.onOpen?.call();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  Future<void> remove(Map<String, dynamic> item) async {
    try {
      await _api.deleteConversation(item['id'].toString());
      await refresh();
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _Heading(
        'Conversation history',
        'Resume a saved conversation or remove its history.',
        action: IconButton(onPressed: refresh, icon: const Icon(Icons.refresh)),
      ),
      if (error != null) _Notice(error!, good: false),
      Expanded(
        child: Card(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : items.isEmpty
              ? const _Empty(
                  icon: Icons.history,
                  title: 'No conversations yet',
                  detail: 'Start a chat and it will be saved here.',
                )
              : RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView.separated(
                    itemCount: items.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, i) {
                      final item = Map<String, dynamic>.from(items[i]);
                      return ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.chat_bubble_outline),
                        ),
                        title: Text(item['title'] ?? 'Conversation'),
                        subtitle: Text(_date(item['updated_at'])),
                        onTap: () => open(item),
                        trailing: IconButton(
                          tooltip: 'Delete conversation',
                          onPressed: () => remove(item),
                          icon: const Icon(Icons.delete_outline),
                        ),
                      );
                    },
                  ),
                ),
        ),
      ),
    ],
  );
}

class ExportsScreen extends StatefulWidget {
  const ExportsScreen({super.key});
  @override
  State<ExportsScreen> createState() => _ExportsScreenState();
}

class _ExportsScreenState extends State<ExportsScreen> {
  List<dynamic> conversations = [];
  String? selected, error, notice;
  bool loading = true, exporting = false;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      conversations = await _api.conversations();
    } catch (e) {
      error = _api.friendlyError(e);
    }
    if (mounted) setState(() => loading = false);
  }

  Future<void> _export(String format) async {
    if (selected == null) {
      setState(() => error = 'Choose a conversation to export.');
      return;
    }
    setState(() {
      exporting = true;
      error = null;
      notice = null;
    });
    try {
      final conversation = await _api.conversation(selected!);
      final payload = {
        'title': conversation['title'] ?? 'Pharma AI conversation',
        'messages': conversation['messages'],
      };
      final bytes = await _api.export(format, payload);
      await FileSaver.instance.saveFile(
        name: 'pharma-conversation-${DateTime.now().millisecondsSinceEpoch}',
        bytes: Uint8List.fromList(bytes),
        fileExtension: format == 'pdf' ? 'pdf' : 'xlsx',
        mimeType: format == 'pdf' ? MimeType.pdf : MimeType.microsoftExcel,
      );
      setState(() => notice = '${format.toUpperCase()} downloaded.');
    } catch (e) {
      setState(() => error = _api.friendlyError(e));
    } finally {
      if (mounted) setState(() => exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _Heading(
        'Exports',
        'Download a conversation with questions, answers, timestamps and available citations.',
      ),
      if (error != null) _Notice(error!, good: false),
      if (notice != null) _Notice(notice!, good: true),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Choose conversation',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              if (loading)
                const LinearProgressIndicator()
              else
                DropdownButtonFormField<String>(
                  initialValue: selected,
                  hint: const Text('Select conversation'),
                  items: conversations
                      .map(
                        (c) => DropdownMenuItem(
                          value: c['id'].toString(),
                          child: Text(c['title'] ?? 'Conversation'),
                        ),
                      )
                      .toList(),
                  onChanged: (v) => setState(() => selected = v),
                ),
              const SizedBox(height: 18),
              Wrap(
                spacing: 12,
                children: [
                  FilledButton.icon(
                    onPressed: exporting ? null : () => _export('pdf'),
                    icon: const Icon(Icons.picture_as_pdf_outlined),
                    label: const Text('Download PDF'),
                  ),
                  OutlinedButton.icon(
                    onPressed: exporting ? null : () => _export('excel'),
                    icon: const Icon(Icons.table_view_outlined),
                    label: const Text('Download Excel'),
                  ),
                ],
              ),
              if (exporting)
                const Padding(
                  padding: EdgeInsets.only(top: 16),
                  child: LinearProgressIndicator(),
                ),
            ],
          ),
        ),
      ),
    ],
  );
}

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? settings;
  String? error;
  bool loading = true;
  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      settings = await _api.providerSettings();
    } catch (e) {
      error = _api.friendlyError(e);
    }
    if (mounted) setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _Heading(
        'Settings',
        'Provider selection is controlled by backend environment configuration.',
      ),
      if (error != null) _Notice(error!, good: false),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : settings == null
              ? const Text('Provider configuration is unavailable.')
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Configured provider',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    _SettingRow('Chat provider', settings!['provider']),
                    _SettingRow('Chat model', settings!['model']),
                    _SettingRow(
                      'Embedding provider',
                      settings!['embedding_provider'],
                    ),
                    _SettingRow(
                      'Embedding model',
                      settings!['embedding_model'],
                    ),
                    _SettingRow(
                      'Ready',
                      settings!['configured'] == true
                          ? 'Yes'
                          : 'No — check backend environment',
                    ),
                    if (settings!['reindex_required'] == true)
                      const Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: Text(
                          'The selected embedding model uses a separate Chroma collection. Existing documents must be reindexed before they are searchable with this model.',
                          style: TextStyle(
                            color: Colors.deepOrange,
                            height: 1.4,
                          ),
                        ),
                      ),
                    const Divider(height: 28),
                    const Text(
                      'To switch providers, update LLM_PROVIDER in backend/.env and restart FastAPI. Set OPENAI_API_KEY only in the backend environment. Keys are never sent to or stored by this app.',
                      style: TextStyle(height: 1.5),
                    ),
                    const SizedBox(height: 14),
                    OutlinedButton.icon(
                      onPressed: refresh,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Refresh configuration'),
                    ),
                  ],
                ),
        ),
      ),
    ],
  );
}

class _SettingRow extends StatelessWidget {
  final String label;
  final Object? value;
  const _SettingRow(this.label, this.value);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      children: [
        SizedBox(
          width: 180,
          child: Text(label, style: TextStyle(color: Colors.blueGrey.shade600)),
        ),
        Expanded(
          child: Text(
            value?.toString() ?? 'Not set',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
      ],
    ),
  );
}

class _StatusPill extends StatelessWidget {
  final String text;
  const _StatusPill(this.text);
  @override
  Widget build(BuildContext context) {
    final status = text.toLowerCase();
    final color = switch (status) {
      'processed' => const Color(0xFFE5F4EC),
      'failed' => const Color(0xFFFFE8E5),
      'pending' || 'processing' => const Color(0xFFFFF2D9),
      _ => const Color(0xFFEEF1F0),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Text(
        text,
        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  final String message;
  final bool good;
  final VoidCallback? onClose;
  const _Notice(this.message, {required this.good, this.onClose});
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: good ? const Color(0xFFE8F5EF) : const Color(0xFFFFEBE8),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Row(
      children: [
        Icon(
          good ? Icons.check_circle_outline : Icons.error_outline,
          color: good ? Colors.teal : Colors.deepOrange,
        ),
        const SizedBox(width: 8),
        Expanded(child: Text(message)),
        if (onClose != null)
          IconButton(onPressed: onClose, icon: const Icon(Icons.close)),
      ],
    ),
  );
}

class _Empty extends StatelessWidget {
  final IconData icon;
  final String title, detail;
  const _Empty({required this.icon, required this.title, required this.detail});
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 44, color: Colors.blueGrey.shade300),
          const SizedBox(height: 14),
          Text(
            title,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
          ),
          const SizedBox(height: 6),
          Text(
            detail,
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.blueGrey.shade600),
          ),
        ],
      ),
    ),
  );
}

String _date(Object? value) {
  final date = DateTime.tryParse(value?.toString() ?? '')?.toLocal();
  if (date == null) return 'Unknown date';
  return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
}
