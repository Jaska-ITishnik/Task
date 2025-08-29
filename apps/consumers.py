import json
from apps.base import CustomAsyncJsonWebsocketConsumer

class OrderConsumer(CustomAsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        print(f"WebSocket connection initiated for user: {self.user.id}")
        await self.accept()
        if not await self.is_authenticate():
            print(f"Authentication failed for user: {self.user.id}")
            return
        self.role = self.scope["url_route"]["kwargs"]["role"]
        print(f"User {self.user.id} connected with role: {self.role}")

        self.user_group = f"user_{self.user.id}"
        self.role_group = f"{self.role}_group"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.role_group, self.channel_name)
        print(f"User {self.user.id} added to groups: {self.user_group}, {self.role_group}")

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected for user: {self.user.id} with close code: {close_code}")
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        await self.channel_layer.group_discard(self.role_group, self.channel_name)
        print(f"User {self.user.id} removed from groups: {self.user_group}, {self.role_group}")

    async def receive(self, text_data):
        if not text_data:
            print("Empty message received")
            return

        try:
            data = json.loads(text_data)
            message = data.get("message")
            if message:
                print(f"Message received from user {self.user.id}: {message}")
                await self.channel_layer.group_send(
                    self.role_group,
                    {
                        "type": "send_message",
                        "message": message
                    }
                )
            else:
                print(f"No message content in data from user {self.user.id}")
        except json.JSONDecodeError:
            print(f"Invalid JSON received from user {self.user.id}: {text_data}")
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))

    async def send_message(self, event):
        message = event["message"]
        print(f"Sending message to user {self.user.id}: {message}")
        await self.send(text_data=json.dumps({
            "message": message
        }))