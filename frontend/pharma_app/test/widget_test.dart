import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharma_app/features/chat/bloc/chat_state.dart';
import 'package:pharma_app/features/chat/presentation/message_bubble.dart';

void main() {
  testWidgets('assistant answer renders its source citation', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MessageBubble(
            message: ChatMessage(
              text: 'The retention period is seven years.',
              isUser: false,
              sources: const [
                {
                  'source': 'Records Policy.pdf',
                  'page_number': 4,
                  'url': 'https://example.org/policy',
                },
              ],
            ),
          ),
        ),
      ),
    );

    expect(find.text('The retention period is seven years.'), findsOneWidget);
    expect(find.text('Sources'), findsOneWidget);
    expect(find.textContaining('Records Policy.pdf · p. 4'), findsOneWidget);
    expect(find.textContaining('https://example.org/policy'), findsOneWidget);
  });
}
