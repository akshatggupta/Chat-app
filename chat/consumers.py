# consumer.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.sessions.models import Session
from asgiref.sync import sync_to_async
from .matchmaker import start_chat, leave_chat

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = None
        self.room_id = None
        
        # accessing the websocket session from scope
        if "session" in self.scope:
            session = self.scope["session"]

            if getattr(session, "session_key", None):
                self.session_id = session.session_key
            else:
                await sync_to_async(session.create)()
                self.session_id = session.session_key

        # once the session is created assign the name of the chat grp
        if self.session_id:
            self.user_group_name = f"user_{self.session_id}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            await self.accept()
            ''' creating the fake request to reuse and handle the function present in matchmaker as they return HTTP request which
                cannot be handled directly by the websocket
            '''
            # Call start_chat from matchmaker.py
            fake_request = type('obj', (object,), {
                'session': type('obj', (object,), {
                    'session_key': self.session_id,
                    'create': lambda: None
                })()
            })()
            
            await sync_to_async(start_chat)(fake_request)
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        if self.session_id:
            fake_request = type('obj', (object,), {
                'session': type('obj', (object,), {
                    'session_key': self.session_id
                })()
            })()
            await sync_to_async(leave_chat)(fake_request)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "")
            
            if hasattr(self, "room_group_name") and self.room_group_name:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "sender": self.session_id  # Track sender
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid message format"
            }))

    async def match_found(self, event):
        """Called when user gets matched with someone"""
        self.room_id = event['room_id']
        self.room_group_name = f"room_{self.room_id}"
        
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify user they're matched
        await self.send(text_data=json.dumps({
            "type": "matched",
            "message": "You're now connected with a stranger!",
            "room_id": self.room_id
        }))
    
    async def partner_left(self, event):
        """Called when partner leaves the chat"""
        # Leave the room group
        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        self.room_id = None
        self.room_group_name = None
        
        await self.send(text_data=json.dumps({
            "type": "partner_left",
            "message": event["message"]
        }))

    async def chat_message(self, event):
        if event.get("sender") != self.session_id:
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                "type": "message",
                "message": event["message"]
            }))
