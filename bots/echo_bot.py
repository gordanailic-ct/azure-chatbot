# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount
from rag_query import ask_question

class EchoBot(ActivityHandler):
    def __init__(self):
        super().__init__()
        self.conversations = {}   # ovde pamtimo poruke po conversation.id
        self.max_history = 10     # koliko poslednjih poruka cuvamo

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Dobrodosli!")

    async def on_message_activity(self, turn_context: TurnContext):
        question = turn_context.activity.text.strip()

        # 1. uzmi conversation.id
        conversation_id = turn_context.activity.conversation.id
        print("conversation_id:", conversation_id)

        # 2. ako prvi put vidimo taj conversation id, napravi praznu listu
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # 3. uzmi staru istoriju za taj razgovor
        history = self.conversations[conversation_id]

        try:
            #print("HISTORY PRE ODGOVORA:", history)
            # 4. posalji pitanje + istoriju u RAG
            answer = ask_question(question, history)

            # 5. sacuvaj user poruku
            history.append({
                "role": "user",
                "content": question
            })

            # 6. sacuvaj bot odgovor
            history.append({
                "role": "assistant",
                "content": answer
            })

            # 7. zadrzi samo poslednjih N poruka
            self.conversations[conversation_id] = history[-self.max_history:]
            print("HISTORY POSLE ODGOVORA:", self.conversations[conversation_id])

            await turn_context.send_activity(MessageFactory.text(answer))

        except Exception as e:
            print("GRESKA:", e)
            await turn_context.send_activity("Došlo je do greške prilikom obrade pitanja.")
