import 'package:flutter/material.dart';

import '../bloc/chat_state.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;

    return Align(
      alignment:
          isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(
          maxWidth: 700,
        ),
        margin: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 8,
        ),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser
              ? Colors.blue
              : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(
          message.text.isEmpty && message.isStreaming
              ? 'Thinking...'
              : message.text,
          style: TextStyle(
            color: isUser
                ? Colors.white
                : Colors.black87,
            fontSize: 15,
          ),
        ),
      ),
    );
  }
}