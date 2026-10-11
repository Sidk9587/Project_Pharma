import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/chat_bloc.dart';
import '../bloc/chat_event.dart';
import '../bloc/chat_state.dart';
import 'message_bubble.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({
    super.key,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller =
      TextEditingController();

  final ScrollController _scrollController =
      ScrollController();

  @override
  void initState() {
    super.initState();

    context.read<ChatBloc>().add(
      ChatStarted(),
    );
  }

  void _sendMessage() {
    final text = _controller.text.trim();

    if (text.isEmpty) {
      return;
    }

    context.read<ChatBloc>().add(
      SendMessage(text),
    );

    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pharma AI'),
      ),
      body: Column(
        children: [
          Expanded(
            child: BlocConsumer<ChatBloc, ChatState>(
              listener: (context, state) {
                WidgetsBinding.instance.addPostFrameCallback(
                  (_) {
                    if (_scrollController.hasClients) {
                      _scrollController.animateTo(
                        _scrollController.position.maxScrollExtent,
                        duration: const Duration(
                          milliseconds: 200,
                        ),
                        curve: Curves.easeOut,
                      );
                    }
                  },
                );
              },
              builder: (context, state) {
                if (state.messages.isEmpty) {
                  return const Center(
                    child: Text(
                      'Ask something about your documents',
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(
                    vertical: 16,
                  ),
                  itemCount: state.messages.length,
                  itemBuilder: (context, index) {
                    return MessageBubble(
                      message: state.messages[index],
                    );
                  },
                );
              },
            ),
          ),

          BlocBuilder<ChatBloc, ChatState>(
            builder: (context, state) {
              if (!state.isGenerating) {
                return const SizedBox.shrink();
              }

              return Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    state.status,
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 12,
                    ),
                  ),
                ),
              );
            },
          ),

          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      minLines: 1,
                      maxLines: 4,
                      onSubmitted: (_) {
                        _sendMessage();
                      },
                      decoration: const InputDecoration(
                        hintText: 'Ask something...',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _sendMessage,
                    icon: const Icon(
                      Icons.send,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();

    context.read<ChatBloc>().add(
      ChatDisconnected(),
    );

    super.dispose();
  }
}