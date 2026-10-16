abstract class ChatEvent {}

class ChatStarted extends ChatEvent {
  final String? conversationId;
  ChatStarted({this.conversationId});
}

class ChatReconnect extends ChatEvent {}

class ChatConversationOpened extends ChatEvent {
  final String conversationId;
  final List<Map<String, dynamic>> messages;
  ChatConversationOpened(this.conversationId, this.messages);
}

class ChatNewConversation extends ChatEvent {}

class SendMessage extends ChatEvent {
  final String message;

  SendMessage(this.message);
}

class ChatDisconnected extends ChatEvent {}

class ChatSocketEvent extends ChatEvent {
  final Map<String, dynamic> data;
  ChatSocketEvent(this.data);
}

class ChatSocketError extends ChatEvent {
  final String message;
  ChatSocketError(this.message);
}
