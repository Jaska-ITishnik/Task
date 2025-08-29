import json

from apps.base import CustomAsyncJsonWebsocketConsumer


class OrderConsumer(CustomAsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        await self.accept()
        if not await self.is_authenticate():
            return
        self.role = self.scope["url_route"]["kwargs"]["role"]

        self.user_group = f"user_{self.user.id}"

        self.role_group = f"{self.role}_group"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.role_group, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        await self.channel_layer.group_discard(self.role_group, self.channel_name)

    async def receive(self, text_data):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            message = data.get("message")
            if message:
                await self.channel_layer.group_send(
                    self.role_group,
                    {
                        "type": "send_message",
                        "message": message
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))

    async def send_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))
