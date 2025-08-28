import ujson
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from ujson import JSONDecodeError


class CustomAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        try:
            ujson.loads(text_data)
        except JSONDecodeError:
            await self.send_json({"message": "Send message in json format!"})
        else:
            return await super().receive(text_data, bytes_data, **kwargs)

    @classmethod
    async def decode_json(cls, text_data):
        return ujson.loads(text_data)

    @classmethod
    async def encode_json(cls, content):
        return ujson.dumps(content)

    async def is_authenticate(self) -> bool:
        if self.user.is_anonymous:
            await self.send_json({'message': 'login is required!'})
            await self.disconnect(0)
            await self.close()
            return False
        return True

    async def update_user_status(self, is_online: bool = True):
        user = self.user
        user.is_online = is_online
        await user.asave()
