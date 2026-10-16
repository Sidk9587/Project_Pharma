import 'package:flutter/material.dart';

import '../bloc/chat_state.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 700),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser ? Colors.blue : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message.text.isEmpty && message.isStreaming
                  ? 'Thinking…'
                  : message.text,
              style: TextStyle(
                color: isUser ? Colors.white : Colors.black87,
                fontSize: 15,
              ),
            ),
            if (!isUser && message.sources.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Divider(height: 1),
              const SizedBox(height: 8),
              const Text(
                'Sources',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
              ),
              for (final source in message.sources)
                Padding(
                  padding: const EdgeInsets.only(top: 5),
                  child: Text(
                    '${source['source'] ?? 'Document'}${source['page_number'] == null ? '' : ' · p. ${source['page_number']}'}${source['url'] == null ? '' : '\n${source['url']}'}',
                    style: TextStyle(
                      fontSize: 12,
                      color: isUser ? Colors.white70 : Colors.blueGrey.shade700,
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}
