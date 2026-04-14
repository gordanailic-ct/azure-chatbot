import asyncio
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from rag_query import ask_question

class EchoBot(ActivityHandler):
    def __init__(self):
        super().__init__()
        self.conversations = {}
        self.max_history = 10

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Dobrodosli!")

    async def _send_typing_loop(self, turn_context: TurnContext, stop_event: asyncio.Event):
        while not stop_event.is_set():
            await turn_context.send_activity(Activity(type=ActivityTypes.typing))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=1.5)
            except asyncio.TimeoutError:
                pass

    async def on_message_activity(self, turn_context: TurnContext):
        question = turn_context.activity.text.strip()
        conversation_id = turn_context.activity.conversation.id
        print("conversation_id:", conversation_id)

        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        history = self.conversations[conversation_id]

        stop_event = asyncio.Event()
        typing_task = None

        try:
            typing_task = asyncio.create_task(self._send_typing_loop(turn_context, stop_event))

            answer = await asyncio.to_thread(ask_question, question, history)

            history.append({
                "role": "user",
                "content": question
            })

            history.append({
                "role": "assistant",
                "content": answer
            })

            self.conversations[conversation_id] = history[-self.max_history:]
            print("HISTORY POSLE ODGOVORA:", self.conversations[conversation_id])

            stop_event.set()
            await typing_task

            await turn_context.send_activity(MessageFactory.text(answer))

        except Exception as e:
            stop_event.set()
            if typing_task:
                await typing_task
            print("GRESKA:", e)
            await turn_context.send_activity("Došlo je do greške prilikom obrade pitanja.")