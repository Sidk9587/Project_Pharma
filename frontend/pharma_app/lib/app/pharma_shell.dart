import 'package:flutter/material.dart';
import '../core/network/api_client.dart';
import '../features/chat/presentation/chat_screen.dart';
import '../features/workspace/presentation/workspace_screens.dart';

class PharmaShell extends StatefulWidget {
  const PharmaShell({super.key});
  @override
  State<PharmaShell> createState() => _PharmaShellState();
}

class _PharmaShellState extends State<PharmaShell> {
  int selected = 0;
  int _historyRefresh = 0, _exportRefresh = 0;
  late final Future<String> _health = ApiClient().checkHealth();
  final titles = const [
    'AI Chat',
    'Documents',
    'Knowledge Sources',
    'Conversation History',
    'Exports',
    'Settings',
  ];
  final icons = const [
    Icons.forum_outlined,
    Icons.description_outlined,
    Icons.language,
    Icons.history,
    Icons.file_download_outlined,
    Icons.tune,
  ];
  Widget screen(int i) => switch (i) {
    0 => const ChatScreen(),
    1 => const DocumentsScreen(),
    2 => const SourcesScreen(),
    3 => HistoryScreen(
      key: ValueKey(_historyRefresh),
      onOpen: () => setState(() => selected = 0),
    ),
    4 => ExportsScreen(key: ValueKey(_exportRefresh)),
    _ => const SettingsScreen(),
  };

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    void selectSection(int value) => setState(() {
      selected = value;
      if (value == 3) _historyRefresh++;
      if (value == 4) _exportRefresh++;
    });
    final navigation = NavigationRail(
      selectedIndex: selected,
      onDestinationSelected: selectSection,
      labelType: wide
          ? NavigationRailLabelType.all
          : NavigationRailLabelType.none,
      leading: Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 24),
        child: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary,
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Icon(Icons.local_pharmacy_outlined, color: Colors.white),
        ),
      ),
      destinations: [
        for (var i = 0; i < titles.length; i++)
          NavigationRailDestination(
            icon: Icon(icons[i]),
            label: Text(titles[i]),
          ),
      ],
    );
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Text(
              titles[selected],
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const Spacer(),
            _BackendBadge(_health),
          ],
        ),
        toolbarHeight: 68,
      ),
      body: Row(
        children: [
          if (wide) navigation,
          if (wide) const VerticalDivider(width: 1),
          Expanded(
            child: Padding(
              padding: EdgeInsets.fromLTRB(
                wide ? 28 : 16,
                8,
                wide ? 28 : 16,
                22,
              ),
              child: IndexedStack(
                index: selected,
                children: [for (var i = 0; i < titles.length; i++) screen(i)],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: wide
          ? null
          : NavigationBar(
              labelBehavior:
                  NavigationDestinationLabelBehavior.onlyShowSelected,
              selectedIndex: selected,
              onDestinationSelected: selectSection,
              destinations: [
                for (var i = 0; i < titles.length; i++)
                  NavigationDestination(icon: Icon(icons[i]), label: titles[i]),
              ],
            ),
    );
  }
}

class _BackendBadge extends StatelessWidget {
  final Future<String> health;
  const _BackendBadge(this.health);
  @override
  Widget build(BuildContext context) => FutureBuilder<String>(
    future: health,
    builder: (context, snapshot) {
      final ok = snapshot.hasData;
      final done = snapshot.connectionState == ConnectionState.done;
      final color = ok
          ? const Color(0xFF18866F)
          : (done ? Colors.deepOrange : Colors.orange);
      final label = ok
          ? 'Backend online'
          : (done ? 'Backend unavailable' : 'Checking backend');
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: ok ? const Color(0xFFE8F4F1) : const Color(0xFFFFF2DF),
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          children: [
            Icon(Icons.circle, size: 8, color: color),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      );
    },
  );
}
