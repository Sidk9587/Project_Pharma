import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/network/api_client.dart';
import '../bloc/chat_bloc.dart';
import '../bloc/chat_event.dart';
import '../bloc/chat_state.dart';
import 'message_bubble.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  final _scroll = ScrollController();
  final _api = ApiClient();
  @override
  void initState() {
    super.initState();
    context.read<ChatBloc>().add(ChatStarted());
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    context.read<ChatBloc>().add(SendMessage(text));
    _controller.clear();
  }

  Future<void> _newConversation() async {
    try {
      final result = await _api.createConversation();
      if (!mounted) return;
      context.read<ChatBloc>().add(
        ChatConversationOpened(result['id'].toString(), []),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(_api.friendlyError(e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Ask your knowledge base',
                  style: Theme.of(
                    context,
                  ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 4),
                Text(
                  'Answers use approved documents and sources.',
                  style: TextStyle(color: Colors.blueGrey.shade600),
                ),
              ],
            ),
          ),
          BlocBuilder<ChatBloc, ChatState>(
            builder: (context, state) => state.connected
                ? const SizedBox.shrink()
                : TextButton.icon(
                    onPressed: () =>
                        context.read<ChatBloc>().add(ChatReconnect()),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Reconnect'),
                  ),
          ),
          const SizedBox(width: 6),
          OutlinedButton.icon(
            onPressed: _newConversation,
            icon: const Icon(Icons.add),
            label: const Text('New chat'),
          ),
        ],
      ),
      const SizedBox(height: 14),
      Expanded(
        child: Card(
          child: BlocConsumer<ChatBloc, ChatState>(
            listener: (context, state) {
              if (state.error != null) {
                ScaffoldMessenger.of(
                  context,
                ).showSnackBar(SnackBar(content: Text(state.error!)));
              }
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (_scroll.hasClients) {
                  _scroll.animateTo(
                    _scroll.position.maxScrollExtent,
                    duration: const Duration(milliseconds: 180),
                    curve: Curves.easeOut,
                  );
                }
              });
            },
            builder: (context, state) {
              if (state.messages.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 66,
                          height: 66,
                          decoration: BoxDecoration(
                            color: const Color(0xFFE7F4F1),
                            borderRadius: BorderRadius.circular(22),
                          ),
                          child: const Icon(
                            Icons.auto_awesome,
                            size: 30,
                            color: Color(0xFF116B63),
                          ),
                        ),
                        const SizedBox(height: 18),
                        const Text(
                          'What would you like to know?',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Ask a question about indexed PDFs or approved website sources.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.blueGrey.shade600),
                        ),
                      ],
                    ),
                  ),
                );
              }
              return ListView.builder(
                controller: _scroll,
                padding: const EdgeInsets.symmetric(vertical: 14),
                itemCount: state.messages.length,
                itemBuilder: (context, i) =>
                    MessageBubble(message: state.messages[i]),
              );
            },
          ),
        ),
      ),
      BlocBuilder<ChatBloc, ChatState>(
        builder: (context, state) => state.isGenerating
            ? Padding(
                padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      state.status.isEmpty
                          ? 'Generating answer…'
                          : state.status,
                      style: TextStyle(
                        color: Colors.blueGrey.shade600,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              )
            : const SizedBox(height: 8),
      ),
      BlocBuilder<ChatBloc, ChatState>(
        builder: (context, state) => Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                readOnly: state.isGenerating || !state.connected,
                minLines: 1,
                maxLines: 5,
                maxLength: 2000,
                onSubmitted: (_) => _send(),
                decoration: InputDecoration(
                  counterText: '',
                  hintText: state.connected
                      ? 'Ask about your indexed knowledge…'
                      : 'Reconnect to continue',
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 14,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: FilledButton.icon(
                onPressed: state.isGenerating || !state.connected
                    ? null
                    : _send,
                icon: const Icon(Icons.send),
                label: const Text('Send'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 17,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ],
  );
  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }
}
