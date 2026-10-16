import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';

import '../data/chat_websocket.dart';
import 'chat_event.dart';
import 'chat_state.dart';

class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ChatWebSocket webSocket;

  StreamSubscription? _subscription;

  ChatBloc({required this.webSocket}) : super(ChatState()) {
    on<ChatStarted>(_onChatStarted);
    on<ChatReconnect>(_onReconnect);
    on<ChatConversationOpened>(_onConversationOpened);
    on<ChatNewConversation>(_onNewConversation);
    on<SendMessage>(_onSendMessage);
    on<ChatDisconnected>(_onChatDisconnected);
    on<ChatSocketEvent>(
      (event, emit) => _handleWebSocketMessage(event.data, emit),
    );
    on<ChatSocketError>(_onSocketError);
  }

  void _onChatStarted(ChatStarted event, Emitter<ChatState> emit) {
    webSocket.connect(conversationId: event.conversationId);

    emit(state.copyWith(connected: true, conversationId: event.conversationId));

    _listen();
  }

  Future<void> _onConversationOpened(
    ChatConversationOpened event,
    Emitter<ChatState> emit,
  ) async {
    await _subscription?.cancel();
    await webSocket.disconnect();
    webSocket.connect(conversationId: event.conversationId);
    _listen();
    final messages = event.messages
        .map(
          (m) => ChatMessage(
            text: m['content'] as String? ?? '',
            isUser: m['role'] == 'user',
            createdAt: DateTime.tryParse(m['created_at']?.toString() ?? ''),
            sources: List<Map<String, dynamic>>.from(m['sources'] ?? []),
          ),
        )
        .toList();
    emit(
      state.copyWith(
        messages: messages,
        connected: true,
        isGenerating: false,
        conversationId: event.conversationId,
        sources: [],
        status: '',
      ),
    );
  }

  Future<void> _onNewConversation(
    ChatNewConversation event,
    Emitter<ChatState> emit,
  ) async {
    await _subscription?.cancel();
    await webSocket.disconnect();
    webSocket.startNewConversation();
    emit(ChatState(connected: true));
    webSocket.connect();
    _listen();
  }

  void _listen() {
    _subscription = webSocket.messages?.listen(
      (data) => add(ChatSocketEvent(data)),
      onError: (Object error) => add(ChatSocketError(error.toString())),
      onDone: () => add(
        ChatSocketError('Chat connection closed. Reconnect to continue.'),
      ),
    );
  }

  void _onSocketError(ChatSocketError event, Emitter<ChatState> emit) {
    emit(
      state.copyWith(
        isGenerating: false,
        connected: false,
        error: event.message,
      ),
    );
  }

  Future<void> _onReconnect(
    ChatReconnect event,
    Emitter<ChatState> emit,
  ) async {
    await _subscription?.cancel();
    await webSocket.disconnect();
    webSocket.connect(conversationId: state.conversationId);
    _listen();
    emit(state.copyWith(connected: true, error: null));
  }

  void _onSendMessage(SendMessage event, Emitter<ChatState> emit) {
    if (!state.connected) {
      emit(
        state.copyWith(
          error:
              'Chat is disconnected. Select Reconnect before sending a question.',
        ),
      );
      return;
    }
    if (state.isGenerating) return;
    final message = event.message.trim();

    if (message.isEmpty) {
      return;
    }

    final updatedMessages = [
      ...state.messages,
      ChatMessage(text: message, isUser: true),
      ChatMessage(text: '', isUser: false, isStreaming: true),
    ];

    emit(
      state.copyWith(
        messages: updatedMessages,
        isGenerating: true,
        status: 'Searching documents...',
        sources: [],
      ),
    );

    webSocket.sendQuestion(message);
  }

  void _handleWebSocketMessage(
    Map<String, dynamic> data,
    Emitter<ChatState> emit,
  ) {
    final type = data['type'];

    switch (type) {
      case 'status':
        final status = data['message'] as String? ?? '';

        emit(
          state.copyWith(
            status: status,
            isGenerating: true,
            conversationId: data['conversation_id'] as String?,
          ),
        );
        break;

      case 'sources':
        final sources = List<Map<String, dynamic>>.from(data['sources'] ?? []);

        emit(state.copyWith(sources: sources));
        break;

      case 'token':
        final token = data['content'] as String? ?? '';

        if (token.isEmpty || state.messages.isEmpty) {
          return;
        }

        final messages = [...state.messages];

        final lastMessage = messages.last;

        messages[messages.length - 1] = ChatMessage(
          text: lastMessage.text + token,
          isUser: false,
          isStreaming: true,
          sources: state.sources,
        );

        emit(state.copyWith(messages: messages));

        break;

      case 'complete':
        if (state.messages.isEmpty) {
          return;
        }

        final messages = [...state.messages];

        final lastMessage = messages.last;

        messages[messages.length - 1] = ChatMessage(
          text: lastMessage.text,
          isUser: false,
          isStreaming: false,
          sources: state.sources,
        );

        emit(
          state.copyWith(messages: messages, isGenerating: false, status: ''),
        );

        break;

      case 'error':
        final messages = [...state.messages];
        if (messages.isNotEmpty &&
            !messages.last.isUser &&
            messages.last.isStreaming &&
            messages.last.text.isEmpty) {
          messages.removeLast();
        } else if (messages.isNotEmpty &&
            !messages.last.isUser &&
            messages.last.isStreaming) {
          final last = messages.last;
          messages[messages.length - 1] = ChatMessage(
            text: last.text,
            isUser: false,
            sources: state.sources,
          );
        }
        emit(
          state.copyWith(
            messages: messages,
            isGenerating: false,
            error: data['message'] as String?,
          ),
        );

        break;
    }
  }

  Future<void> _onChatDisconnected(
    ChatDisconnected event,
    Emitter<ChatState> emit,
  ) async {
    await _subscription?.cancel();
    await webSocket.disconnect();

    emit(state.copyWith(connected: false, isGenerating: false));
  }

  @override
  Future<void> close() async {
    await _subscription?.cancel();
    await webSocket.disconnect();

    return super.close();
  }
}
