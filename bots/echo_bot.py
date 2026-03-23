# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount
from rag_query import ask_question

class EchoBot(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Dobrodosli!")

    async def on_message_activity(self, turn_context: TurnContext):
        print("ULAZIM U BOT")

        question = turn_context.activity.text

        try:
            answer = ask_question(question)

            await turn_context.send_activity(MessageFactory.text(answer))

        except Exception as e:
            print("GRESKA:", e)
            await turn_context.send_activity("Došlo je do greške prilikom obrade pitanja.")
