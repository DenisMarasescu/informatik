import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from accounts.models import Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['user'].username
        self.friend_username = self.scope['url_route']['kwargs']['username']
        self.room_group_name = self.get_room_group_name(self.username, self.friend_username)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_username = data['sender']

        sender = await self.get_user(sender_username)
        receiver = await self.get_user(self.friend_username)

        await self.save_message(sender, receiver, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    @sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)

    @sync_to_async
    def save_message(self, sender, receiver, message):
        return Message.objects.create(sender=sender, receiver=receiver, content=message)

    def get_room_group_name(self, username1, username2):
        return f'chat_{"_".join(sorted([username1, username2]))}'
